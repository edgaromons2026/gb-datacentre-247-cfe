@echo off
cd /d "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1"
"C:\Users\Edgar\anaconda3\anaconda3.12\envs\gbtea\python.exe" -u -W ignore run_flagship.py --drive-root "G:/My Drive" --experiments design --modes grid --wind-loss 0.86 --grid-adder 30 --tag adder30 > logs\flagship_adder30.log 2>&1
