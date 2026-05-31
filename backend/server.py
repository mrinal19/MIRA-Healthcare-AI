#!/usr/bin/env python3
"""
MIRA - Medical Intelligence Robotic Automation
Backend API Server
Python stdlib only - no external dependencies required
"""

import sqlite3
import json
import os
import sys
import re
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, date
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────────────
PORT = 8000
DB_PATH = Path(__file__).parent / "mira.db"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# ─── Database ─────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name   TEXT    NOT NULL,
            dob         TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            glucose     REAL    NOT NULL,
            haemoglobin REAL    NOT NULL,
            cholesterol REAL    NOT NULL,
            remarks     TEXT    DEFAULT '',
            created_at  TEXT    DEFAULT (datetime('now')),
            updated_at  TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()
    print(f"[MIRA] Database initialised → {DB_PATH}")

# ─── Validation ───────────────────────────────────────────────────────────────
def validate_patient(data: dict) -> list:
    errors = []
    required = ["full_name", "dob", "email", "glucose", "haemoglobin", "cholesterol"]
    for field in required:
        if field not in data or str(data[field]).strip() == "":
            errors.append(f"{field} is required")

    if errors:
        return errors

    # Email
    email_re = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_re, str(data["email"])):
        errors.append("Invalid email address format")

    # DOB - cannot be future
    try:
        dob = datetime.strptime(str(data["dob"]), "%Y-%m-%d").date()
        if dob >= date.today():
            errors.append("Date of birth cannot be today or a future date")
        if dob.year < 1900:
            errors.append("Date of birth is unrealistically old")
    except ValueError:
        errors.append("Date of birth must be in YYYY-MM-DD format")

    # Numeric blood test values
    for field in ["glucose", "haemoglobin", "cholesterol"]:
        try:
            val = float(data[field])
            if val <= 0:
                errors.append(f"{field} must be a positive number")
        except (ValueError, TypeError):
            errors.append(f"{field} must be a numeric value")

    return errors

# ─── AI Prediction ────────────────────────────────────────────────────────────
def get_ai_remarks(patient_data: dict) -> str:
    """Call Claude API (Anthropic) for health risk prediction."""
    if not ANTHROPIC_API_KEY:
        return fallback_prediction(patient_data)

    try:
        name = patient_data["full_name"]
        dob  = patient_data["dob"]
        glucose     = float(patient_data["glucose"])
        haemoglobin = float(patient_data["haemoglobin"])
        cholesterol = float(patient_data["cholesterol"])

        # Calculate age
        birth = datetime.strptime(dob, "%Y-%m-%d")
        age   = (datetime.today() - birth).days // 365

        prompt = f"""You are MIRA, a medical AI assistant. Analyse these patient blood test results and provide a brief clinical risk assessment.

Patient: {name}, Age: {age}
Blood Test Results:
- Glucose:      {glucose} mg/dL   (Normal: 70–99 mg/dL fasting)
- Haemoglobin:  {haemoglobin} g/dL (Normal: M 13.5–17.5, F 12–15.5 g/dL)
- Cholesterol:  {cholesterol} mg/dL (Desirable: <200, Borderline: 200–239, High: ≥240)

Provide a concise clinical risk summary in 2-3 sentences covering:
1. Individual parameter interpretation (normal/abnormal/critical)
2. Potential health conditions indicated (e.g. diabetes risk, anaemia, cardiovascular risk)
3. Recommended follow-up action

Keep it professional, factual and clinical. Do not use markdown formatting."""

        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}]
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type":      "application/json",
                "x-api-key":         ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            return result["content"][0]["text"].strip()

    except Exception as e:
        print(f"[MIRA] AI API error: {e}")
        return fallback_prediction(patient_data)

def fallback_prediction(data: dict) -> str:
    """Rule-based fallback when API key not set."""
    glucose     = float(data.get("glucose", 0))
    haemoglobin = float(data.get("haemoglobin", 0))
    cholesterol = float(data.get("cholesterol", 0))
    issues = []

    if glucose < 70:
        issues.append("hypoglycaemia (low blood sugar)")
    elif 100 <= glucose < 126:
        issues.append("pre-diabetic glucose level")
    elif glucose >= 126:
        issues.append("diabetic-range glucose — immediate follow-up advised")

    if haemoglobin < 12:
        issues.append("anaemia (low haemoglobin)")
    elif haemoglobin > 17.5:
        issues.append("polycythaemia (elevated haemoglobin)")

    if 200 <= cholesterol < 240:
        issues.append("borderline high cholesterol")
    elif cholesterol >= 240:
        issues.append("high cholesterol — cardiovascular risk")

    if not issues:
        return ("All three parameters (glucose, haemoglobin, cholesterol) are within normal reference ranges. "
                "No immediate clinical concerns identified. Routine annual review recommended.")
    return (f"Blood results indicate: {'; '.join(issues)}. "
            "Clinical correlation is recommended. "
            "Please consult a physician for further evaluation and management.")

