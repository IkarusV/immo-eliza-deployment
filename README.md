# Immo Eliza - Deployment

Final part of the Immo Eliza project. After scraping, cleaning, analyzing and building ML models, this repo deploys the price prediction model as a REST API using FastAPI + Docker, hosted on Render.

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