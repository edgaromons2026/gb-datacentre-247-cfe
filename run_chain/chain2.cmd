@echo off
cd /d "D:\Research\GB_DataCentre_Microgrid_TEA\03_Models\corrected_v1"
echo CHAIN2 START %DATE% %TIME% >> logs\chain.log
echo [step2_grid_stress.cmd] start %DATE% %TIME% >> logs\chain.log
call logs\step2_grid_stress.cmd
echo [step2_grid_stress.cmd] exit %ERRORLEVEL% %DATE% %TIME% >> logs\chain.log
echo [step3_robust_design.cmd] start %DATE% %TIME% >> logs\chain.log
call logs\step3_robust_design.cmd
echo [step3_robust_design.cmd] exit %ERRORLEVEL% %DATE% %TIME% >> logs\chain.log
echo [step4_robust_stress.cmd] start %DATE% %TIME% >> logs\chain.log
call logs\step4_robust_stress.cmd
echo [step4_robust_stress.cmd] exit %ERRORLEVEL% %DATE% %TIME% >> logs\chain.log
echo [step5_adder30.cmd] start %DATE% %TIME% >> logs\chain.log
call logs\step5_adder30.cmd
echo [step5_adder30.cmd] exit %ERRORLEVEL% %DATE% %TIME% >> logs\chain.log
echo [step6_adder70.cmd] start %DATE% %TIME% >> logs\chain.log
call logs\step6_adder70.cmd
echo [step6_adder70.cmd] exit %ERRORLEVEL% %DATE% %TIME% >> logs\chain.log
echo CHAIN2 END %DATE% %TIME% >> logs\chain.log

