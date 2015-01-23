cd Export
pyinstaller -y --upx-dir=../../upx GAMSExport.spec
xcopy dist\GAMSExport\* ..\GAMSPlugin\plugins\GAMSExport\ /Y /E
copy plugin.xml ..\GAMSPlugin\plugins\GAMSExport\plugin.xml /Y
cd ..\\Import
pyinstaller -y --upx-dir=../../upx GAMSImport.spec
xcopy dist\GAMSImport\* ..\GAMSPlugin\plugins\GAMSImport\ /Y /E
copy plugin.xml ..\GAMSPlugin\plugins\GAMSImport\plugin.xml /Y
cd ..\\Auto
pyinstaller -y --upx-dir=../../upx GAMSAutoRun.spec
xcopy dist\GAMSAutoRun\* ..\GAMSPlugin\plugins\GAMSAuto\ /Y /E
copy plugin.xml ..\GAMSPlugin\plugins\GAMSAuto\plugin.xml /Y
pause