# MIRA – Medical Intelligence Robotic Automation

> Task 1 Submission — Junior AI/ML Developer Assessment  
> A health prediction application using patient blood test results and Claude AI (Anthropic)

---

## 📋 Project Overview

MIRA is a full-stack health prediction platform that:
- Manages patient records with full CRUD operations
- Collects blood test data (Glucose, Haemoglobin, Cholesterol)
- Automatically calls the **Claude AI API** (Anthropic) to generate clinical risk assessments
- Stores all data persistently in **SQLite**
- Provides a modern, responsive **React** frontend

---

## 🗂 Project Structure

```
mira-health/
├── backend/
│   └── server.py          # Python HTTP server + REST API (stdlib only)
├── frontend/
│   └── index.html         # React SPA (CDN, no build step)
├── start.sh               # One-command startup script
├── requirements.txt       # Empty — no external Python deps needed
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (check: `python3 --version`)
- A modern browser (Chrome, Firefox, Safari)
- Anthropic API key (optional — app works without it using rule-based fallback)

### 1. Clone / Download the project
```bash
cd ~/Desktop
# If using git:
git clone <your-repo-url>
cd mira-health
```

### 2. Set your Anthropic API key (recommended)
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```
> Get a free API key at https://console.anthropic.com  
> Without this, the app uses a built-in rule-based health assessment instead.

### 3. Run the server
```bash
python3 backend/server.py
```

### 4. Open the app
```
http://localhost:8000
```

That's it — **no pip installs, no npm, no build step required.**

---

## ✅ Features Implemented

| Requirement | Status | Details |
|---|---|---|
| Create patient record | ✅ | Form with validation, AI analysis on save |
| Read / list patients | ✅ | Table with search, stats dashboard |
| Update patient record | ✅ | Edit modal, re-runs AI analysis |
| Delete patient record | ✅ | Confirmation dialog |
| Input validation | ✅ | Email format, future DOB blocked, numeric checks |
| Persistent storage | ✅ | SQLite database (`mira.db`) |
| AI/ML API integration | ✅ | Claude (Anthropic) API for health risk prediction |
| Clean UI | ✅ | Dark medical theme, responsive, animated |
| REST API | ✅ | Full CRUD endpoints at `/api/patients` |

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/patients` | List all patients (supports `?search=`) |
| `GET` | `/api/patients/:id` | Get single patient |
| `POST` | `/api/patients` | Create patient + AI analysis |
| `PUT` | `/api/patients/:id` | Update patient + re-analyse |
| `DELETE` | `/api/patients/:id` | Delete patient |
| `GET` | `/api/health` | Server health check |

### Example POST body
```json
{
  "full_name": "Priya Sharma",
  "dob": "1990-03-15",
  "email": "priya@example.com",
  "glucose": 112.5,
  "haemoglobin": 10.2,
  "cholesterol": 235.0
}
```

---

## 🤖 AI Integration

When a patient record is saved, the backend:
1. Builds a clinical prompt with the patient's age and blood test values
2. Calls the **Claude claude-sonnet-4-20250514** model via `api.anthropic.com/v1/messages`
3. Returns a 2–3 sentence clinical risk assessment stored in the `remarks` field

**Reference ranges used:**
- Glucose: Normal 70–99 mg/dL, Pre-diabetic 100–125, Diabetic ≥126
- Haemoglobin: Male 13.5–17.5 g/dL, Female 12–15.5 g/dL
- Cholesterol: Desirable <200, Borderline 200–239, High ≥240 mg/dL

---

## 🛠 Technology Stack

| Layer | Technology | Why |
|---|---|---|
| **Backend** | Python 3 (stdlib only) | Zero dependencies, runs anywhere, clean REST API |
| **Database** | SQLite | Built into Python, persistent, perfect for this scale |
| **Frontend** | React 18 via CDN | No build step, component-based, modern UX |
| **AI** | Claude (Anthropic) | State-of-the-art medical NLP, reliable API |
| **Fonts** | Google Fonts (Syne + Space Grotesk) | Distinctive medical/tech aesthetic |

**Why stdlib-only backend?**  
Using only Python's built-in `http.server`, `sqlite3`, `json`, and `urllib` means the app runs on any Python 3.8+ installation with absolutely zero setup. This demonstrates understanding of fundamentals rather than just knowing how to `pip install` a framework.

---

## 🏗 Challenges & Decisions

1. **No pip install environment** — Solved by building on stdlib. `http.server` + `sqlite3` + `urllib` gives a fully functional REST API.
2. **AI fallback** — If no API key is set, a rule-based classifier provides meaningful health assessments so the app is always functional.
3. **SPA routing** — The backend serves `index.html` for all non-API routes, enabling proper React client-side routing.
4. **CORS** — All API responses include `Access-Control-Allow-Origin: *` so the frontend can be served separately during development.

---

## 📸 Screenshots

Run the app and visit `http://localhost:8000` to see:
- Dashboard with patient stats
- Full CRUD interface with search
- AI-generated clinical remarks per patient
- Colour-coded blood test status pills

---

*Built for the MIRA platform — Gokul Infocare Junior AI/ML Developer Assessment*
