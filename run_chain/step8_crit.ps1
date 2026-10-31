# Step 8 (provisional): critical-years robust design, 1 h steps, islanded, then hourly check on all 25 years.
# N years per zone from flagship\crit_years_<N>.csv (pick_critical_years.py). N=5, dropped to 4 if Z10 takes > 4 h
# (the choice is kept in logs\crit_n.txt so a resume uses the same N). RAM guard 12 GB.
$cv = "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1"; $py = "C:\Users\Edgar\anaconda3\anaconda3.12\envs\gbtea\python.exe"; $fd = "G:\My Drive\Energy_System_Modelling_GB\esm_GB_2025\corrected_v1\flagship"; $log = "$cv\logs\chain.log"
function L($m) { Add-Content $log "[step8_crit] $m $(Get-Date)" }
$nf = "$cv\logs\crit_n.txt"; $N = if (Test-Path $nf) { [int](Get-Content $nf) } else { 5 }
while ($true) {
    $tag = "crit$N"; $out = "$fd\robust_$tag.csv"
    L "design start N=$N"
    $a = "-u -W ignore run_flagship.py --drive-root `"G:/My Drive`" --experiments robust --modes islanded --agg-hours 1 --years-file `"$fd\crit_years_$N.csv`" --zones Z10 Z11 Z8 Z3 Z7 Z1_2 Z6 Z5 Z4 Z1_1 Z15 Z14 Z12 Z13 Z9 Z1_3 Z1_4 Z2 Z16 Z17 --tag $tag"
    $p = Start-Process $py -ArgumentList $a -WorkingDirectory $cv -WindowStyle Hidden -PassThru -RedirectStandardOutput "$cv\logs\robust_$tag.log" -RedirectStandardError "$cv\logs\robust_$tag.err"
    $t0 = Get-Date; $peak = 0; $restart = $false
    while (-not $p.HasExited) {
        try { $w = (Get-Process -Id $p.Id).WorkingSet64 / 1GB; if ($w -gt $peak) { $peak = $w } } catch {}
        if ($peak -gt 12) { Stop-Process -Id $p.Id -Force; L "STOPPED: RAM $([math]::Round($peak,1)) GB > 12 GB"; exit 1 }
        $z10 = (Test-Path $out) -and (Select-String $out -Pattern '^([^,]*,){24}Z10,' -Quiet)
        if ($N -eq 5 -and -not $z10 -and ((Get-Date) - $t0).TotalHours -gt 4) {
            Stop-Process -Id $p.Id -Force; L "Z10 over 4 h at N=5; switching to N=4"; Set-Content $nf 4; $N = 4; $restart = $true; break
        }
        Start-Sleep 30
    }
    if ($restart) { continue }
    L "design exit $($p.ExitCode), peak RAM $([math]::Round($peak,1)) GB"
    break
}
$b = "-u -W ignore run_stress.py --drive-root `"G:/My Drive`" --mode islanded --from-designs robust_$tag.csv --zones Z10 Z11 Z8 Z3 Z7 Z1_2 Z6 Z5 Z4 Z1_1 Z15 Z14 Z12 Z13 Z9 Z1_3 Z1_4 Z2 Z16 Z17 --tag $tag"
$q = Start-Process $py -ArgumentList $b -WorkingDirectory $cv -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput "$cv\logs\stress_$tag.log" -RedirectStandardError "$cv\logs\stress_$tag.err"
L "hourly check exit $($q.ExitCode)"

