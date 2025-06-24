@echo off
REM Navigate to your application directory
cd C:\Users\timch\OneDrive\Desktop\Japanese Flash Card App

REM Run the Streamlit application using the direct path to streamlit.exe
"C:\Users\timch\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\Scripts\streamlit.exe" run flashcard_app.py

echo.
echo Streamlit app launched.
echo If the browser window does not open automatically, check your command prompt for the local URL.
pause
