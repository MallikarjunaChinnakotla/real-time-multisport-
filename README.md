# 🏆 Real-Time Multi-Sport Dashboard

A full-stack web application for managing and live-scoring **9 sports** with real-time statistics, player management, team tracking, tournament scheduling, and match awards.

---

## 🚀 Quick Start

> **One-command launch (Windows)**
```bash
start.bat
```
This script opens two terminal windows — one for the backend, one for the frontend.

| Service    | URL                           |
|------------|-------------------------------|
| Frontend   | http://localhost:5173         |
| Backend    | http://localhost:8000         |
| API Docs   | http://localhost:8000/docs    |

---

## 📁 Project Structure

```
pro/
├── backend/                   # FastAPI REST API
│   ├── main.py                # API routes for all 9 sports
│   └── crud.py                # CSV-based data layer (CRUD operations)
│
├── frontend/                  # React + TypeScript + Vite app
│   └── src/
│       ├── App.tsx            # Root component with routing
│       ├── api/index.ts       # Axios API client (points to :8000)
│       └── components/
│           ├── Layout.tsx     # Sidebar navigation + app shell
│           ├── SportDashboard.tsx  # Per-sport tab navigation
│           └── modules/       # Feature modules
│               ├── Tournaments.tsx
│               ├── Teams.tsx
│               ├── Players.tsx
│               ├── Schedule.tsx
│               ├── LiveScoring.tsx
│               ├── Stats.tsx
│               ├── Awards.tsx
│               └── scoring/   # Sport-specific live scoring UIs
│
├── sports/                    # Streamlit sport modules (legacy UI)
│   ├── cricket.py
│   ├── football.py
│   └── ... (9 sports total)
│
├── sports_dashboard/data/     # CSV files (auto-created on first run)
├── score_predictor.pkl        # ML model: score prediction
├── win_predictor.pkl          # ML model: win prediction
├── app.py                     # Streamlit entry point (legacy)
├── requirements.txt           # Python dependencies
└── start.bat                  # One-click launcher
```

---

## 🏅 Supported Sports

| Sport         | Live Scoring | Stats | Awards |
|---------------|:---:|:---:|:---:|
| Cricket       | ✅ | ✅ | ✅ |
| Football      | ✅ | ✅ | ✅ |
| Basketball    | ✅ | ✅ | ✅ |
| Volleyball    | ✅ | ✅ | ✅ |
| Kabaddi       | ✅ | ✅ | ✅ |
| Handball      | ✅ | ✅ | ✅ |
| Table Tennis  | ✅ | ✅ | ✅ |
| Hockey        | ✅ | ✅ | ✅ |
| Softball      | ✅ | ✅ | ✅ |

---

## 🛠️ Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19 | UI framework |
| TypeScript | 5.9 | Type safety |
| Vite | 7 | Dev server & bundler |
| React Router | 7 | Client-side routing |
| Tailwind CSS | 4 | Styling |
| Recharts | 3 | Statistics charts |
| Axios | 1.x | HTTP client |
| Lucide React | latest | Icons |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.115 | REST API framework |
| Uvicorn | 0.30 | ASGI server |
| Pandas | 2.2 | CSV data management |
| scikit-learn | 1.6 | ML predictions |
| NumPy | 2.0 | Numerical ops |

### Data Storage
- **CSV files** stored in `sports_dashboard/data/` (auto-created)
- File naming convention: `{sport}_{module}.csv`
  e.g., `cricket_teams.csv`, `football_matches.csv`

---

## ⚙️ Prerequisites

- **Python** 3.11+
- **Node.js** 18+
- **npm** 8+

---

## 📦 Installation

### 1. Install Python Dependencies
```bash
pip install fastapi uvicorn pandas numpy scikit-learn joblib python-dotenv streamlit
```

### 2. Install Frontend Dependencies
```bash
cd frontend
npm install
```

---

## ▶️ Running the Application

### Option A: One-Click (Recommended)
Double-click `start.bat` from the project root.

### Option B: Manual Start

**Terminal 1 — Backend**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend**
```bash
cd frontend
npm run dev
```

### Option C: Streamlit (Legacy UI)
```bash
streamlit run app.py
```

---

## 🔗 API Reference

All endpoints follow the pattern: `/api/{sport}/{resource}`

**Supported sports**: `cricket`, `football`, `basketball`, `volleyball`, `kabaddi`, `handball`, `table_tennis`, `hockey`, `softball`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/{sport}/tournaments` | List tournaments |
| POST | `/api/{sport}/tournaments` | Create tournament |
| DELETE | `/api/{sport}/tournaments/{id}` | Delete tournament |
| GET | `/api/{sport}/teams` | List teams |
| POST | `/api/{sport}/teams` | Create team |
| DELETE | `/api/{sport}/teams/{id}` | Delete team |
| GET | `/api/{sport}/players` | List players |
| POST | `/api/{sport}/players` | Create player |
| DELETE | `/api/{sport}/players/{id}` | Delete player |
| GET | `/api/{sport}/matches` | List matches |
| POST | `/api/{sport}/matches` | Schedule match |
| DELETE | `/api/{sport}/matches/{id}` | Delete match |
| GET | `/api/{sport}/scores` | Get scores |
| POST | `/api/{sport}/scores` | Submit score event |
| GET | `/api/{sport}/stats` | Get full statistics |

> 📖 Interactive docs available at **http://localhost:8000/docs**

---

## ✨ Features

- **Tournament Management** — Create, view, and delete tournaments per sport
- **Team & Player Management** — Register teams and players with profile info
- **Match Scheduling** — Schedule matches with date, venue, and team selection
- **Live Scoring** — Real-time, sport-specific scoring panels (balls, overs, points, raids, etc.)
- **Statistics Dashboard** — Visual charts (bar, pie, line) powered by Recharts
- **Awards & Match Summary** — Auto-generated MVP, best bowler, top scorer, and more
- **ML Predictions** — Score and win predictions using pre-trained scikit-learn models

---

## 🧹 Data Management

All data is stored as CSV files. To reset a sport's data, delete the corresponding CSV files:

```bash
del sports_dashboard\data\cricket_*.csv
```

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| Backend fails to start | Run `pip install fastapi uvicorn pandas` |
| Frontend 404 on API calls | Make sure backend is running on port 8000 |
| `node_modules` missing | Run `npm install` inside `frontend/` |
| CORS errors in browser | Backend already has `allow_origins=["*"]` configured |
| CSV read errors | Check `sports_dashboard/data/` directory exists |

---

## 📄 License

This project is for educational/personal use.
