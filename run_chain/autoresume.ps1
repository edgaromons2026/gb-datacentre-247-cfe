# GBTEA auto-resume: run at logon by the scheduled task "GBTEA auto-resume" (current user only).
# Remove with:  schtasks /Delete /TN "GBTEA auto-resume" /F
$cv = "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1"; $log = "$cv\logs\autoresume.log"; $chain = "$cv\logs\chain.log"
function L($m) { Add-Content $log "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $m" }
L "triggered"
if (Test-Path "$cv\logs\PAUSE") { L "logs\PAUSE present; not resuming"; exit 0 }
if (Test-Path "$cv\logs\CHAIN_DONE") { L "chain already finished (logs\CHAIN_DONE); nothing to do"; exit 0 }
$busy = Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'python.exe' -and $_.CommandLine -match 'run_flagship|run_stress') -or ($_.CommandLine -match 'current_chain\.ps1|chain3\.ps1|step7_robust1h\.ps1|step8_crit\.ps1|sens_queue\.ps1|sens_after_step8\.ps1') }
if ($busy) { L "chain already running (PIDs $(($busy.ProcessId) -join ', ')); nothing to do"; exit 0 }
if (-not (Get-Process GoogleDriveFS -ErrorAction SilentlyContinue)) {
    $g = Get-ChildItem "C:\Program Files\Google\Drive File Stream" -Recurse -Filter GoogleDriveFS.exe -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
    if ($g) { Start-Process $g.FullName; L "started Google Drive ($($g.FullName))" } else { L "Google Drive executable not found" }
}
$t0 = Get-Date
while (-not (Test-Path "G:\My Drive\Energy_System_Modelling_GB") -and ((Get-Date) - $t0).TotalMinutes -lt 15) { Start-Sleep 10 }
if (-not (Test-Path "G:\My Drive\Energy_System_Modelling_GB")) { L "G:\My Drive not reachable after 15 min; NOT resuming"; exit 1 }
L "G: reachable; resuming current_chain"
Add-Content $chain "[auto-resume] resuming current_chain $(Get-Date)"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$cv\logs\current_chain.ps1"
L "current_chain returned"



