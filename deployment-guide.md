# Deployment Cheatsheet — FastAPI, Streamlit, Render & Cloud Hosting

Everything you need to talk about deployment comfortably by the end of the week.
Written as a reference you can come back to anytime.

---

## Table of contents

1. [The big picture — what is deployment?](#1-the-big-picture--what-is-deployment)
2. [FastAPI — building APIs](#2-fastapi--building-apis)
3. [Streamlit — building frontends](#3-streamlit--building-frontends)
4. [Docker — packaging your app](#4-docker--packaging-your-app)
5. [Render — hosting your app](#5-render--hosting-your-app)
6. [Cloud hosting — the landscape](#6-cloud-hosting--the-landscape)
7. [Quick reference tables](#7-quick-reference-tables)

---

## 1. The big picture — what is deployment?

You wrote a model that predicts prices. Right now it only works on YOUR computer.
Deployment = making it available to anyone, anywhere, through the internet.

The stack looks like this:

```
[User in browser]
      |
      v
[Streamlit frontend]  <-- pretty interface (buttons, sliders, charts)
      |
      v
[FastAPI backend]     <-- receives data as JSON, returns predictions as JSON
      |
      v
[ML model]            <-- xgboost, random forest, etc.
```

- **FastAPI** = the backend. It's an API (Application Programming Interface).
  Other programs talk to it by sending HTTP requests with JSON data.
- **Streamlit** = the frontend. It's a web app that humans interact with.
  It sends requests to the FastAPI backend behind the scenes.
- **Docker** = a box that packages your code + dependencies so it runs the same everywhere.
- **Render** = a website that takes your Docker box and puts it on the internet.

---

## 2. FastAPI — building APIs

### what is it

FastAPI is a Python framework for creating web APIs.
An API receives requests (data in) and returns responses (data out), both as JSON.
It auto-generates interactive documentation at `/docs` where anyone can test your routes.

### install

```bash
pip install fastapi uvicorn
```

- `fastapi` = the framework (defines your routes, validates input)
- `uvicorn` = the server (actually runs your app and listens for requests)

### run

```bash
uvicorn app:app --reload
```

- `app:app` = "in the file app.py, find the variable called app"
- `--reload` = auto-restart when you save changes (dev only, not production)
- default port: 8000 → open http://localhost:8000
- docs page: http://localhost:8000/docs

### the minimal app

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "alive"}
```

That's it. This creates a GET route at `/` that returns JSON.

### anatomy of a route

```python
@app.get("/hello")          # 1. decorator = HTTP method + path
def say_hello():             # 2. function name (any name you want)
    return {"msg": "hello"}  # 3. return value → automatically converted to JSON
```

The decorator tells FastAPI: "when someone visits `/hello`, run this function."

### HTTP methods — the 4 you'll see

| Method | What it does | Example |
|--------|-------------|---------|
| GET | read/fetch data | get a list of users |
| POST | send data to create something | send property data, get a prediction |
| PUT | update existing data | update a user's email |
| DELETE | remove data | delete a user |

For ML APIs, you mainly use **GET** (health check) and **POST** (predictions).

```python
@app.get("/")           # GET route
@app.post("/predict")   # POST route
@app.put("/users/{id}") # PUT route (less common for ML)
@app.delete("/items")   # DELETE route (less common for ML)
```

### path parameters — values in the URL

```python
@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}
```

Visit `/users/42` → returns `{"user_id": 42}`.
The `{user_id}` in the path becomes a function parameter.
FastAPI converts it to `int` automatically and returns an error if it's not a number.

### query parameters — values after the ?

```python
@app.get("/search")
def search(city: str, min_price: int = 0):
    return {"city": city, "min_price": min_price}
```

Visit `/search?city=brussels&min_price=200000` → returns both values.
Parameters with a default value (`min_price=0`) are optional.

### request body — sending JSON with POST

This is the most important pattern for ML APIs.
You define a Pydantic model = a class that describes what the JSON should look like.

```python
from fastapi import FastAPI
from pydantic import BaseModel

class PropertyData(BaseModel):
    property_type: str        # required
    province: str             # required
    livable_surface: int      # required
    bedroom_count: int = 1    # optional, default 1

app = FastAPI()

@app.post("/predict")
def predict(data: PropertyData):
    # data.property_type, data.province, etc. are available here
    # FastAPI automatically validates the JSON against PropertyData
    return {"received": data.model_dump()}
```

When someone sends this JSON to POST /predict:
```json
{
    "property_type": "apartment",
    "province": "brussels",
    "livable_surface": 75
}
```

FastAPI:
1. checks all required fields are present (if not → 422 error automatically)
2. checks types match (if not → 422 error automatically)
3. fills in defaults for missing optional fields
4. passes it to your function as a `PropertyData` object

### pydantic — input validation made easy

Pydantic is the library FastAPI uses to validate input data.
You define a class that inherits from `BaseModel`:

```python
from pydantic import BaseModel, Field
from typing import Optional

class PropertyData(BaseModel):
    # required field with a description (shows up in /docs)
    property_type: str = Field(description="apartment or house")

    # optional field with a default value
    garage: Optional[int] = Field(default=0, description="1 if has garage")

    # optional field that defaults to None (missing data)
    build_year: Optional[int] = Field(default=None, description="year built")
```

Key types you'll use:
| Type | What it accepts |
|------|----------------|
| `str` | text |
| `int` | whole numbers |
| `float` | decimal numbers |
| `bool` | true/false |
| `Optional[str]` | text OR None |
| `list[int]` | list of numbers |

### returning responses

FastAPI auto-converts Python dicts/lists to JSON:

```python
@app.get("/")
def root():
    return "alive"                        # → "alive"

@app.get("/info")
def info():
    return {"name": "immo-api", "v": 1}   # → {"name":"immo-api","v":1}

@app.get("/items")
def items():
    return [1, 2, 3]                      # → [1, 2, 3]
```

You can also define an output model (like we did with PredictionOutput):
```python
class PredictionOutput(BaseModel):
    prediction: float
    status_code: int

@app.post("/predict", response_model=PredictionOutput)
def predict(data: PropertyData):
    price = 250000.0  # your model's prediction
    return PredictionOutput(prediction=price, status_code=200)
```

### error handling

```python
from fastapi import HTTPException

@app.post("/predict")
def predict(data: PropertyData):
    if data.livable_surface <= 0:
        raise HTTPException(status_code=400, detail="surface must be positive")
    # ... normal prediction logic
```

Common status codes:
| Code | Meaning |
|------|---------|
| 200 | OK — everything worked |
| 400 | Bad Request — the client sent wrong data |
| 404 | Not Found — that route doesn't exist |
| 422 | Validation Error — JSON doesn't match the Pydantic model |
| 500 | Server Error — something broke on your end |

### the /docs page

FastAPI generates this automatically from your code.
It reads your route decorators, Pydantic models, and Field descriptions.

Visit `http://localhost:8000/docs` after starting your app:
- you can see all your routes listed
- click on a route → click "Try it out" → fill in the JSON → click "Execute"
- it sends a real request and shows you the response
- this is how developers test your API without writing any code

### common imports cheatsheet

```python
from fastapi import FastAPI              # the app itself
from fastapi import HTTPException        # to return error responses
from pydantic import BaseModel           # to define input/output models
from pydantic import Field               # to add descriptions to fields
from typing import Optional              # for optional fields
```

### building a new API from scratch — the template

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

# step 1: define what data you expect
class InputData(BaseModel):
    name: str = Field(description="what this field is")
    value: float = Field(description="what this field is")
    optional_thing: Optional[str] = Field(default=None)

# step 2: define what you return
class OutputData(BaseModel):
    result: float
    status_code: int

# step 3: create the app
app = FastAPI(title="My API", version="1.0.0")

# step 4: health check route (GET /)
@app.get("/")
def alive():
    return "alive"

# step 5: your main route (POST /whatever)
@app.post("/process", response_model=OutputData)
def process(body: InputData):
    try:
        result = body.value * 2  # your logic here
        return OutputData(result=result, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 3. Streamlit — building frontends

### what is it

Streamlit is a Python library that turns a regular .py script into a web app.
No HTML, no CSS, no JavaScript. Just Python.

It's meant for data scientists who want to show off their work with
interactive dashboards, charts, and input forms.

### install and run

```bash
pip install streamlit
streamlit run app.py
```

Opens on http://localhost:8501. Every time you save your .py file, the app refreshes.

### the minimal app

```python
import streamlit as st

st.title("Hello World")
st.write("this is my first streamlit app")
```

That's it. `st.write()` can display text, dataframes, charts — it figures out what to do.

### display functions — showing things

```python
import streamlit as st
import pandas as pd

# text
st.title("Big Title")            # huge text
st.header("Section Header")      # medium text
st.subheader("Subsection")       # smaller text
st.write("any text or object")   # smart display (auto-detects type)
st.markdown("**bold** _italic_") # markdown formatted text
st.code("print('hello')")        # code block

# data
df = pd.DataFrame({"col1": [1,2], "col2": [3,4]})
st.dataframe(df)                 # interactive table (sortable, scrollable)
st.table(df)                     # static table
st.json({"key": "value"})        # formatted JSON display

# status messages
st.success("it worked!")         # green box
st.error("something broke")     # red box
st.warning("be careful")        # yellow box
st.info("fyi")                  # blue box
```

### input widgets — getting data from the user

```python
import streamlit as st

# text input
name = st.text_input("your name", value="Anonymous")

# number input
age = st.number_input("your age", min_value=0, max_value=120, value=25)

# slider
price = st.slider("max price", 0, 1000000, 250000)

# dropdown
city = st.selectbox("choose a city", ["brussels", "antwerp", "liege"])

# multi-select
features = st.multiselect("select features", ["garage", "terrace", "pool"])

# checkbox
show_data = st.checkbox("show raw data")

# button
if st.button("predict"):
    st.write("prediction goes here")
```

Every widget returns its current value. When the user changes it, the script re-runs.

### layout — organizing the page

```python
import streamlit as st

# sidebar (left panel)
st.sidebar.title("Settings")
option = st.sidebar.selectbox("model", ["xgboost", "random forest"])

# columns (side by side)
col1, col2 = st.columns(2)
col1.write("left side")
col2.write("right side")

# expander (collapsible section)
with st.expander("show details"):
    st.write("hidden content here")

# tabs
tab1, tab2 = st.tabs(["Charts", "Data"])
with tab1:
    st.write("chart goes here")
with tab2:
    st.write("table goes here")
```

### charts — built-in visualization

```python
import streamlit as st
import pandas as pd

df = pd.DataFrame({"x": [1,2,3,4], "y": [10,20,15,25]})

st.line_chart(df)     # line chart
st.bar_chart(df)      # bar chart
st.area_chart(df)     # area chart

# for maps (needs latitude/longitude columns)
st.map(df_with_lat_lon)

# you can also use matplotlib, plotly, seaborn etc.
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot([1,2,3], [4,5,6])
st.pyplot(fig)
```

### connecting streamlit to a FastAPI backend

This is the pattern for your project — the frontend calls your API:

```python
import streamlit as st
import requests

st.title("Immo Eliza Price Predictor")

# input form
property_type = st.selectbox("type", ["apartment", "house"])
province = st.selectbox("province", ["brussels", "antwerp", "liege"])
surface = st.number_input("living area (m2)", min_value=10, value=75)
bedrooms = st.number_input("bedrooms", min_value=0, value=2)

if st.button("predict price"):
    # send a POST request to your FastAPI backend
    response = requests.post(
        "https://your-api-on-render.com/predict",
        json={
            "data": {
                "property_type": property_type,
                "province": province,
                "livable_surface": surface,
                "bedroom_count": bedrooms,
            }
        }
    )

    if response.status_code == 200:
        result = response.json()
        st.success(f"predicted price: {result['prediction']} euros")
    else:
        st.error("something went wrong")
```

### deploying streamlit

1. push your streamlit app to GitHub
2. go to share.streamlit.io
3. connect your GitHub account
4. pick the repo and the .py file
5. click deploy — done

free hosting, auto-redeploys when you push to main.

### common imports cheatsheet

```python
import streamlit as st     # the framework itself
import requests            # to call your FastAPI backend
import pandas as pd        # to work with data
```

---

## 4. Docker — packaging your app

### what is it

Docker packages your app + all its dependencies into a "container".
Think of it as a lightweight virtual computer that has everything pre-installed.

Why? Because "it works on my machine" is not good enough.
Docker makes sure it works the same way on Render, on your colleague's laptop, everywhere.

### the Dockerfile — a recipe

A Dockerfile is a text file with instructions to build your container.
Read it top to bottom like a recipe:

```dockerfile
# start from a base image (a minimal linux with python pre-installed)
FROM python:3.11-slim

# set the working directory inside the container
WORKDIR /app

# copy requirements first (docker caches this step if requirements didn't change)
COPY requirements.txt .

# install python packages
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest of your code
COPY . .

# tell docker which port your app uses (documentation, not enforced)
EXPOSE 8000

# the command to run when the container starts
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### key Dockerfile commands

| Command | What it does |
|---------|-------------|
| `FROM image` | base image to start from (python:3.11-slim, node:18, etc.) |
| `WORKDIR /path` | set the working directory for following commands |
| `COPY src dest` | copy files from your machine into the container |
| `RUN command` | run a command during build (install packages, etc.) |
| `EXPOSE port` | document which port the app uses |
| `CMD ["cmd"]` | the command to run when the container starts |

### building and running (when you have Docker installed)

```bash
# build the image (run from the folder with the Dockerfile)
docker build -t my-api .

# run the container
docker run -p 8000:8000 my-api
```

- `-t my-api` = give the image a name
- `-p 8000:8000` = map port 8000 on your machine to port 8000 in the container
- after this, visit http://localhost:8000

you don't need Docker installed to deploy on Render — Render builds it for you.

---

## 5. Render — hosting your app

### what is it

Render is a cloud platform that takes your code from GitHub and deploys it.
Free tier available. Auto-redeploys every time you push to main.

### step by step deployment

1. **push your code to GitHub** (make sure the Dockerfile is in the repo)
2. **go to render.com** → sign up / log in
3. **click "New +" → "Web Service"**
4. **connect your GitHub** account and pick your repo
5. **configure:**
   - name: whatever you want (e.g. "immo-eliza-api")
   - region: EU (Frankfurt)
   - branch: main
   - root directory: `api` (if your Dockerfile is in the api/ folder)
   - runtime: Docker (Render auto-detects the Dockerfile)
   - plan: Free
6. **click "Create Web Service"**
7. **wait** — Render builds the Docker image and starts your app (takes a few minutes)
8. **grab your URL** — something like `https://immo-eliza-api.onrender.com`

### important things about the free tier

- **spin down after inactivity**: if nobody visits your API for 15 minutes,
  Render shuts it down. Next request takes ~30-60 seconds to "wake up".
  this is normal, don't worry about it.
- **512 MB RAM, 0.1 CPU**: enough for a small ML model (xgboost is fine)
- **auto-deploy on push**: every `git push` to main triggers a new build
- **logs**: you can see your app's logs in the Render dashboard (useful for debugging)

### testing your deployed API

Once deployed, test it with curl or Python:

```bash
# health check
curl https://your-app.onrender.com/

# prediction
curl -X POST https://your-app.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{"data":{"property_type":"apartment","province":"brussels","livable_surface":75,"bedroom_count":2}}'
```

Or in Python:
```python
import requests

response = requests.post(
    "https://your-app.onrender.com/predict",
    json={
        "data": {
            "property_type": "apartment",
            "province": "brussels",
            "livable_surface": 75,
            "bedroom_count": 2
        }
    }
)
print(response.json())
# {"prediction": 275738.45, "status_code": 200}
```

Or just open `https://your-app.onrender.com/docs` in your browser and use the interactive docs.

---

## 6. Cloud hosting — the landscape

The big picture of where apps can live:

```
Cloud Hosting
├── Easy & Free (what we use)
│   ├── Render        → APIs with Docker (our backend)
│   ├── Streamlit     → data apps (our frontend)
│   └── Gradio        → quick ML demos (alternative to Streamlit)
│
└── Enterprise (big companies, paid, complex)
    ├── AWS (Amazon)  → the biggest, most services, most complex
    ├── Azure (Microsoft) → popular in corporate environments
    └── GCP (Google)  → strong in AI/ML tools
```

### why do big companies use AWS/Azure/GCP instead of Render?

- they need to handle millions of users
- they need databases, storage, security, monitoring, etc.
- they have teams dedicated to managing infrastructure
- they need custom configurations that simple platforms can't offer

### why do we use Render?

- free tier is enough for our project
- deploys in 5 clicks (no terminal commands on a remote server)
- auto-deploys from GitHub
- no server management (no linux updates, no firewall config)

### what to remember for interviews

"I deployed my ML model as a REST API using FastAPI and Docker, hosted on Render.
The frontend is a Streamlit app that calls the API. For production at scale,
I'd consider AWS or Azure, but for a portfolio project Render is perfect
because it's free and auto-deploys from GitHub."

That's enough. You don't need to know AWS/Azure/GCP details yet.

---

## 7. Quick reference tables

### FastAPI — most used code patterns

| What | Code |
|------|------|
| create app | `app = FastAPI()` |
| GET route | `@app.get("/path")` |
| POST route | `@app.post("/path")` |
| path param | `@app.get("/users/{id}")` then `def f(id: int)` |
| query param | `def f(city: str, limit: int = 10)` |
| request body | define a `BaseModel` class, use as param type |
| return JSON | `return {"key": "value"}` |
| raise error | `raise HTTPException(status_code=400, detail="msg")` |
| run server | `uvicorn app:app --reload` |
| see docs | visit `/docs` in browser |

### Streamlit — most used functions

| What | Code |
|------|------|
| text | `st.title()`, `st.header()`, `st.write()` |
| input | `st.text_input()`, `st.number_input()`, `st.slider()` |
| select | `st.selectbox()`, `st.multiselect()` |
| toggle | `st.checkbox()`, `st.button()` |
| layout | `st.sidebar`, `st.columns()`, `st.tabs()` |
| charts | `st.line_chart()`, `st.bar_chart()`, `st.map()` |
| status | `st.success()`, `st.error()`, `st.warning()` |
| data | `st.dataframe()`, `st.table()`, `st.json()` |
| run | `streamlit run file.py` (port 8501) |
| deploy | share.streamlit.io → connect GitHub |

### Docker — the essentials

| What | Code |
|------|------|
| base image | `FROM python:3.11-slim` |
| work dir | `WORKDIR /app` |
| copy files | `COPY . .` |
| run command | `RUN pip install -r requirements.txt` |
| start command | `CMD ["uvicorn", "app:app", "--host", "0.0.0.0"]` |
| build image | `docker build -t name .` |
| run container | `docker run -p 8000:8000 name` |

### Render — deployment checklist

| Step | Action |
|------|--------|
| 1 | push code to GitHub |
| 2 | render.com → New → Web Service |
| 3 | connect GitHub repo |
| 4 | set root directory (if Dockerfile not at root) |
| 5 | pick Docker runtime, EU region, Free plan |
| 6 | click Create → wait for build |
| 7 | grab URL, test with /docs |

---

## Glossary

| Term | Plain English |
|------|--------------|
| **API** | a program that receives requests and sends responses (like a waiter taking orders) |
| **REST** | a style of API that uses HTTP methods (GET, POST, etc.) and URLs |
| **endpoint/route** | a specific URL path in your API (e.g. `/predict`) |
| **JSON** | the data format APIs use — looks like Python dicts: `{"key": "value"}` |
| **HTTP request** | a message sent to an API (contains method, URL, and optionally data) |
| **HTTP response** | the answer from the API (contains status code and data) |
| **status code** | a number that tells you if the request worked (200=OK, 400=bad input, 500=server broke) |
| **Pydantic** | library that validates data — you define a class, it checks the input matches |
| **uvicorn** | the server that runs FastAPI apps (like a waiter that actually serves the food) |
| **Docker image** | a snapshot of your app + everything it needs (like a recipe) |
| **Docker container** | a running instance of an image (like the actual dish made from the recipe) |
| **Dockerfile** | the instructions to build an image |
| **deployment** | putting your app on the internet so others can use it |
| **free tier** | the free plan on Render — limited resources but enough for projects |
