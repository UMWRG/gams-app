pyinstaller --upx-dir=../../upx GAMSExport.spec
xcopy dist\GAMSExport.exe ..\GAMSPlugin\plugins\GAMSExport\ /Y
copy plugin.xml ..\GAMSPlugin\plugins\GAMSExport\plugin.xml /Y
pause
