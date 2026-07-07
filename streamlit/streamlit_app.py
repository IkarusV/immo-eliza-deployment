import streamlit as st
import requests


# config

API_URL = "https://immo-eliza-deployment-backend.onrender.com"

PROVINCES = [
    "antwerp", "brabant-wallon", "brussels", "east-flanders",
    "hainaut", "liege", "limburg", "luxembourg",
    "namur", "vlaams-brabant", "west-flanders",
]

PROPERTY_STATES = ["New", "Normal", "To renovate", "To restore"]


# page setup

st.set_page_config(page_title="Immo Eliza", page_icon="", layout="centered")
st.title(" Immo Eliza Price Predictor")
st.write("Get an estimated price for a Belgian property based on its features.")


# sidebar: required fields

st.sidebar.header("Property Info")

property_type = st.sidebar.selectbox("Property type", ["apartment", "house"])
province = st.sidebar.selectbox("Province", PROVINCES)
livable_surface = st.sidebar.number_input("Living area (m²)", min_value=10, max_value=2000, value=75)
bedroom_count = st.sidebar.number_input("Bedrooms", min_value=0, max_value=20, value=2)


# main area: optional fields in expandable sections

st.subheader("Optional details")
st.write("Fill in what you know, leave the rest as is. The model handles missing values.")

# split optional fields into two columns
col1, col2 = st.columns(2)

with col1:
    property_state = st.selectbox("Property state", ["Unknown"] + PROPERTY_STATES)
    total_surface = st.number_input("Total surface (m²)", min_value=0, max_value=50000, value=0)
    build_year = st.number_input("Build year", min_value=1800, max_value=2026, value=0)
    garage = st.checkbox("Garage")
    terrace = st.checkbox("Terrace")
    swimming_pool = st.checkbox("Swimming pool")

with col2:
    energy_consumption = st.number_input("Energy consumption (kWh/m²/year)", min_value=0.0, max_value=1000.0, value=0.0)
    preschool_distance = st.number_input("Distance to preschool (m)", min_value=0.0, max_value=50000.0, value=0.0)
    train_station_distance = st.number_input("Distance to train station (m)", min_value=0.0, max_value=50000.0, value=0.0)
    supermarket_distance = st.number_input("Distance to supermarket (m)", min_value=0.0, max_value=50000.0, value=0.0)
    nearest_city_distance = st.number_input("Distance to nearest city (km)", min_value=0.0, max_value=200.0, value=0.0)


# build the payload (only send values that were actually filled in)

def build_payload():
    """Put together the JSON payload to send to the API."""
    payload = {
        "property_type": property_type,
        "province": province,
        "livable_surface": livable_surface,
        "bedroom_count": bedroom_count,
        "garage": int(garage),
        "terrace": int(terrace),
        "swimming_pool": int(swimming_pool),
    }

    # only add optional fields if the user actually filled them
    if property_state != "Unknown":
        payload["property_state"] = property_state
    if total_surface > 0:
        payload["total_surface"] = total_surface
    if build_year > 0:
        payload["build_year"] = build_year
    if energy_consumption > 0:
        payload["energy_consumption"] = energy_consumption
    if preschool_distance > 0:
        payload["preschool_distance_m"] = preschool_distance
    if train_station_distance > 0:
        payload["train_station_distance_m"] = train_station_distance
    if supermarket_distance > 0:
        payload["supermarket_distance_m"] = supermarket_distance
    if nearest_city_distance > 0:
        payload["nearest_city_distance_km"] = nearest_city_distance

    return {"data": payload}


# predict button

st.divider()

if st.button("Predict Price", type="primary", use_container_width=True):
    payload = build_payload()

    with st.spinner("Asking the API... (first request might take ~30s if the server is waking up)"):
        try:
            response = requests.post(f"{API_URL}/predict", json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                price = result["prediction"]
                st.success(f"Estimated price: **€{price:,.2f}**")

                # show what was sent to the API
                with st.expander("See request details"):
                    st.json(payload)
            else:
                st.error(f"API returned an error (status {response.status_code})")
                st.write(response.text)

        except requests.exceptions.ConnectionError:
            st.error("Can't reach the API. The Render server might be sleeping, try again in 30 seconds.")
        except requests.exceptions.Timeout:
            st.error("Request timed out. The server is probably waking up, try again.")
        except Exception as e:
            st.error(f"Something went wrong: {e}")
