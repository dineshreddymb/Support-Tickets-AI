@echo off
REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run Streamlit app
echo.
echo Starting AI Support Ticket Assistant...
echo Open browser to: http://localhost:8501
echo.
python -m streamlit run app.py
