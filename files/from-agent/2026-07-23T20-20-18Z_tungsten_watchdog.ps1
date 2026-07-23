<#
  ═══════════════════════════════════════════════════════════════════════
  TUNGSTEN WATCHDOG  ·  tungsten_watchdog.ps1
  ═══════════════════════════════════════════════════════════════════════
  External process monitor for the MT4 terminal. Runs OUTSIDE the
  terminal, so it survives the terminal's death and records the exact
  second it happened — the one fact the 18 July closes never left behind.

  Writes ONLY on state change. A quiet session produces a handful of
  lines, not spam.

  USAGE (PowerShell):
      .\tungsten_watchdog.ps1
      .\tungsten_watchdog.ps1 -SessionId RUN_20260723_0900
      .\tungsten_watchdog.ps1 -ProcessName terminal -PollSeconds 3

  Stop with Ctrl+C — it logs its own shutdown so an absent stop line
  means the watchdog itself was killed.
  ═══════════════════════════════════════════════════════════════════════
#>

param(
    # Session token — stamp the SAME id into the EA's log header so all
    # files for one run reconcile on one string.
    [string]$SessionId   = ("RUN_" + (Get-Date -Format "yyyyMMdd_HHmm")),

    # MT4 process name without .exe ("terminal" for MT4, "terminal64" MT5)
    [string]$ProcessName = "terminal",

    # Seconds between existence checks. 3s brackets time-of-death tightly
    # at negligible cost. This is the CHECK interval, not a log interval —
    # nothing is written unless something changes.
    [int]$PollSeconds    = 3,

    # Log directory. Default: alongside this script.
    [string]$LogDir      = $PSScriptRoot
)

# ── disable console QuickEdit Mode ────────────────────────────────────────
# CONFIRMED ROOT CAUSE, first live run 2026-07-23: this watchdog (launched hidden via
# Start-Process) silently froze ~1 min after starting and never logged the terminal's actual
# death 105 minutes later -- confirmed via thread inspection (blocked, near-zero CPU growth,
# zero log growth) even after terminal.exe had genuinely exited. QuickEdit Mode is a Windows
# console default: any mark/select interaction on a console's input buffer -- even a HIDDEN
# one, which still owns a real console handle -- suspends ALL console I/O until dismissed,
# which blocks this script's every Get-Process/Start-Sleep cycle forever with no error, no
# exception, nothing to catch. Clearing ENABLE_QUICK_EDIT_MODE on stdin is the standard fix.
# Best-effort: if this ever fails (e.g. no console at all), there is nothing to disable anyway.
try {
    Add-Type -Name Console -Namespace Native -MemberDefinition @'
[DllImport("kernel32.dll")] public static extern IntPtr GetStdHandle(int nStdHandle);
[DllImport("kernel32.dll")] public static extern bool GetConsoleMode(IntPtr hConsoleHandle, out uint lpMode);
[DllImport("kernel32.dll")] public static extern bool SetConsoleMode(IntPtr hConsoleHandle, uint dwMode);
'@ -ErrorAction Stop
    $STD_INPUT_HANDLE = -10
    $ENABLE_QUICK_EDIT_MODE = 0x0040
    $ENABLE_EXTENDED_FLAGS = 0x0080
    $h = [Native.Console]::GetStdHandle($STD_INPUT_HANDLE)
    [uint32]$mode = 0
    if ([Native.Console]::GetConsoleMode($h, [ref]$mode)) {
        $newMode = ($mode -band (-bnot $ENABLE_QUICK_EDIT_MODE)) -bor $ENABLE_EXTENDED_FLAGS
        [Native.Console]::SetConsoleMode($h, $newMode) | Out-Null
    }
} catch { }

# ── log file: timestamped, never overwritten ─────────────────────────────
if (-not $LogDir) { $LogDir = "." }
$LogFile = Join-Path $LogDir ("tungsten_watchdog_{0}.log" -f $SessionId)

function Write-Log([string]$Tag, [string]$Msg) {
    # One clock for everything: local machine time, millisecond precision.
    $ts   = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $line = "{0} [{1}] {2}" -f $ts, $Tag, $Msg
    # Append + implicit flush per write; nothing buffered to lose.
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
    Write-Host $line
}

