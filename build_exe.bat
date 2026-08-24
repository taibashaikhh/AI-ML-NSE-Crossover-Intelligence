@echo off
setlocal
call venv\Scripts\activate
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean --onedir --name StockScreener dashboard_launcher.py
copy .env.example dist\StockScreener\ >nul
copy README.md dist\StockScreener\ >nul
xcopy data_store dist\StockScreener\data_store\ /E /I /Y >nul 2>nul
xcopy models dist\StockScreener\models\ /E /I /Y >nul 2>nul
 echo.
echo Built: dist\StockScreener\StockScreener.exe
echo IMPORTANT: .env is NOT bundled. Configure it beside the executable before running.
pause
