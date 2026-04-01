# LinkedIn Post Generator

Chrome extension + FastAPI backend that generates LinkedIn posts and smart replies using Claude AI.

## Setup

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-xxxxx
uvicorn main:app --reload --port 8000
```

### Extension
1. Open `chrome://extensions`
2. Enable Developer mode
3. Click "Load unpacked" → select `extension/` folder
4. Pin to toolbar, open LinkedIn, click icon