# ── header block: the sync contract with the EA log ─────────────────────
$tz     = [System.TimeZoneInfo]::Local
$offset = $tz.GetUtcOffset([datetime]::Now)
Write-Log "HEADER" ("session={0}" -f $SessionId)
Write-Log "HEADER" ("watching={0}.exe  poll={1}s  pid_of_watchdog={2}" -f $ProcessName, $PollSeconds, $PID)
Write-Log "HEADER" ("localtime_utc_offset={0}  timezone={1}" -f $offset, $tz.Id)
Write-Log "HEADER" ("machine={0}  logfile={1}" -f $env:COMPUTERNAME, $LogFile)

# ── state machine: log transitions only ─────────────────────────────────
#    States: WAITING (no process) → ALIVE (running) → DIED / WAITING
$state    = "INIT"
$procId   = $null
$procStart= $null
$lastSeen = $null

while ($true) {
    $p = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue |
         Sort-Object StartTime | Select-Object -First 1

    if ($p) {
        $lastSeen = Get-Date
        if ($state -ne "ALIVE" -or $procId -ne $p.Id) {
            # process appeared, or a NEW instance replaced the old one
            if ($state -eq "ALIVE" -and $procId -ne $p.Id) {
                Write-Log "RESTART" ("new instance pid={0} replaced pid={1}" -f $p.Id, $procId)
            } else {
                Write-Log "ALIVE" ("{0}.exe running  pid={1}  started={2}" -f `
                    $ProcessName, $p.Id, $p.StartTime.ToString("yyyy-MM-dd HH:mm:ss"))
            }
            $state     = "ALIVE"
            $procId    = $p.Id
            $procStart = $p.StartTime
        }
        # memory watermark: logged only when it crosses a new 256MB step,
        # so a leak shows up without a line per poll
        $mb = [math]::Round($p.WorkingSet64 / 1MB)
        $step = [math]::Floor($mb / 256)
        if ($null -eq $script:memStep) { $script:memStep = $step }
        elseif ($step -gt $script:memStep) {
            $script:memStep = $step
            Write-Log "MEMORY" ("working set crossed {0} MB (now {1} MB)" -f ($step*256), $mb)
        }
    }
    else {
        if ($state -eq "ALIVE") {
            # ── THE LINE THIS ENTIRE SCRIPT EXISTS FOR ──────────────────
            $up = if ($procStart) { ((Get-Date) - $procStart).ToString("hh\:mm\:ss") } else { "?" }
            Write-Log "DIED" ("{0}.exe pid={1} GONE. uptime_was={2}  last_seen={3}" -f `
                $ProcessName, $procId, $up, $lastSeen.ToString("HH:mm:ss.fff"))
            Write-Log "DIED" ("time_of_death bracketed to <= {0}s. Check EA log for [DEINIT] at/before this stamp — absent [DEINIT] = unclean termination." -f $PollSeconds)
            # one-shot context capture: what else was happening on the box
            try {
                $recent = Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=(Get-Date).AddMinutes(-3)} `
                          -MaxEvents 12 -ErrorAction Stop |
                          ForEach-Object { "{0} id={1} {2}" -f $_.TimeCreated.ToString("HH:mm:ss"), $_.Id, ($_.ProviderName) }
                Write-Log "CONTEXT" ("last 3min System events: " + ($recent -join " | "))
            } catch {
                Write-Log "CONTEXT" "System event query unavailable (known unreliable on this box — see 22 Jul forensics)"
            }
            $state = "WAITING"; $procId = $null; $script:memStep = $null
        }
        elseif ($state -eq "INIT") {
            Write-Log "WAITING" ("{0}.exe not running yet — watching for it" -f $ProcessName)
            $state = "WAITING"
        }
    }

    Start-Sleep -Seconds $PollSeconds
}

# Ctrl+C lands here via finally-like behaviour in console host:
# (PowerShell doesn't guarantee this block; the trap below covers it)
trap {
    Write-Log "STOP" "watchdog terminated (Ctrl+C or error). If this line is absent in a future log, the watchdog itself was killed."
    break
}
