cd Export
pyinstaller -y --upx-dir=../../upx GAMSExport.spec
xcopy dist\GAMSExport\* ..\GAMSPlugin_Licensed\plugins\GAMSExport\ /Y /E
copy plugin.xml ..\GAMSPlugin_Licensed\plugins\GAMSExport\plugin.xml /Y
copy *.png ..\GAMSPlugin_Licensed\plugins\GAMSExport\*.png /Y
copy gasm_l.bin ..\GAMSPlugin_Licensed\plugins\GAMSExport\gasm_l.bin /Y
cd ..\\Import
pyinstaller -y --upx-dir=../../upx GAMSImport.spec
xcopy dist\GAMSImport\* ..\GAMSPlugin_Licensed\plugins\GAMSImport\ /Y /E
copy plugin.xml ..\GAMSPlugin_Licensed\plugins\GAMSImport\plugin.xml /Y
copy *.png ..\GAMSPlugin_Licensed\plugins\GAMSImport\*.png /Y
copy gasm_l.bin ..\GAMSPlugin_Licensed\plugins\GAMSImport\gasm_l.bin /Y
cd ..\\Auto
pyinstaller -y --upx-dir=../../upx GAMSAutoRun.spec
xcopy dist\GAMSAutoRun\* ..\GAMSPlugin_Licensed\plugins\GAMSAuto\ /Y /E
copy plugin.xml ..\GAMSPlugin_Licensed\plugins\GAMSAuto\plugin.xml /Y
copy gasm_l.bin ..\GAMSPlugin_Licensed\plugins\GAMSAuto\gasm_l.bin /Y

copy *.png ..\GAMSPlugin_Licensed\plugins\GAMSAuto\*.png /Y
pause