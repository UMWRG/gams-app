pyinstaller --upx-dir=../../upx GAMSImport.spec
xcopy dist\GAMSImport.exe ..\GAMSPlugin\plugins\GAMSImport\ /Y
copy plugin.xml ..\GAMSPlugin\plugins\GAMSImport\plugin.xml /Y
pause
