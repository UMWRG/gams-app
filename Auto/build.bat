pyinstaller --upx-dir=../../upx GAMSAutoRun.spec
xcopy dist\GAMSAutoRun\* ..\GAMSPlugin\plugins\GAMSAuto\ /Y /s
copy plugin.xml ..\GAMSPlugin\plugins\GAMSAuto\plugin.xml /Y
pause
