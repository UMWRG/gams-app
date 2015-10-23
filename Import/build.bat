pyinstaller -y --upx-dir=../../upx GAMSImport.spec
xcopy dist\GAMSImport\* ..\GAMSPlugin\plugins\GAMSImport\ /Y /E
copy plugin.xml ..\GAMSPlugin\plugins\GAMSImport\plugin.xml /Y
copy *.png ..\GAMSPlugin\plugins\GAMSImport\plugin.xml /Y
pause
