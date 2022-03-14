REM If it fails due to matplotlib, look at https://stackoverflow.com/a/67922414/36061
REM --noupx see https://stackoverflow.com/a/28415085/36061
cd pyinst
pyinstaller --name "pdCIFplotter" --onefile --noupx ..\src\pdCIFplotter\__main__.py --icon ..\src\pdCIFplotter\icon.ico
REM pyinstaller --name "pdCIFplotter" --onedir --noupx ..\src\pdCIFplotter\__main__.py --icon ..\src\pdCIFplotter\icon.ico
cd ..
pause