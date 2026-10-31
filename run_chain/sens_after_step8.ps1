# Live hand-off (30 Oct): the running current_chain (PID 13912) predates the sens step, so run it when that exits.
Wait-Process -Id 13912 -ErrorAction SilentlyContinue
Remove-Item "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1\logs\CHAIN_DONE" -ErrorAction SilentlyContinue
Add-Content "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1\logs\chain.log" "[sens] queue start after step 8 $(Get-Date)"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1\sens\sens_queue.ps1"
Set-Content "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1\logs\CHAIN_DONE" "step 8 + sensitivity queue finished $(Get-Date)"
