## Architecture

- **Backend API** (FastAPI) → deployed on Render with Docker
- **Frontend** (Streamlit) → coming later
- **Model** → XGBoost tuned regressor (~1MB), trained on Belgian real estate data

## Project structure

```
immo-eliza-deployment/
├── api/
│   ├── model/              # saved model + preprocessing artifacts
│   │   ├── xgboost_tuned.joblib
│   │   └── preprocessors.joblib
│   ├── predict.py          # standalone prediction pipeline
│   ├── app.py              # FastAPI application
│   ├── Dockerfile
│   └── requirements.txt
├── streamlit/              # (coming later)
└── README.md
```

## API endpoints

### `GET /`
Health check — returns `"alive"` if the server is running.

### `POST /predict`
Predict the price of a property.

**Required fields:**
| Field | Type | Description |
|-------|------|-------------|
| property_type | string | "apartment" or "house" |
| province | string | e.g. "brussels", "antwerp", "liege" |
| livable_surface | int | living area in m² |
| bedroom_count | int | number of bedrooms |

**Optional fields:**
| Field | Type | Default |
|-------|------|---------|
| property_state | string | null |
| total_surface | int | null |
| build_year | int | null |
| garage | int | 0 |
| terrace | int | 0 |
| swimming_pool | int | 0 |
| energy_consumption | float | null |
| latitude / longitude | float | null |
| preschool_distance_m | float | null |
| train_station_distance_m | float | null |
| supermarket_distance_m | float | null |
| nearest_city_distance_km | float | null |

**Example request:**
```json
{
  "data": {
    "property_type": "apartment",
    "province": "brussels",
    "livable_surface": 75,
    "bedroom_count": 2,
    "terrace": 1
  }
}
```

**Example response:**
```json
{
  "prediction": 275738.45,
  "status_code": 200
}
```

## Run locally

```bash
cd api
pip install -r requirements.txt
uvicorn app:app --reload
```

Then check `http://localhost:8000/docs` for the interactive API documentation.

## Run with Docker

```bash
cd api
docker build -t immo-eliza-api .
docker run -p 8000:8000 immo-eliza-api
```

## Deploy on Render

1. Push this repo to GitHub
2. Go to render.com → New Web Service
3. Connect your GitHub repo
4. Set Root Directory to `api`
5. Render auto-detects the Dockerfile