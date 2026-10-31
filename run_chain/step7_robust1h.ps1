# PROVISIONAL step 7: 1 h robust multi-year design + hourly check. Cancel: stop the watcher running logs\step7_after_chain2.ps1
$cv = "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1"; $py = "C:\Users\Edgar\anaconda3\anaconda3.12\envs\gbtea\python.exe"; $log = "$cv\logs\chain.log"
Add-Content $log "[step7_robust1h] start $(Get-Date)"
$a = '-u -W ignore run_flagship.py --drive-root "G:/My Drive" --experiments robust --modes islanded --agg-hours 1 --zones Z10 Z11 Z8 Z3 Z7 Z1_2 Z6 Z5 Z4 Z1_1 Z15 Z14 Z12 Z13 Z9 Z1_3 Z1_4 Z2 Z16 Z17 --tag 1h'
$p = Start-Process $py -ArgumentList $a -WorkingDirectory $cv -WindowStyle Hidden -PassThru -RedirectStandardOutput "$cv\logs\robust_1h.log" -RedirectStandardError "$cv\logs\robust_1h.err"
$peak = 0
while (-not $p.HasExited) {
    try { $w = (Get-Process -Id $p.Id).WorkingSet64 / 1GB; if ($w -gt $peak) { $peak = $w } } catch {}
    if ($peak -gt 12) { Stop-Process -Id $p.Id -Force; Add-Content $log "[step7_robust1h] STOPPED: RAM $([math]::Round($peak,1)) GB > 12 GB $(Get-Date)"; exit 1 }
    Start-Sleep 20
}
Add-Content $log "[step7_robust1h] design exit $($p.ExitCode), peak RAM $([math]::Round($peak,1)) GB $(Get-Date)"
$b = '-u -W ignore run_stress.py --drive-root "G:/My Drive" --mode islanded --from-designs robust_1h.csv --zones Z10 Z11 Z8 Z3 Z7 Z1_2 Z6 Z5 Z4 Z1_1 Z15 Z14 Z12 Z13 Z9 Z1_3 Z1_4 Z2 Z16 Z17 --tag robust1h'
$q = Start-Process $py -ArgumentList $b -WorkingDirectory $cv -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput "$cv\logs\stress_robust1h.log" -RedirectStandardError "$cv\logs\stress_robust1h.err"
Add-Content $log "[step7_robust1h] hourly check exit $($q.ExitCode) $(Get-Date)"
