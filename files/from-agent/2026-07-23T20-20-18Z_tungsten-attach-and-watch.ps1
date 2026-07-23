<#
Permanent TUNGSTEN attach + watch script. Single continuous script, not two separate steps --
baselines are captured BEFORE launch so nothing the EA writes between launch and monitor-start
is ever silently swallowed (this was a real, confirmed bug in an earlier two-step version: a
monitor armed a few seconds after launch treated content already on disk as "pre-existing/stale"
and never reported it -- including an init-failure that mattered).

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File tungsten-attach-and-watch.ps1 `
      -ExpertName "TUNGSTEN_9.82_A7.5_QUANT_SLS(68)"

  -WatchOnly   : skip the chart swap + launch, just watch whatever is currently running
                 (use this if the terminal is already attached and you only want the feed).
  -NoLaunch    : swap the chart to ExpertName but do not start terminal.exe (manual launch after).
#>
param(
    [string]$ExpertName = "",
    [string]$Symbol = "USDJPY",
    [int]$Period = 5,
    [switch]$WatchOnly,
    [switch]$NoLaunch,
    # Shared token stamped into this script's own output AND into the standalone
    # watchdog's log filename, so the two logs for one run reconcile on one string.
    [string]$SessionId = ("RUN_" + (Get-Date -Format "yyyyMMdd_HHmm"))
)

# ===== PERMANENT, CONFIRMED PATHS -- do not rediscover these, they don't change =====
$Data          = "C:\Users\User\AppData\Roaming\MetaQuotes\Terminal\98A82F92176B73A2100FCD1F8ABD7255"
$Chart         = "$Data\profiles\default\chart02.chr"          # THE TUNGSTEN test chart (USDJPY M5)
$TerminalExe   = "C:\Program Files (x86)\XM Global MT4\terminal.exe"
$MetaEditorExe = "C:\Program Files (x86)\XM Global MT4\metaeditor.exe"
$ExpertsDir    = "$Data\MQL4\Experts"                            # where terminal ACTUALLY reads compiled EAs from
$LiveLog       = "$Data\MQL4\Files\TUNGSTEN_live.log"            # EA's own file -- OVERWRITTEN each update, not appended
$TodayStr      = Get-Date -Format 'yyyyMMdd'
$TermLog       = "$Data\logs\$TodayStr.log"                      # terminal-level order/system events, appended, cp1252
# Confirmed directly by Manuel 2026-07-17: THIS is where logs appear in realtime --
# the Expert Journal tab / Print()/PrintFormat() output. Appended, cp1252. Primary feed.
$JournalLog    = "$Data\MQL4\Logs\$TodayStr.log"

function Read-Shared([string]$path) {
    if (-not (Test-Path $path)) { return $null }
    try {
        $fs = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        $ms = New-Object System.IO.MemoryStream
        $fs.CopyTo($ms)
        $fs.Close()
        return $ms.ToArray()
    } catch { return $null }
}

function Read-NewTail([string]$path, [long]$prevLen, [int]$encCodePage) {
    if (-not (Test-Path $path)) { return @{ text = $null; len = $prevLen } }
    try {
        $fs = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        $curLen = $fs.Length
        if ($curLen -le $prevLen) {
            $fs.Close()
            if ($curLen -lt $prevLen) { return @{ text = $null; len = 0 } }  # rotated/truncated
            return @{ text = $null; len = $prevLen }
        }
        $fs.Seek($prevLen, [System.IO.SeekOrigin]::Begin) | Out-Null
        $ms = New-Object System.IO.MemoryStream
        $fs.CopyTo($ms)
        $fs.Close()
        $bytes = $ms.ToArray()
        $text = [System.Text.Encoding]::GetEncoding($encCodePage).GetString($bytes)
        return @{ text = $text; len = $curLen }
    } catch { return @{ text = $prevLen } }
}

# ===== STEP 0: ensure the standalone external watchdog is running =====
# Runs OUTSIDE this script's process, so it survives THIS script hanging/crashing/being
# closed too, not just the terminal dying. One watchdog instance is enough across repeated
# attach/relaunch cycles (it already tracks RESTART transitions on its own) -- reuse via a
# PID file instead of spawning a duplicate poller every time this script runs.
$WatchdogScript = "C:\Users\User\Desktop\Work\# EX MACHINA\stoic wealth\tungsten_watchdog.ps1"
$WatchdogLogDir = "C:\Users\User\tungsten-ops\watchdog-logs"
$WatchdogPidFile = Join-Path $WatchdogLogDir ".watchdog.pid.json"
if (-not (Test-Path $WatchdogLogDir)) { New-Item -ItemType Directory -Path $WatchdogLogDir -Force | Out-Null }

# Resolves to whichever SessionId's log is ACTUALLY being written -- this run's freshly
# generated $SessionId if a new watchdog gets spawned, or the reused instance's own
# original SessionId if one is already alive. Every downstream reference to the watchdog's
# log path uses this, never the raw $SessionId, so a reused older instance never gets
# mis-pointed-at a log file that doesn't exist.
$ActiveWatchdogSessionId = $SessionId

$watchdogAlreadyRunning = $false
if (Test-Path $WatchdogPidFile) {
    try {
        $pidInfo = Get-Content $WatchdogPidFile -Raw -ErrorAction Stop | ConvertFrom-Json
        # Verify the PID is not just alive but is ACTUALLY this watchdog script -- a bare
        # Get-Process -Id check would false-positive on a recycled PID belonging to an
        # unrelated process that happened to reuse the same number after a reboot.
        $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$($pidInfo.pid)" -ErrorAction Stop
        if ($cim -and $cim.CommandLine -match [regex]::Escape('tungsten_watchdog.ps1')) {
            $watchdogAlreadyRunning = $true
            $ActiveWatchdogSessionId = $pidInfo.sessionId
        }
    } catch { }  # missing/corrupt/stale pidfile -> fall through to spawning a fresh one
}

if ($watchdogAlreadyRunning) {
    Write-Output "WATCHDOG: already running (pid $($pidInfo.pid), session=$ActiveWatchdogSessionId) -- reusing, not spawning a duplicate. This run's own session is $SessionId; watchdog log stays under the ORIGINAL session it started with."
} elseif (Test-Path $WatchdogScript) {
    # -RedirectStandardInput from a real empty file: second layer of defense against the
    # QuickEdit-Mode console freeze confirmed live 2026-07-23 (the watchdog itself hung for
    # 105+ min, never saw terminal.exe die). The script now disables QuickEdit on its own
    # console at startup, but giving it no interactive input handle at all here removes the
    # mechanism entirely rather than just disabling the one flag that triggers it.
    # (Literal "NUL" is NOT valid here -- Start-Process's Test-Path-based validation rejects
    # the device path; confirmed 2026-07-23, must be a real file on disk.)
    $EmptyStdin = Join-Path $WatchdogLogDir ".empty_stdin"
    if (-not (Test-Path $EmptyStdin)) { New-Item -ItemType File -Path $EmptyStdin -Force | Out-Null }
    $wp = Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$WatchdogScript`"",
        "-SessionId", $SessionId, "-LogDir", "`"$WatchdogLogDir`""
    ) -WindowStyle Hidden -RedirectStandardInput $EmptyStdin -PassThru
    @{ pid = $wp.Id; sessionId = $SessionId } | ConvertTo-Json | Set-Content -Path $WatchdogPidFile
    Write-Output "WATCHDOG: started standalone monitor pid=$($wp.Id), session=$SessionId, log=$WatchdogLogDir\tungsten_watchdog_$SessionId.log"
} else {
    Write-Output "WATCHDOG: WARNING -- $WatchdogScript not found, running WITHOUT the independent death monitor this run"
}

# ===== STEP 1: capture baselines BEFORE touching anything -- this is the race-free part =====
$lastLiveWrite  = if (Test-Path $LiveLog)    { (Get-Item $LiveLog).LastWriteTime } else { [datetime]::MinValue }
$lastTermLen    = if (Test-Path $TermLog)    { (Get-Item $TermLog).Length }       else { 0 }
$lastJournalLen = if (Test-Path $JournalLog) { (Get-Item $JournalLog).Length }    else { 0 }

if (-not $WatchOnly) {
    if ([string]::IsNullOrWhiteSpace($ExpertName)) {
        # Auto-detect: highest SLS(N) build present in the terminal's actual Experts folder.
        $latest = Get-ChildItem $ExpertsDir -Filter "TUNGSTEN_*_SLS(*).ex4" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if (-not $latest) { throw "No TUNGSTEN_*.ex4 found in $ExpertsDir -- copy the compiled build there first." }
        $ExpertName = $latest.BaseName
        Write-Output "AUTO-DETECTED latest build in Experts folder: $ExpertName (by file LastWriteTime)"
    }

    # ===== STEP 2: swap chart02.chr's <expert> block: name= AND window_num= together =====
    # (editing name= alone silently does not take effect -- window_num must also increment)
    #
    # KNOWN FAILURE MODE (confirmed 2026-07-17): when an EA fails OnInit() and MT4 "removes"
    # it, the terminal's NEXT profile save strips the <expert>...</expert> block from the
    # chart file entirely (chart02.chr went from 228181 to 228090 lines, zero occurrences of
    # "expert" anywhere). A plain name=/window_num= edit then has nothing to edit. Recover
    # automatically: fall back to the newest chart02.chr.bak_* that still has an <expert>
    # block, restore its full structure, then proceed with the normal swap on top of it.
    $lines = Get-Content -Path $Chart -Encoding UTF8
    $expertLineNum = ($lines | Select-String -Pattern '^<expert>' | Select-Object -First 1).LineNumber
    if (-not $expertLineNum) {
        Write-Output "RECOVERY: <expert> block missing from $Chart (EA was removed after a prior failed init) -- restoring structure from newest backup that has one"
        $candidates = Get-ChildItem "$Chart.bak_*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
        $restored = $false
        foreach ($cand in $candidates) {
            $candLines = Get-Content -Path $cand.FullName -Encoding UTF8
            if ($candLines | Select-String -Pattern '^<expert>' -Quiet) {
                Copy-Item $Chart "$Chart.bak_stripped_$(Get-Date -Format yyyyMMddHHmmss)"  # preserve the stripped state too
                Copy-Item $cand.FullName $Chart
                Write-Output "RECOVERY: restored structure from $($cand.Name)"
                $lines = Get-Content -Path $Chart -Encoding UTF8
                $expertLineNum = ($lines | Select-String -Pattern '^<expert>' | Select-Object -First 1).LineNumber
                $restored = $true
                break
            }
        }
        if (-not $restored) { throw "No <expert> block found in $Chart and no backup with one exists -- needs a manual GUI reattach once to re-seed a backup." }
    }
    $nameIdx  = $expertLineNum      # 0-based index of the name= line (line AFTER <expert>, 1-based expertLineNum == 0-based name line)
    $flagsIdx = $expertLineNum + 1
    $winIdx   = $expertLineNum + 2
    $curWin = 0
    if ($lines[$winIdx] -match 'window_num=(\d+)') { $curWin = [int]$Matches[1] }
    $backupPath = "$Chart.bak_$(Get-Date -Format yyyyMMddHHmmss)"
    Copy-Item $Chart $backupPath
    $lines[$nameIdx] = "name=$ExpertName"
    $lines[$winIdx]  = "window_num=$($curWin + 1)"
    Set-Content -Path $Chart -Value $lines -Encoding UTF8
    Write-Output "CHART SWAPPED: $ExpertName, window_num $curWin -> $($curWin+1) (backup: $backupPath)"

    if (-not $NoLaunch) {
        Start-Process -FilePath $TerminalExe
        Write-Output "LAUNCHED terminal.exe -- watching from pre-launch baseline (nothing written by this run can be missed)"
        Start-Sleep -Seconds 3
    }
}

# ===== STEP 3: continuous watch, baselined from STEP 1 (before any launch) =====
$tick = 0
$initFailPattern = 'NOT READY|initialization failed|autotrading enabled.*FAIL|FAIL\s*\[01\]'
Write-Output "WATCH ACTIVE $(Get-Date -Format 'HH:mm:ss') session=$SessionId -- baselines: live-write=$lastLiveWrite term=$lastTermLen journal=$lastJournalLen"

while ($true) {
    $proc = Get-Process -Name terminal -ErrorAction SilentlyContinue
    if (-not $proc) {
        Write-Output "ALERT $(Get-Date -Format 'HH:mm:ss'): terminal.exe is GONE -- crash or hang"
        $ev = Get-WinEvent -FilterHashtable @{LogName='Application'; Id=1000,1002} -MaxEvents 3 -ErrorAction SilentlyContinue
        if ($ev) { $ev | ForEach-Object { Write-Output "  EVENT $($_.TimeCreated) Id=$($_.Id): $($_.Message.Split("`n")[0])" } }
        Write-Output "  See $WatchdogLogDir\tungsten_watchdog_$ActiveWatchdogSessionId.log for the tighter-bracketed (3s poll) time-of-death, System-log context, and DEINIT cross-check -- that log is independent of this script and was already recording before this loop started."
        break
    }

    if (Test-Path $LiveLog) {
        $curWrite = (Get-Item $LiveLog).LastWriteTime
        if ($curWrite -gt $lastLiveWrite) {
            $liveBytes = Read-Shared $LiveLog
            if ($liveBytes) {
                $cur = [System.Text.Encoding]::UTF8.GetString($liveBytes).Trim()
                Write-Output "LIVE $(Get-Date -Format 'HH:mm:ss') (written $curWrite): $cur"
            }
            $lastLiveWrite = $curWrite
        }
    }

    $termResult = Read-NewTail $TermLog $lastTermLen 1252
    if ($termResult.text) {
        $termResult.text -split "`r`n" | Where-Object { $_.Trim() -ne "" } | ForEach-Object { Write-Output "TERM: $_" }
    }
    $lastTermLen = $termResult.len

    $journalResult = Read-NewTail $JournalLog $lastJournalLen 1252
    if ($journalResult.text) {
        $journalResult.text -split "`r`n" | Where-Object { $_.Trim() -ne "" } | ForEach-Object {
            if ($_ -match $initFailPattern) {
                Write-Output "!!! INIT-FAIL SIGNAL: $_"
            } else {
                Write-Output "JOURNAL: $_"
            }
        }
    }
    $lastJournalLen = $journalResult.len

    $tick++
    if ($tick % 12 -eq 0) {
        $cpu = [math]::Round($proc.CPU, 1)
        Write-Output "HEARTBEAT $(Get-Date -Format 'HH:mm:ss'): terminal.exe alive (PID $($proc.Id), CPU ${cpu}s total)"
    }
    Start-Sleep -Seconds 5
}
