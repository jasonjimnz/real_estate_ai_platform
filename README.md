# 🏠 NestScout (this name is from AI, but sounds cool)

**AI-powered real estate intelligence platform with 100 % personalised property scoring.**

NestScout aggregates property listings from multiple sources, enriches them with nearby Points of Interest (cafés, schools, transport, shops…), and lets every user define custom scoring rules to rank properties by what truly matters to them.

---

## ✨ Key Features

- **Multi-source import** — manual entry, CSV/Excel upload, URL extraction (AI-powered), API connectors, scheduled scrapers.
- **POI enrichment** — automatically maps nearby businesses and services around every property.
- **Personal scoring engine** — user-defined weighted rules produce a 0–100 score per property, per profile.
- **AI assistant** — natural-language search, price predictions, and neighbourhood Q&A powered by LangChain agents.
- **Interactive map** — properties colour-coded by personal score with POI overlays.

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vite + React + TypeScript |
| Backend | Flask (Application Factory) |
| Database | PostgreSQL + PostGIS |
| Vector DB | Qdrant |
| Task Queue | Celery + Redis |
| AI / ML | LangChain + Local LLM (Ollama / LM Studio) |
| Containers | Docker (multi-stage) |

## 📁 Project Structure

```text
real_estate/
├── app/                  # Flask application (factory pattern)
│   ├── __init__.py       # create_app()
│   ├── extensions.py     # SQLAlchemy, Migrate, etc.
│   ├── models/           # SQLAlchemy 2.0 models
│   ├── api/              # Blueprints (routes)
│   └── services/         # Business logic layer
├── frontend/             # Vite + React + TypeScript
├── migrations/           # Alembic migrations
├── tests/                # Pytest suite
├── config.py             # Configuration classes
├── run.py                # Entry point
├── DesignDoc.md          # Full design document
├── requirements.txt
├── docker-compose.yml
└── Dockerfile
```

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/your-username/nestscout.git
cd nestscout

# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Environment
cp .env.example .env   # Edit with your settings

# Database
flask db upgrade

# Run
python run.py
```

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0** — see the [LICENSE](LICENSE) file for details.

---

> **Author:** Jason Jiménez Cruz · 2026
