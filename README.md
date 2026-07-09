# Immo Eliza - Deployment

Final part of the Immo Eliza project. After scraping, cleaning, analyzing and building ML models, this repo deploys the price prediction model as a web app with a FastAPI backend and a Streamlit frontend.

**Live demo:** https://immo-eliza-deployment-67h8aj95mmw28wr9eegf6g.streamlit.app/

## Architecture

- **Backend API** (FastAPI) → deployed on Render with Docker
- **Frontend** (Streamlit) → deployed on Streamlit Community Cloud
- **Model** → XGBoost tuned regressor, trained on Belgian real estate data

## Project structure

```
immo-eliza-deployment/
├── api/
│   ├── model/                  # saved model + preprocessing artifacts
│   │   ├── xgboost_tuned.joblib
│   │   └── preprocessors.joblib
│   ├── predict.py              # standalone prediction pipeline
│   ├── app.py                  # FastAPI application
│   ├── Dockerfile
│   └── requirements.txt
├── streamlit/
│   ├── streamlit_app.py        # Streamlit frontend
│   └── requirements.txt
├── .streamlit/
│   └── config.toml             # theme config
└── README.md
```

## API endpoints

Base URL: `https://immo-eliza-deployment-backend.onrender.com`

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

**API:**
```bash
cd api
pip install -r requirements.txt
uvicorn app:app --reload
```
Then check `http://localhost:8000/docs` for the interactive API documentation.

**Streamlit:**
```bash
cd streamlit
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Run with Docker (API only)

```bash
cd api
docker build -t immo-eliza-api .
docker run -p 8000:8000 immo-eliza-api
```

## Deploy

**API on Render:**
1. Push this repo to GitHub
2. Go to render.com → New Web Service
3. Connect your GitHub repo
4. Set Root Directory to `api`
5. Render auto-detects the Dockerfile

**Streamlit on Streamlit Community Cloud:**
1. Go to share.streamlit.io
2. Connect your GitHub repo
3. Set main file path to `streamlit/streamlit_app.py`
4. Deploy Auto-redeploys on push to main