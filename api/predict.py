import os
import joblib
import pandas as pd


# same feature lists as train.py, copied here so this file is standalone

NUMERIC_FEATURES = [
    "livable_surface",
    "bedroom_count",
    "total_surface",
    "build_year",
    "garage",
    "terrace",
    "swimming_pool",
    "energy_consumption_kWh/m2/year",
    "preschool_distance_m",
    "train_station_distance_m",
    "supermarket_distance_m",
    "nearest_city_distance_km",
    "latitude",
    "longitude",
]

CATEGORICAL_FEATURES = [
    "property_type",
    "province",
    "property_state",
]

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")


# load artifacts

def load_model(model_name="xgboost_tuned"):
    """Load a saved model from the model folder.

    Input:
        model_name: filename without extension (default: "xgboost_tuned").
    """
    path = os.path.join(MODEL_DIR, f"{model_name}.joblib")
    if not os.path.exists(path):
        raise FileNotFoundError(f"no model found at {path}")
    model = joblib.load(path)
    print(f"loaded model from {path}")
    return model


def load_preprocessors():
    """Load the saved preprocessing objects (imputer, scaler, encoder)."""
    path = os.path.join(MODEL_DIR, "preprocessors.joblib")
    if not os.path.exists(path):
        raise FileNotFoundError(f"no preprocessors found at {path}")
    preprocessors = joblib.load(path)
    print(f"loaded preprocessors from {path}")
    return preprocessors


# preprocess

def preprocess(df, preprocessors):
    """Apply the same transformations that were used during training.

    Input:
        df: pandas DataFrame with property features.
        preprocessors: dict of fitted preprocessing objects.
    Returns:
        X: transformed DataFrame ready for the model.
    """
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()

    # fill missing numbers with the median learned during training
    X[NUMERIC_FEATURES] = preprocessors["num_imputer"].transform(X[NUMERIC_FEATURES])

    # fill missing text with "unknown"
    X[CATEGORICAL_FEATURES] = preprocessors["cat_imputer"].transform(X[CATEGORICAL_FEATURES])

    # scale numbers using the same ranges as training
    X[NUMERIC_FEATURES] = preprocessors["scaler"].transform(X[NUMERIC_FEATURES])

    # turn text categories into 0/1 columns using the same encoding as training
    encoded_cats = preprocessors["encoder"].transform(X[CATEGORICAL_FEATURES])
    encoded_columns = preprocessors["encoder"].get_feature_names_out(CATEGORICAL_FEATURES)
    encoded_df = pd.DataFrame(encoded_cats, columns=encoded_columns, index=X.index)

    # swap old text columns for the new 0/1 columns
    X = X.drop(columns=CATEGORICAL_FEATURES)
    X = pd.concat([X, encoded_df], axis=1)

    return X


# predict

def predict(model, preprocessors, data):
    """Predict prices for one or more properties.

    Input:
        model: trained sklearn model.
        preprocessors: dict from load_preprocessors().
        data: dict or list of dicts with property info.
    Returns:
        list of predicted prices.
    """
    df = pd.DataFrame(data if isinstance(data, list) else [data])
    X = preprocess(df, preprocessors)
    predictions = model.predict(X)
    return predictions.tolist()
