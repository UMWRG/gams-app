pyinstaller -y --upx-dir=../../upx GAMSAutoRun.spec
xcopy dist\GAMSAutoRun\* ..\GAMSPlugin\plugins\GAMSAuto\ /Y /E
copy plugin.xml ..\GAMSPlugin\plugins\GAMSAuto\plugin.xml /Y
copy *.png ..\GAMSPlugin\plugins\GAMSAuto\plugin.xml /Y
pause
