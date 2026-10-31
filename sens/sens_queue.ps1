# Z10 input sensitivities (user request 28 Oct 2026). Waits for the current chain (adder70, then step 7) to finish,
# then runs each case: design (islanded 2000-2024 + grid 2015-2024 at 90/95/99/100%) and the islanded cross-year stress test.
# Every run is resumable (solved rows are skipped), so this script can simply be started again after a crash or reboot.
# Progress: logs\sens_chain.log. Cancel: stop the powershell process running this script.
$cv = "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1"; $py = "C:\Users\Edgar\anaconda3\anaconda3.12\envs\gbtea\python.exe"
$chain = "$cv\logs\chain.log"; $log = "$cv\logs\sens_chain.log"; $dr = '--drive-root "G:/My Drive"'
$out = "G:\My Drive\Energy_System_Modelling_GB\esm_GB_2025\corrected_v1"
$bias = "$cv\sens\era5_bias_factors_monthly.csv"
function Say($m) { Add-Content $log "$m $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" }
function Run($name, $argline) {
    Say "[$name] start"
    $p = Start-Process $py -ArgumentList "-u -W ignore $argline" -WorkingDirectory $cv -WindowStyle Hidden -PassThru -Wait `
         -RedirectStandardOutput "$cv\logs\sens_$name.log" -RedirectStandardError "$cv\logs\sens_$name.err"
    Say "[$name] exit $($p.ExitCode)"
}
# (30 Oct) No longer waits for step 7 (abandoned); logs\current_chain.ps1 runs this after step 8.
Say "SENS QUEUE start"
$z = "--zones Z10"
$cases = @(
  @("noh2",     "run_flagship.py $dr $z --no-h2 --tag noh2",                                    "run_stress.py $dr --mode islanded $z --from-designs design_noh2.csv --tag noh2"),
  @("wl080",    "run_flagship.py $dr $z --wind-loss 0.80 --tag wl080",                          "run_stress.py $dr --mode islanded $z --from-designs design_wl080.csv --tag wl080"),
  @("wl090",    "run_flagship.py $dr $z --wind-loss 0.90 --tag wl090",                          "run_stress.py $dr --mode islanded $z --from-designs design_wl090.csv --tag wl090"),
  @("cy2030",   "run_flagship.py $dr $z --cost-year 2030 --tag cy2030",                         "run_stress.py $dr --mode islanded $z --cost-year 2030 --from-designs design_cy2030.csv --tag cy2030"),
  @("cy2050",   "run_flagship.py $dr $z --cost-year 2050 --tag cy2050",                         "run_stress.py $dr --mode islanded $z --cost-year 2050 --from-designs design_cy2050.csv --tag cy2050"),
  @("r03",      "sens\run_sens.py flagship --rate 0.03 -- $dr $z --tag r03",                    "sens\run_sens.py stress --rate 0.03 -- $dr --mode islanded $z --from-designs design_r03.csv --tag r03"),
  @("r05",      "sens\run_sens.py flagship --rate 0.05 -- $dr $z --tag r05",                    "sens\run_sens.py stress --rate 0.05 -- $dr --mode islanded $z --from-designs design_r05.csv --tag r05"),
  @("r10",      "sens\run_sens.py flagship --rate 0.10 -- $dr $z --tag r10",                    "sens\run_sens.py stress --rate 0.10 -- $dr --mode islanded $z --from-designs design_r10.csv --tag r10"),
  @("era5bias", "sens\run_sens.py flagship --cf-bias `"$bias`" -- $dr $z --tag era5bias",      "sens\run_sens.py stress --cf-bias `"$bias`" -- $dr --mode islanded $z --from-designs design_era5bias.csv --tag era5bias")
)
foreach ($c in $cases) { Run "$($c[0])_design" $c[1]; Run "$($c[0])_stress" $c[2] }
# grid carbon: build hourly g from NESO, then grid designs only (g counts the carbon-free part of imports)
Run "neso_g" "sens\make_neso_g.py $dr"
if (Test-Path "$out\sens\neso_g_hourly_2009_2025.csv") {
    Run "neso_design" "run_flagship.py $dr $z --modes grid --grid-cfe `"$out\sens\neso_g_hourly_2009_2025.csv`" --tag neso"
} else { Say "[neso] skipped: no g file (see logs\sens_neso_g.err)" }
Say "SENS QUEUE done"
