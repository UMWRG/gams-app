cd Export
pyinstaller -y --upx-dir=../../upx GAMSExport.spec
xcopy dist\GAMSExport\* ..\GAMSPlugin_64\plugins\GAMSExport\ /Y /E
copy plugin.xml ..\GAMSPlugin_64\plugins\GAMSExport\plugin.xml /Y
copy *.png ..\GAMSPlugin_64\plugins\GAMSExport\*.png /Y
cd ..\\Import
pyinstaller -y --upx-dir=../../upx GAMSImport.spec
xcopy dist\GAMSImport\* ..\GAMSPlugin_64\plugins\GAMSExport\\plugins\GAMSImport\ /Y /E
copy plugin.xml ..\GAMSPlugin_64\plugins\GAMSImport\plugin.xml /Y
copy *.png ..\GAMSPlugin_64\plugins\GAMSImport\*.png /Y
cd ..\\Auto
pyinstaller -y --upx-dir=../../upx GAMSAutoRun.spec
xcopy dist\GAMSAutoRun\* ..\GAMSPlugin_64\plugins\GAMSAuto\ /Y /E
copy plugin.xml ..\GAMSPlugin\plugins\GAMSAuto\plugin.xml /Y
copy *.png ..\GAMSPlugin\plugins\GAMSAuto\plugin.xml /Y
pause