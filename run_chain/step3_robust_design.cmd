@echo off
cd /d "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1"
"C:\Users\Edgar\anaconda3\anaconda3.12\envs\gbtea\python.exe" -u -W ignore run_flagship.py --drive-root "G:/My Drive" --experiments robust --modes islanded --agg-hours 3 --tag main > logs\robust_main.log 2>&1
