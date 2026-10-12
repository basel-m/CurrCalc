@echo off
pip install pyinstaller
pyinstaller --noconsole --onefile --name CurrencyCalc currency_calc.pyw
echo.
echo Done. Your app is in the "dist" folder: dist\CurrencyCalc.exe
pause
