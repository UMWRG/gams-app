pyinstaller -y --upx-dir=../../upx GAMSExport.spec
xcopy dist\GAMSExport\* ..\GAMSPlugin\plugins\GAMSExport\ /Y /s
copy plugin.xml ..\GAMSPlugin\plugins\GAMSExport\plugin.xml /Y
pause
