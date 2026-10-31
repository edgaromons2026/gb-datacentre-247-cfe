# Current chain for auto-resume: step 8 (critical-years robust), then the Z10 input-sensitivity queue. Each part skips finished work.
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1\logs\step8_crit.ps1"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1\sens\sens_queue.ps1"
Set-Content "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1\logs\CHAIN_DONE" "step 8 + sensitivity queue finished $(Get-Date)"
