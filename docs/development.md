# Agent Forge — Developer Setup & Integration Guide

This guide covers local environment setup, running unit tests, starting backend services, configuring the Next.js frontend, and contributing code.

---

## 1. Environment Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ / npm
- Git

### Backend Setup
```bash
cd Agent_Forge
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Provide your `GEMINI_API_KEY` in `.env`.

---

## 2. Running Local Services

### FastAPI Backend
```bash
uvicorn app.main:app --reload --port 8000
```
Interactive Swagger API documentation will be available at: `http://localhost:8000/docs`

### Next.js Frontend Dashboard (PLANNED / In Development on `member-4`)
```bash
cd frontend
npm install
npm run dev
```
Dashboard will be accessible at: `http://localhost:3000`

---

## 3. Running Backend Unit Tests

Run pytest across all schemas and entrypoints:
```bash
pytest -v
```

---

## 4. Git Branch Workflow & PRs

Refer to [`CONTRIBUTING.md`](../CONTRIBUTING.md) for full branch strategy (`main`, `common`, `member-1` .. `member-4`), conventional commit standards, and PR submission rules.
