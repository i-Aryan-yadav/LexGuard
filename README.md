# AI Contract Risk Platform

An AI-powered contract risk analysis platform that uses LegalBERT and Google Gemini to classify, segment, and score legal contract clauses for risk.

---

## 📋 Prerequisites

Before setting up, make sure the following are installed on your system:

| Requirement | Version | Notes |
|---|---|---|
| **Python** | 3.10+ | [Download](https://www.python.org/downloads/) |
| **pip** | Latest | Comes with Python |
| **Git** | Any | [Download](https://git-scm.com/) |
| **Tesseract OCR** | Any | Required for scanned PDF support |

### Installing Tesseract OCR

- **Windows**: Download installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add it to your system PATH.
- **macOS**: `brew install tesseract`
- **Linux (Ubuntu/Debian)**: `sudo apt install tesseract-ocr`

---

## 🚀 Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/ai-contract-risk-platform.git
cd ai-contract-risk-platform
```

### 2. Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** The first run will also download the `all-MiniLM-L6-v2` sentence-transformer model automatically (~80 MB).

### 4. Configure Environment Variables

Copy the example environment file and fill in your API keys:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Now open `.env` in any text editor and set the values:

```env
DATABASE_URL=sqlite+aiosqlite:///./contract_risk.db
OPENAI_API_KEY=             # Optional – leave blank if not using OpenAI
GEMINI_API_KEY=             # Required – your Google Gemini API key
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
LOG_LEVEL=INFO
```

> **Getting a Gemini API Key:**
> 1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
> 2. Sign in with your Google account
> 3. Click **Create API Key** and copy it into `.env`

### 5. Download NLTK Data

Open a Python shell and run:

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

Or run it as a one-liner:

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

---

## ▶️ Running the Application

You need to run **two terminals** — one for the backend API and one for the Streamlit frontend.

### Terminal 1 – Start the Backend (FastAPI)

```bash
# Make sure your venv is activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`  
Interactive API docs: `http://localhost:8000/docs`

### Terminal 2 – Start the Frontend (React + Vite)

```bash
cd frontend
npm install        # first time only
npm run dev
```

The UI will be available at: `http://localhost:5173`

---

## 📁 Project Structure

```
ai-contract-risk-platform/
├── app/
│   ├── api/                  # FastAPI route handlers
│   ├── core/                 # Config and settings
│   ├── domain/               # Data models and risk rules
│   ├── infrastructure/       # Database engine and schema
│   └── services/             # Core business logic
│       ├── classification_service.py
│       ├── contextual_classifier.py   # LegalBERT AI classifier
│       ├── contract_service.py
│       ├── risk_service.py
│       ├── segmentation_service.py
│       └── text_extraction.py
├── frontend/
│   └── streamlit_app.py      # Streamlit UI
├── contracts/                # Sample contract files
├── models/                   # Downloaded model weights (auto-generated)
├── .env.example              # Environment variable template
├── requirements.txt          # Python dependencies
└── README.md
```

---

## 🧪 Running Tests

```bash
# Run all tests
python -m pytest

# Run a specific test file
python test_risk_engine.py
python test_contextual_classifier.py
```

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Ensure your virtual environment is activated and you ran `pip install -r requirements.txt` |
| Tesseract not found | Install Tesseract and ensure it is added to your system `PATH` |
| `GEMINI_API_KEY` error | Make sure `.env` file exists and the key is set correctly |
| Database errors on startup | Delete `contract_risk.db` and restart the backend to recreate it |
| Port already in use | Change the port: `uvicorn app.main:app --port 8001` |

---

## 📄 License

This project is for educational and research purposes.
