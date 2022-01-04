REM If it fails due to matplotlib, look at https://stackoverflow.com/a/67922414/36061
cd pyinst
pyinstaller --name "pdCIFplotter" --onefile ..\src\pdCIFplotter\__main__.py --icon ..\src\pdCIFplotter\icon.ico
cd ..
pause