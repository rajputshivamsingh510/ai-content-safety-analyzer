# 🛡️ SafeScript AI

Streamlit UI for a parallel LangGraph content safety analyzer.

## Pipeline

```text
                    INPUT
                      |
          +-----------+-----------+
          |           |           |
       Toxicity   Copyright    Culture
          |           |           |
          +-----------+-----------+
                      |
                   Reducer
                      |
                 Safety Report
```

## Run

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env`:

```env
GROQ_API_KEY=your_groq_api_key
```

Start:

```powershell
streamlit run app.py
```
