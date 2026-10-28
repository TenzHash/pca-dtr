@echo off
REM Builds the DTR Generator desktop program (Windows, Python 3.10.11+; 3.12 recommended).
pip install -r requirements.txt
python -m PyInstaller --onefile --windowed --name DTR_Generator --paths . ^
  --hidden-import zkparser --hidden-import schedules --hidden-import form48 ^
  --hidden-import roster --hidden-import generate_dtr --hidden-import ui --hidden-import app --hidden-import version --hidden-import auth ^
  --hidden-import xlrd --hidden-import webview --collect-data reportlab desktop.py
echo.
echo Done. Your program is dist\DTR_Generator.exe - double-click it to open the app window.
echo Data is kept in a DTR_Data folder next to the .exe (errors, if any, go to DTR_Data\error.log).
pause
