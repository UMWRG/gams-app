pyinstaller --upx-dir=../../upx GAMSImport.spec
xcopy dist\GAMSImport\* ..\GAMSPlugin\plugins\GAMSImport\ /Y
copy plugin.xml ..\GAMSPlugin\plugins\GAMSImport\plugin.xml /Y
pause
