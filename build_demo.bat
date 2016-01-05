cd Export
pyinstaller -y --upx-dir=../../upx GAMSExport.spec
xcopy dist\GAMSExport\* ..\release\GAMSApp_Demo\plugins\GAMS_files\ /Y /E
copy plugin.xml ..\release\GAMSApp_Demo\plugins\GAMSExport\plugin.xml /Y
copy *.png ..\release\GAMSApp_Demo\plugins\GAMSExport\*.png /Y
copy G*.bat ..\release\GAMSApp_Demo\plugins\GAMSExport\G*.bat /Y
cd ..\\Import
pyinstaller -y --upx-dir=../../upx GAMSImport.spec
xcopy dist\GAMSImport\* ..\release\GAMSApp_Demo\plugins\GAMS_files\ /Y /E
copy plugin.xml ..\release\GAMSApp_Demo\plugins\GAMSImport\plugin.xml /Y
copy *.png ..\release\GAMSApp_Demo\plugins\GAMSImport\*.png /Y
copy G*.bat ..\release\GAMSApp_Demo\plugins\GAMSImport\G*.bat /Y

cd ..\\Auto
pyinstaller -y --upx-dir=../../upx GAMSAutoRun.spec
xcopy dist\GAMSAutoRun\* ..\release\GAMSApp_Demo\plugins\GAMS_files\ /Y /E
copy plugin.xml ..\release\GAMSApp_Demo\plugins\GAMSAuto\plugin.xml /Y
copy *.png ..\release\GAMSApp_Demo\plugins\GAMSAuto\*.png /Y
copy G*.bat ..\release\GAMSApp_Demo\plugins\GAMSAuto\G*.bat /Y

pause
