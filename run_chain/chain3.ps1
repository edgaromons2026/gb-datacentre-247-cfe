Add-Content "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1\logs\chain.log" "[restart after 29 Oct 05:24 crash] $(Get-Date)"
& cmd.exe /c "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1\logs\step6_adder70.cmd"
Add-Content "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1\logs\chain.log" "[step6_adder70] exit $LASTEXITCODE $(Get-Date)"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1\logs\step7_robust1h.ps1"
