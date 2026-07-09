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

st.set_page_config(page_title="Immo Eliza", layout="centered")

# custom CSS injected into the page
st.markdown("""
<style>
    /* teal gradient banner behind the title */
    .block-container > div:first-child {
        padding-top: 0;
    }
    .title-banner {
        background: linear-gradient(135deg, #2A9D8F, #264653);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .title-banner h1 {
        color: white;
        margin: 0;
    }
    .title-banner p {
        color: #d4e4e1;
        margin: 0.5rem 0 0 0;
    }

    /* colored box around the predicted price */
    .result-box {
        background: #e8f5f3;
        border-left: 4px solid #2A9D8F;
        padding: 1rem 1.5rem;
        border-radius: 5px;
        margin-top: 1rem;
    }
    .result-box .price {
        font-size: 2rem;
        font-weight: bold;
        color: #264653;
    }
</style>
""", unsafe_allow_html=True)

# title banner with custom styling
st.markdown("""
<div class="title-banner">
    <h1>Immo Eliza Price Predictor</h1>
    <p>Get an estimated price for a Belgian property based on its features.</p>
</div>
""", unsafe_allow_html=True)


# sidebar: required fields

st.sidebar.header("Property Info")

property_type = st.sidebar.selectbox("Property type", ["apartment", "house"], help="Apartment or house")
province = st.sidebar.selectbox("Province", PROVINCES)
livable_surface = st.sidebar.number_input("Living area (m²)", min_value=10, max_value=2000, value=75)
bedroom_count = st.sidebar.number_input("Bedrooms", min_value=0, max_value=20, value=2)


# main area: optional fields in expandable sections

st.subheader("Optional details")
st.write("Fill in what you know, leave the rest as is. The model handles missing values.")

# split optional fields into two columns
col1, col2 = st.columns(2)

with col1:
    property_state = st.selectbox("Property state", ["Unknown"] + PROPERTY_STATES, help="New, normal condition, needs renovation, or needs full restoration")
    total_surface = st.number_input("Total surface (m²)", min_value=0, max_value=50000, value=0)
    build_year = st.number_input("Build year", min_value=0, max_value=2026, value=0)
    garage = st.checkbox("Garage")
    terrace = st.checkbox("Terrace")
    swimming_pool = st.checkbox("Swimming pool")

with col2:
    energy_consumption = st.number_input("Energy consumption (kWh/m²/year)", min_value=0.0, max_value=1000.0, value=0.0)
    latitude = st.number_input("Latitude", min_value=0.0, max_value=51.6, value=0.0)
    longitude = st.number_input("Longitude", min_value=0.0, max_value=6.5, value=0.0)
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
    if latitude > 0:
        payload["latitude"] = latitude
    if longitude > 0:
        payload["longitude"] = longitude
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

    with st.spinner("Asking the API... (first request might take ~50s if the server is waking up from his sleep ! You should not see this message in your next few request :) )"):
        try:
            response = requests.post(f"{API_URL}/predict", json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                price = result["prediction"]

                # short version: 221K, 99K, etc.
                short_price = f"{int(price / 1000)}K"

                st.markdown(f"""
<div class="result-box">
    <p style="margin:0; color:#2A9D8F; font-weight:bold;">Estimated price</p>
    <p class="price">€{short_price}</p>
</div>
""", unsafe_allow_html=True)

                # toggle for full price
                if st.checkbox("Show full price"):
                    st.write(f"€{price:,.2f}")

                # show what was sent to the API
                with st.expander("See request details"):
                    st.json(payload)
            else:
                st.error(f"API returned an error (status {response.status_code})")
                st.write(response.text)

        except requests.exceptions.ConnectionError:
            st.error("Can't reach the API. The Render server might be sleeping, try again in 30 seconds.")
        except requests.exceptions.Timeout:
            st.error("Request timed out. The server is probably waking up, please try again.")
        except Exception as e:
            st.error(f"Something went wrong: {e}")


# about section at the bottom

st.divider()

with st.expander("About this project & API"):
    st.markdown(f"""
**Made by** [IkarusV](https://github.com/IkarusV)
| [Source code](https://github.com/IkarusV/immo-eliza-deployment/tree/main)

---

**Want to use the API directly?**

Base URL: `{API_URL}`

- `GET /` — health check
- `POST /predict` — get a price prediction

**Example request:**
```json
{{
  "data": {{
    "property_type": "apartment",
    "province": "brussels",
    "livable_surface": 75,
    "bedroom_count": 2,
    "terrace": 1
  }}
}}
```

**Example response:**
```json
{{
  "prediction": 275738.45,
  "status_code": 200
}}
```
""")
