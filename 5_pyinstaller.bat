REM If it fails due to matplotlib, look at https://stackoverflow.com/a/67922414/36061
REM --noupx see https://stackoverflow.com/a/28415085/36061
cd pyinst
REM trying to diagnose why it takes a long time to open
REM pyinstaller --name "pdCIFplotter" --onefile --noupx --debug=all ..\src\pdCIFplotter\__main__.py --icon ..\src\pdCIFplotter\icon.ico
REM pyinstaller --name "pdCIFplotter" --onefile --noupx --debug=imports ..\src\pdCIFplotter\__main__.py --icon ..\src\pdCIFplotter\icon.ico
REM pyinstaller --name "pdCIFplotter" --onefile --noupx --debug=bootloader ..\src\pdCIFplotter\__main__.py --icon ..\src\pdCIFplotter\icon.ico
REM pyinstaller --name "pdCIFplotter" --onefile --noupx --debug=noarchive ..\src\pdCIFplotter\__main__.py --icon ..\src\pdCIFplotter\icon.ico
REM pyinstaller --name "pdCIFplotter" --onefile --noupx  ..\src\pdCIFplotter\__main__.py --icon ..\src\pdCIFplotter\icon.ico


REM trying to diagnose why it takes a long time to open
REM pyinstaller --name "pdCIFplotter" --onedir --noupx --debug=all ..\src\pdCIFplotter\__main__.py --icon ..\src\pdCIFplotter\icon.ico
REM pyinstaller --name "pdCIFplotter" --onedir --noupx --debug=imports ..\src\pdCIFplotter\__main__.py --icon ..\src\pdCIFplotter\icon.ico
REM pyinstaller --name "pdCIFplotter" --onedir --noupx --debug=bootloader ..\src\pdCIFplotter\__main__.py --icon ..\src\pdCIFplotter\icon.ico
pyinstaller --name "pdCIFplotter" --onedir --noupx --debug=noarchive ..\src\pdCIFplotter\__main__.py --icon ..\src\pdCIFplotter\icon.ico
REM pyinstaller --name "pdCIFplotter" --onedir --noupx ..\src\pdCIFplotter\__main__.py --icon ..\src\pdCIFplotter\icon.ico



cd ..
pause