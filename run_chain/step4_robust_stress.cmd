@echo off
cd /d "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1"
"C:\Users\Edgar\anaconda3\anaconda3.12\envs\gbtea\python.exe" -u -W ignore run_stress.py --drive-root "G:/My Drive" --mode islanded --from-designs robust_main.csv --tag main > logs\stress_robust.log 2>&1
