import requests

#live Render URL
BASE_URL = "https://immo-eliza-deployment-backend.onrender.com"

def test_health_check():
    print("Testing health base url ")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}\n")
    except Exception as e:
        print(f"rip api might not be ON check render, server might be waking up from innactivity: {e}\n")

def test_prediction():
    print("Testing Price Prediction and post method")
    
    # Fake house data payload to post
    payload = {
        "data": {
            "property_type": "house",
            "province": "antwerp",
            "livable_surface": 150,
            "bedroom_count": 3,
            "property_state": "New",
            "total_surface": 300,
            "build_year": 2021,
            "garage": 1,
            "terrace": 1,
            "swimming_pool": 0,
            "energy_consumption": 110.5,
            "preschool_distance_m": 450.0,
            "train_station_distance_m": 1200.0,
            "supermarket_distance_m": 300.0,
            "nearest_city_distance_km": 2.5,
            "latitude": None,   # testing if my province fall back will work
            "longitude": None   # it should be replace by the coordinate of the province in the backend if not provided
        }
    }

    try:
        response = requests.post(f"{BASE_URL}/predict", json=payload)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Prediction Successful concgrats to me")
            print(f"Estimated Price: €{result.get('prediction'):,}")
        else:
            print("Prediction Failed :'( )")
            print(f"Error Details: {response.text}")
            
    except Exception as e:
        print(f"An error occurred during the request: {e}")

if __name__ == "__main__":
    test_health_check()
    test_prediction()