cd Export
pyinstaller --upx-dir=../../upx GAMSExport.spec
xcopy dist\GAMSExport\* ..\GAMSPlugin\plugins\GAMSExport\ /Y /s
copy plugin.xml ..\GAMSPlugin\plugins\GAMSExport\plugin.xml /Y
cd ..\\Import
pyinstaller --upx-dir=../../upx GAMSImport.spec
xcopy dist\GAMSImport\* ..\GAMSPlugin\plugins\GAMSImport\ /Y
copy plugin.xml ..\GAMSPlugin\plugins\GAMSImport\plugin.xml /Y
cd ..\\Auto
pyinstaller --upx-dir=../../upx GAMSAutoRun.spec
xcopy dist\GAMSAutoRun\* ..\GAMSPlugin\plugins\GAMSAuto\ /Y /s
copy plugin.xml ..\GAMSPlugin\plugins\GAMSAuto\plugin.xml /Y
pause