# ─── CRUD Handlers ────────────────────────────────────────────────────────────
def handle_get_patients(query_params: dict) -> dict:
    conn = get_db()
    search = query_params.get("search", [""])[0].strip()
    if search:
        rows = conn.execute(
            "SELECT * FROM patients WHERE full_name LIKE ? OR email LIKE ? ORDER BY updated_at DESC",
            (f"%{search}%", f"%{search}%")
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM patients ORDER BY updated_at DESC").fetchall()
    conn.close()
    return {"patients": [dict(r) for r in rows], "total": len(rows)}

def handle_get_patient(pid: int) -> object:
    conn = get_db()
    row  = conn.execute("SELECT * FROM patients WHERE id = ?", (pid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def handle_create_patient(data: dict) -> dict:
    errors = validate_patient(data)
    if errors:
        return {"error": errors}

    # Check duplicate email
    conn = get_db()
    existing = conn.execute("SELECT id FROM patients WHERE email = ?", (data["email"],)).fetchone()
    if existing:
        conn.close()
        return {"error": ["A patient with this email already exists"]}

    remarks = get_ai_remarks(data)
    try:
        cursor = conn.execute(
            "INSERT INTO patients (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks) VALUES (?,?,?,?,?,?,?)",
            (data["full_name"].strip(), data["dob"], data["email"].strip().lower(),
             float(data["glucose"]), float(data["haemoglobin"]), float(data["cholesterol"]), remarks)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (cursor.lastrowid,)).fetchone()
        conn.close()
        return {"patient": dict(row)}
    except Exception as e:
        conn.close()
        return {"error": [str(e)]}

def handle_update_patient(pid: int, data: dict) -> dict:
    errors = validate_patient(data)
    if errors:
        return {"error": errors}

    conn = get_db()
    existing = conn.execute("SELECT id FROM patients WHERE email = ? AND id != ?", (data["email"], pid)).fetchone()
    if existing:
        conn.close()
        return {"error": ["Another patient with this email already exists"]}

    remarks = get_ai_remarks(data)
    try:
        conn.execute(
            """UPDATE patients SET full_name=?, dob=?, email=?, glucose=?, haemoglobin=?, cholesterol=?,
               remarks=?, updated_at=datetime('now') WHERE id=?""",
            (data["full_name"].strip(), data["dob"], data["email"].strip().lower(),
             float(data["glucose"]), float(data["haemoglobin"]), float(data["cholesterol"]), remarks, pid)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (pid,)).fetchone()
        conn.close()
        if not row:
            return {"error": ["Patient not found"]}
        return {"patient": dict(row)}
    except Exception as e:
        conn.close()
        return {"error": [str(e)]}

def handle_delete_patient(pid: int) -> dict:
    conn = get_db()
    row = conn.execute("SELECT id FROM patients WHERE id = ?", (pid,)).fetchone()
    if not row:
        conn.close()
        return {"error": ["Patient not found"]}
    conn.execute("DELETE FROM patients WHERE id = ?", (pid,))
    conn.commit()
    conn.close()
    return {"deleted": True, "id": pid}

# ─── HTTP Handler ─────────────────────────────────────────────────────────────
class MIRAHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[MIRA] {self.address_string()} → {fmt % args}")

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path):
        try:
            content = path.read_bytes()
            ext = path.suffix.lower()
            mime = {
                ".html": "text/html",
                ".js":   "application/javascript",
                ".css":  "text/css",
                ".ico":  "image/x-icon",
                ".json": "application/json",
                ".png":  "image/png",
                ".svg":  "image/svg+xml"
            }.get(ext, "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def route(self):
        parsed = urllib.parse.urlparse(self.path)
        path   = parsed.path.rstrip("/")
        params = urllib.parse.parse_qs(parsed.query)
        parts  = [p for p in path.split("/") if p]
        return path, params, parts

    def do_GET(self):
        path, params, parts = self.route()

        # API routes
        if path == "/api/patients":
            self.send_json(handle_get_patients(params))
            return
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "patients":
            try:
                pid = int(parts[2])
            except ValueError:
                self.send_json({"error": "Invalid ID"}, 400)
                return
            patient = handle_get_patient(pid)
            if patient:
                self.send_json({"patient": patient})
            else:
                self.send_json({"error": "Patient not found"}, 404)
            return
        if path == "/api/health":
            self.send_json({"status": "ok", "service": "MIRA", "ai_enabled": bool(ANTHROPIC_API_KEY)})
            return

        # Serve frontend
        if path == "" or path == "/":
            target = FRONTEND_DIR / "index.html"
        else:
            target = FRONTEND_DIR / path.lstrip("/")

        if target.is_file():
            self.send_file(target)
        elif (FRONTEND_DIR / "index.html").exists():
            # SPA fallback
            self.send_file(FRONTEND_DIR / "index.html")
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        path, _, parts = self.route()
        if path == "/api/patients":
            data   = self.read_body()
            result = handle_create_patient(data)
            status = 201 if "patient" in result else 400
            self.send_json(result, status)
        else:
            self.send_error(404)

    def do_PUT(self):
        _, _, parts = self.route()
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "patients":
            try:
                pid = int(parts[2])
            except ValueError:
                self.send_json({"error": "Invalid ID"}, 400)
                return
            data   = self.read_body()
            result = handle_update_patient(pid, data)
            status = 200 if "patient" in result else 400
            self.send_json(result, status)
        else:
            self.send_error(404)

    def do_DELETE(self):
        _, _, parts = self.route()
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "patients":
            try:
                pid = int(parts[2])
            except ValueError:
                self.send_json({"error": "Invalid ID"}, 400)
                return
            result = handle_delete_patient(pid)
            status = 200 if "deleted" in result else 404
            self.send_json(result, status)
        else:
            self.send_error(404)

# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    server = HTTPServer(("0.0.0.0", PORT), MIRAHandler)
    ai_status = "Claude AI enabled ✓" if ANTHROPIC_API_KEY else "Rule-based fallback (set ANTHROPIC_API_KEY to enable AI)"
    print(f"""
╔══════════════════════════════════════════════════════════╗
║   MIRA – Medical Intelligence Robotic Automation         ║
║   Backend API Server                                     ║
╠══════════════════════════════════════════════════════════╣
║   URL:  http://localhost:{PORT}                             ║
║   DB:   {str(DB_PATH):<48}║
║   AI:   {ai_status:<48}║
╚══════════════════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[MIRA] Server stopped.")
        sys.exit(0)
