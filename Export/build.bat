pyinstaller -y --upx-dir=../../upx GAMSExport.spec
xcopy dist\GAMSExport\* ..\GAMSPlugin\plugins\GAMSExport\ /Y /E
copy plugin.xml ..\GAMSPlugin\plugins\GAMSExport\plugin.xml /Y
copy *.png ..\GAMSPlugin\plugins\GAMSExport\plugin.xml /Y
png
pause
