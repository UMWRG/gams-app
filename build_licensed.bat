cd Export
pyinstaller -y --upx-dir=../../upx GAMSExport.spec
xcopy dist\GAMSExport\* ..\release\GAMSApp_Licensed\plugins\GAMS_files\ /Y /E
copy plugin.xml ..\release\GAMSApp_Licensed\plugins\GAMSExport\plugin.xml /Y
copy *.png ..\release\GAMSApp_Licensed\plugins\GAMSExport\*.png /Y
copy G*.bat ..\release\GAMSApp_Licensed\plugins\GAMSExport\G*.bat /Y
copy gasm_l.bin ..\release\GAMSApp_Licensed\plugins\GAMS_files\gasm_l.bin /Y

cd ..\\Import
pyinstaller -y --upx-dir=../../upx GAMSImport.spec
xcopy dist\GAMSImport\* ..\release\GAMSApp_Licensed\plugins\GAMS_files\ /Y /E
copy plugin.xml ..\release\GAMSApp_Licensed\plugins\GAMSImport\plugin.xml /Y
copy *.png ..\release\GAMSApp_Licensed\plugins\GAMSImport\*.png /Y
copy G*.bat ..\release\GAMSApp_Licensed\plugins\GAMSImport\G*.bat /Y
copy gasm_l.bin ..\release\GAMSApp_Licensed\plugins\GAMS_files\gasm_l.bin /Y

cd ..\\Auto
pyinstaller -y --upx-dir=../../upx GAMSAutoRun.spec
xcopy dist\GAMSAutoRun\* ..\release\GAMSApp_Licensed\plugins\GAMS_files\ /Y /E
copy plugin.xml ..\release\GAMSApp_Licensed\plugins\GAMSAuto\plugin.xml /Y
copy *.png ..\release\GAMSApp_Licensed\plugins\GAMSAuto\*.png /Y
copy G*.bat ..\release\GAMSApp_Licensed\plugins\GAMSAuto\G*.bat /Y
copy gasm_l.bin ..\release\GAMSApp_Licensed\plugins\GAMS_files\gasm_l.bin /Y


pause
