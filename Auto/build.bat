pyinstaller --upx-dir=../../upx GAMSAutoRun.spec
xcopy dist\GAMSAutoRun.exe ..\GAMSPlugin\plugins\GAMSAuto\ /Y
copy plugin.xml ..\GAMSPlugin\plugins\GAMSAuto\plugin.xml /Y
pause
