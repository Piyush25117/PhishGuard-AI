<div align="center">

# 🛡️ PhishGuard AI — ML-Based Phishing & Scam URL Detector

Machine Learning-based system for detecting phishing and scam URLs in real-time.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green?logo=flask)](https://flask.palletsprojects.com/)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-orange?logo=scikit-learn)](https://scikit-learn.org/)
[![MongoDB](https://img.shields.io/badge/DB-MongoDB%20%7C%20SQLite-green?logo=mongodb)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)](https://www.docker.com/)

*Real-time ML-based detection of phishing and scam websites.*

</div>

---

## 📌 Project Overview

**PhishGuard AI** is a full-stack application that uses a trained **Random Forest classifier** to analyse URLs and determine whether they are safe or likely phishing/scam sites.

The system extracts **16 hand-crafted features** from any URL (WHOIS age, SSL status, suspicious character patterns, TLD risk, and more) and passes them through a scikit-learn pipeline to deliver a prediction with a confidence score in milliseconds.

Results are stored in **MongoDB** (with an automatic **SQLite fallback**) so you can review history and visualise statistics on an analytics dashboard.

---

## ✨ Features

| Category | Details |
|---|---|
| **ML Model** | Random Forest (200 trees)trained on synthetic dataset (for demonstration purposes) |
| **Feature Extraction** | 16 URL features: length, IP address, `@`, `//`, hyphens, dots, HTTPS, domain age, SSL cert, TLD risk, special chars, port, subdomains, path length, page-rank mock |
| **Prediction API** | `POST /api/predict` — returns label + confidence |
| **History API** | `GET /api/history` / `DELETE /api/history` |
| **Analytics API** | `GET /api/analytics` — aggregate stats |
| **Frontend** | Single-page dark UI with scanner, history table, donut chart |
| **Database** | MongoDB primary, auto-falls back to SQLite |
| **Docker** | Multi-stage build + `docker-compose` with Nginx reverse proxy |

---

## ⚙️ Special Handling

> ⚠️ Note: To reduce false positives during demonstration, some well-known domains (e.g., Google, Amazon, GitHub) are automatically classified as Safe.

---

## 🗂️ Project Structure

```
phishguard-ai/
├── backend/
│   ├── app.py                 # Flask application factory
│   ├── feature_extraction.py  # 16-feature URL analyser
│   ├── train_model.py         # Train & persist model.pkl
│   ├── model.pkl              # (generated after training)
│   ├── phishing.db            # (generated if SQLite fallback)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── predict.py         # POST /api/predict
│   │   ├── history.py         # GET/DELETE /api/history
│   │   └── analytics.py       # GET /api/analytics
│   └── database/
│       ├── __init__.py
│       └── db.py              # MongoDB / SQLite abstraction
├── frontend/
│   ├── index.html             # Full single-page UI
│   ├── style.css              # Premium dark theme
│   └── app.js                 # API integration & UI logic
├── Dockerfile                 # Multi-stage production image
├── docker-compose.yml         # MongoDB + Flask + Nginx
├── nginx.conf                 # Nginx reverse proxy config
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask 3, Flask-CORS, Gunicorn |
| ML | scikit-learn, Random Forest, StandardScaler pipeline |
| Feature Extraction | tldextract, python-whois, requests, ssl, socket |
| Database | MongoDB 7 (pymongo) with SQLite automatic fallback |
| Frontend | Vanilla HTML5 / CSS3 / ES2022 JavaScript |
| DevOps | Docker, Docker Compose, Nginx |

---

## 🚀 Quick Start (Local — No Docker)

### Prerequisites

- Python 3.10+ installed
- `pip` available
- (Optional) MongoDB running locally on port 27017

### 1. Clone / navigate to the project

```bash
cd phishguard-ai
```

### 2. Create & activate a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Train the model

```bash
python backend/train_model.py
```

This generates `backend/model.pkl`. You will see a classification report in the console.

### 5. Copy environment template

```bash
cp .env.example .env
# Edit .env if needed (MongoDB URI, port, etc.)
```

### 6. Start the Flask API server

```bash
python backend/app.py
```

API is now available at **http://localhost:5000**

### 7. Open the frontend

Simply open `frontend/index.html` in your browser (double-click or drag into Chrome/Firefox).

> **Tip:** If CORS blocks the request, serve the frontend with:
> ```bash
> cd frontend && python -m http.server 3000
> ```
> Then visit http://localhost:3000

---

## 🐳 Docker (Recommended for Production)

```bash
# Build & start all services (MongoDB + Flask + Nginx)
docker-compose up --build

# Frontend → http://localhost:3000
# API      → http://localhost:5000/api
```

Stop everything:

```bash
docker-compose down
```

---

## 📡 API Reference

### `POST /api/predict`

**Request:**
```json
{ "url": "https://suspicious-site.xyz/login" }
```

**Response:**
```json
{
  "id":         "664abc…",
  "url":        "https://suspicious-site.xyz/login",
  "prediction": "Phishing",
  "confidence": 0.93,
  "features": {
    "url_length": 42,
    "uses_https": 1,
    "ssl_valid":  0,
    "domain_age_days": 3,
    …
  }
}
```

### `GET /api/history?limit=50`

Returns the 50 most recent scan records.

### `DELETE /api/history`

Removes all stored predictions. Returns `{ "deleted": <count> }`.

### `GET /api/analytics`

```json
{
  "total": 120,
  "by_label": {
    "Safe":     { "count": 80, "avg_confidence": 0.92 },
    "Phishing": { "count": 40, "avg_confidence": 0.88 }
  },
  "phishing_rate": 0.333
}
```

### `GET /api/health`

Health-check: `{ "status": "ok" }`

---

## 🔍 How the ML Model Works

1. **Feature Extraction** — `feature_extraction.py` pulls 16 signals from any URL
2. **Feature Vector** — values are ordered and scaled in a `StandardScaler`
3. **Random Forest** — 200 decision trees vote on the class label
4. **Output** — majority label + probability of that class (confidence)

| Feature | Why it matters |
|---|---|
| URL length | Phishing URLs tend to be very long |
| IP address in hostname | Hiding the real domain |
| `@` symbol | Everything before `@` is ignored by browsers |
| HTTPS usage | Legitimate sites almost always use HTTPS |
| Domain age | Phishing domains are registered days before an attack |
| SSL certificate | Fraudulent sites often lack valid certs |
| Suspicious TLD | `.tk`, `.ml`, `.xyz` have high phishing prevalence |
| Subdomains count | `paypal.login.hack.xyz` tricks the eye |

---

## 🔮 Future Improvements

- [ ] **Real phishing dataset** — train on [UCI Phishing Dataset](https://archive.ics.uci.edu/ml/datasets/phishing+websites) or [PhishTank](https://www.phishtank.com/)
- [ ] **Real WHOIS API** — replace mock domain age with live lookup
- [ ] **Real PageRank** — integrate Moz / Majestic API
- [ ] **Browser extension** — check URLs before visiting
- [ ] **User accounts** — per-user scan history with JWT auth
- [ ] **Retraining pipeline** — online learning from user feedback
- [ ] **NLP features** — analyse page content for scam language
- [ ] **Ensemble model** — combine RF with XGBoost / LSTM
- [ ] **Webhook alerts** — Slack / email when phishing detected
- [ ] **Rate limiting** — prevent API abuse

---

## ⚠️ Limitations
- Uses synthetic dataset (not trained on real-world phishing datasets)
- WHOIS and SSL features may fail due to network/API restrictions
- Some complex or long URLs may produce false positives
- Detection is based on handcrafted features, not deep learning

---

## ☁️ Deployment Guide

### Render (Flask backend)

1. Push this repo to GitHub
2. New Render **Web Service** → select your repo
3. **Build command:** `pip install -r requirements.txt && python backend/train_model.py`
4. **Start command:** `gunicorn --chdir backend -b 0.0.0.0:$PORT "app:create_app()"`
5. Set environment variables: `MONGO_URI`, `MONGO_DB_NAME`

### Vercel (Frontend)

1. In Vercel, import the repo and set the **Root Directory** to `frontend`
2. No build step needed (static site)
3. Set `API_BASE` in `app.js` to your Render backend URL

---

## 📄 License

MIT — free to use, modify, and distribute.

---

<div align="center">
Built with ❤️ using Flask · scikit-learn · MongoDB · Vanilla JS
</div>
