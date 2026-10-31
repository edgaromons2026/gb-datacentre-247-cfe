@echo off
cd /d "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1"
"C:\Users\Edgar\anaconda3\anaconda3.12\envs\gbtea\python.exe" -u -W ignore run_flagship.py --drive-root "G:/My Drive" --experiments design --modes grid --wind-loss 0.86 --grid-adder 70 --tag adder70 > logs\flagship_adder70.log 2>&1
