from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from predict import load_model, load_preprocessors, predict


# median coordinates per province from the training data
# used as fallback when the user doesn't provide latitude/longitude
PROVINCE_COORDS = {
    "antwerp": (51.1815, 4.4973),
    "brabant-wallon": (50.6905, 4.4939),
    "brussels": (50.8428, 4.3516),
    "east-flanders": (51.0051, 3.8724),
    "hainaut": (50.4659, 4.0692),
    "liege": (50.6210, 5.5888),
    "limburg": (51.0147, 5.3721),
    "luxembourg": (50.0209, 5.5099),
    "namur": (50.3011, 4.8718),
    "vlaams-brabant": (50.8705, 4.4327),
    "west-flanders": (51.1141, 3.0848),
}


# pydantic model = defines what the API expects as input
# required fields: the ones that matter most for a good prediction
# optional fields: the model can handle missing values (imputer fills them)

class PropertyData(BaseModel):
    property_type: str = Field(description="apartment or house")
    province: str = Field(description="e.g. brussels, antwerp, liege")
    livable_surface: int = Field(description="living area in m2")
    bedroom_count: int = Field(description="number of bedrooms")

    property_state: Optional[str] = Field(default=None, description="e.g. Normal, New, To renovate")
    total_surface: Optional[int] = Field(default=None, description="total land area in m2")
    build_year: Optional[int] = Field(default=None, description="year the property was built")
    garage: Optional[int] = Field(default=0, description="1 if has garage, 0 if not")
    terrace: Optional[int] = Field(default=0, description="1 if has terrace, 0 if not")
    swimming_pool: Optional[int] = Field(default=0, description="1 if has pool, 0 if not")
    energy_consumption: Optional[float] = Field(default=None, description="energy consumption in kWh/m2/year")
    preschool_distance_m: Optional[float] = Field(default=None, description="distance to nearest preschool in meters")
    train_station_distance_m: Optional[float] = Field(default=None, description="distance to nearest train station in meters")
    supermarket_distance_m: Optional[float] = Field(default=None, description="distance to nearest supermarket in meters")
    nearest_city_distance_km: Optional[float] = Field(default=None, description="distance to nearest city in km")
    latitude: Optional[float] = Field(default=None, description="latitude coordinate")
    longitude: Optional[float] = Field(default=None, description="longitude coordinate")


class PredictionInput(BaseModel):
    data: PropertyData


class PredictionOutput(BaseModel):
    prediction: float
    status_code: int


# load model and preprocessors once at startup (not on every request)
model = load_model()
preprocessors = load_preprocessors()

app = FastAPI(
    title="Immo Eliza Price Prediction API",
    description="Predict Belgian real estate prices based on property features.",
    version="1.0.0",
)


# route 1: health check

@app.get("/")
def alive():
    """Check if the API is up and running."""
    return "alive"


# route 2: prediction

@app.post("/predict", response_model=PredictionOutput)
def predict_price(body: PredictionInput):
    """Receive property data, return a price prediction."""
    try:
        # convert pydantic model to dict with the exact feature names the model expects
        prop = body.data.model_dump()

        # map the clean API field name to the column name from the dataset
        prop["energy_consumption_kWh/m2/year"] = prop.pop("energy_consumption")

        # if no lat/lon provided, use the province center as fallback
        province = prop.get("province", "").lower()
        if prop["latitude"] is None and province in PROVINCE_COORDS:
            prop["latitude"] = PROVINCE_COORDS[province][0]
        if prop["longitude"] is None and province in PROVINCE_COORDS:
            prop["longitude"] = PROVINCE_COORDS[province][1]

        prediction = predict(model, preprocessors, prop)

        return PredictionOutput(
            prediction=round(prediction[0], 2),
            status_code=200,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
