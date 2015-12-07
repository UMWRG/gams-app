cd Export
pyinstaller -y --upx-dir=../../upx GAMSExport.spec
xcopy dist\GAMSExport\* ..\GAMSPlugin_Demo\plugins\GAMS_files\ /Y /E
copy plugin.xml ..\GAMSPlugin_Demo\plugins\GAMSExport\plugin.xml /Y
copy *.png ..\GAMSPlugin_Demo\plugins\GAMSExport\*.png /Y
copy G*.bat ..\GAMSPlugin_Demo\plugins\GAMSExport\G*.bat /Y
cd ..\\Import
pyinstaller -y --upx-dir=../../upx GAMSImport.spec
xcopy dist\GAMSImport\* ..\GAMSPlugin_Demo\plugins\GAMS_files\ /Y /E
copy plugin.xml ..\GAMSPlugin_Demo\plugins\GAMSImport\plugin.xml /Y
copy *.png ..\GAMSPlugin_Demo\plugins\GAMSImport\*.png /Y
copy G*.bat ..\GAMSPlugin_Demo\plugins\GAMSImport\G*.bat /Y

cd ..\\Auto
pyinstaller -y --upx-dir=../../upx GAMSAutoRun.spec
xcopy dist\GAMSAutoRun\* ..\GAMSPlugin_Demo\plugins\GAMS_files\ /Y /E
copy plugin.xml ..\GAMSPlugin_Demo\plugins\GAMSAuto\plugin.xml /Y
copy *.png ..\GAMSPlugin_Demo\plugins\GAMSAuto\*.png /Y
copy G*.bat ..\GAMSPlugin_Demo\plugins\GAMSAuto\G*.bat /Y

pause