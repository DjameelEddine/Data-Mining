# Algerie Post Tracking Dashboard

Full-stack dashboard for the Algerie Post mail tracking system with AI-powered route duration predictions.

## Architecture

```
dashboard/
├── backend/          # FastAPI (Python)
│   ├── main.py       # App entry-point
│   ├── config.py     # Paths, keys, constants
│   ├── schemas.py    # Pydantic request/response models
│   ├── routers/      # API endpoints
│   │   ├── shipments.py      GET /api/shipments
│   │   ├── predictions.py    POST /api/predict/{id}
│   │   ├── stats.py          GET /api/stats/*
│   │   ├── chat.py           POST /api/chat
│   │   └── export.py         GET /api/export/pdf|excel
│   └── services/     # Business logic
│       ├── data_service.py   # Data loading & feature engineering
│       ├── ml_service.py     # CatBoost model inference
│       ├── ai_service.py     # Gemini AI chat
│       └── export_service.py # PDF & Excel generation
│
└── frontend/         # Next.js 14 + TypeScript + Tailwind + Recharts
    └── src/
        ├── app/page.tsx              # Main dashboard page
        ├── components/
        │   ├── Navbar.tsx            # Top navigation bar
        │   ├── MapView.tsx           # World map with tracking markers
        │   ├── StatusDonut.tsx       # Donut chart (Delivered/Transit/Delayed)
        │   ├── PredictionAccuracyCard.tsx
        │   ├── VolumeForecast.tsx    # Area chart
        │   ├── ShipmentsTable.tsx    # Data table with pagination
        │   └── ChatWidget.tsx        # Floating AI chat
        ├── lib/
        │   ├── api.ts               # Centralised API client
        │   └── utils.ts             # cn() helper
        └── types/index.ts           # Shared TypeScript interfaces
```

## Quick Start

### 1. Backend

```bash
cd dashboard/backend
pip install -r requirements.txt

# Run from the project root (Data-Mining/) so that relative paths resolve:
cd ../..
uvicorn dashboard.backend.main:app --reload --port 8000
```

The API will be available at **http://localhost:8000**. Swagger docs at `/docs`.

### 2. Frontend

```bash
cd dashboard/frontend
npm install
npm run dev
```

Open **http://localhost:3000** in your browser.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | built-in key | Google Gemini API key (backend) |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | FastAPI backend URL (frontend) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/shipments` | Paginated list with search, status, region filters |
| GET | `/api/shipments/{id}` | All scan events for a package |
| POST | `/api/predict/{id}` | Run CatBoost prediction for a package |
| GET | `/api/predictions/log` | View all past predictions |
| GET | `/api/stats/overview` | Total/delivered/transit/delayed counts |
| GET | `/api/stats/prediction-accuracy` | Model accuracy metrics |
| GET | `/api/stats/volume-forecast` | Weekly volume data for charts |
| POST | `/api/chat` | AI assistant (Gemini-powered) |
| GET | `/api/export/pdf/{id}` | Download PDF report for a package |
| GET | `/api/export/excel` | Download Excel of filtered shipments |
