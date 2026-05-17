import json

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Base, User, Todo, Recommendation
from schemas import UserSignup, UserLogin, TaskCreate, TaskUpdate
from auth_utils import hash_password, verify_password
from auth_jwt import create_token
from auth_dependency import get_current_user

from soil import get_soil_data
from weather_service import get_weather

import pandas as pd
import joblib

app = FastAPI()

Base.metadata.create_all(bind=engine)

# ── CORS ──────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB ────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── ML models ─────────────────────────────────
clf            = joblib.load("agripulse_classifier.pkl")
label_encoders = joblib.load("agripulse_label_encoders.pkl")
le_target      = joblib.load("agripulse_target_encoder.pkl")

# ── Unit conversion ───────────────────────────
# 1 hectare = 19.664 ropani (Nepal standard)
HA_TO_ROPANI = 19.664

# ── ICAR/FAO recommended NPK doses (kg/ha) ───
# Source: FAO Fertilizer and Plant Nutrition Bulletin 16 (2006)
NPK_DOSE = {
    "Wheat":     {"Sowing": (60, 60, 40),  "Vegetative": (60, 0, 0),   "Flowering": (0, 0, 0),  "Harvest": (0, 0, 0)},
    "Rice":      {"Sowing": (40, 30, 30),  "Vegetative": (40, 0, 0),   "Flowering": (20, 0, 0), "Harvest": (0, 0, 0)},
    "Maize":     {"Sowing": (60, 60, 40),  "Vegetative": (60, 0, 0),   "Flowering": (30, 0, 0), "Harvest": (0, 0, 0)},
    "Cotton":    {"Sowing": (60, 30, 30),  "Vegetative": (60, 0, 0),   "Flowering": (30, 0, 0), "Harvest": (0, 0, 0)},
    "Sugarcane": {"Sowing": (100, 60, 60), "Vegetative": (100, 0, 0),  "Flowering": (50, 0, 0), "Harvest": (0, 0, 0)},
    "Potato":    {"Sowing": (100, 60, 80), "Vegetative": (50, 0, 0),   "Flowering": (50, 0, 40),"Harvest": (0, 0, 0)},
    "Tomato":    {"Sowing": (60, 60, 60),  "Vegetative": (60, 0, 0),   "Flowering": (40, 0, 40),"Harvest": (0, 0, 0)},
}

# ── Fertilizer nutrient content (%) ──────────
# Source: Tandon (2004); FAO Bulletin 16
NUTRIENT_CONTENT = {
    "Urea":          {"N": 46,  "P": 0,   "K": 0},
    "DAP":           {"N": 18,  "P": 46,  "K": 0},
    "MOP":           {"N": 0,   "P": 0,   "K": 60},
    "SSP":           {"N": 0,   "P": 16,  "K": 0},
    "NPK":           {"N": 12,  "P": 32,  "K": 16},
    "Compost":       {"N": 1.5, "P": 0.8, "K": 1.0},
    "Zinc Sulphate": {"Zn": 21},
}

ZINC_DOSE    = {"Wheat": 25, "Rice": 25, "Maize": 25, "Cotton": 10, "Sugarcane": 10, "Potato": 10, "Tomato": 10}
COMPOST_DOSE = {"low": 5000, "medium": 3000, "high": 1500}


def calculate_dosage(fertilizer, crop, growth_stage, organic_carbon,
                     nitrogen, phosphorus, potassium):
    """
    Dosage (kg/ha) = (Recommended Nutrient Dose x 100) / Nutrient Content (%)
    Source: FAO Fertilizer and Plant Nutrition Bulletin 16 (2006)
    """
    N_rec, P_rec, K_rec = NPK_DOSE[crop][growth_stage]
    nc = NUTRIENT_CONTENT[fertilizer]

    if fertilizer == "Urea":
        if N_rec == 0:
            return 0.0, "No N application needed at this stage"
        dose = (N_rec * 100) / nc["N"]
        note = f"Urea dose for {N_rec} kg/ha N @ 46% N content"

    elif fertilizer == "DAP":
        if P_rec == 0:
            return 0.0, "No P application needed at this stage"
        dose = (P_rec * 100) / nc["P"]
        note = f"DAP dose for {P_rec} kg/ha P2O5 @ 46% P; supplies {round(dose * nc['N'] / 100, 1)} kg N as credit"

    elif fertilizer == "MOP":
        if K_rec == 0:
            return 0.0, "No K application needed at this stage"
        dose = (K_rec * 100) / nc["K"]
        note = f"MOP dose for {K_rec} kg/ha K2O @ 60% K2O content"

    elif fertilizer == "SSP":
        if P_rec == 0:
            return 0.0, "No P application needed at this stage"
        dose = (P_rec * 100) / nc["P"]
        note = f"SSP dose for {P_rec} kg/ha P2O5 @ 16% P2O5 content"

    elif fertilizer == "NPK":
        doses = []
        if N_rec > 0: doses.append((N_rec * 100) / nc["N"])
        if P_rec > 0: doses.append((P_rec * 100) / nc["P"])
        if K_rec > 0: doses.append((K_rec * 100) / nc["K"])
        if not doses:
            return 0.0, "No NPK application needed at this stage"
        dose = max(doses)
        note = "NPK 12:32:16 dose - limiting nutrient approach"

    elif fertilizer == "Compost":
        if organic_carbon < 0.5:
            level, dose = "low",    COMPOST_DOSE["low"]
        elif organic_carbon < 1.0:
            level, dose = "medium", COMPOST_DOSE["medium"]
        else:
            level, dose = "high",   COMPOST_DOSE["high"]
        note = f"Compost dose for {level} organic carbon ({organic_carbon:.2f}%) - soil deficit basis"

    elif fertilizer == "Zinc Sulphate":
        dose = ZINC_DOSE.get(crop, 10)
        note = f"Zinc Sulphate soil application @ 21% Zn for {crop}"

    else:
        dose, note = 0.0, "Unknown fertilizer"

    return round(dose, 1), note


# ── Request schema ────────────────────────────
class PredictRequest(BaseModel):
    lat: float
    lon: float
    crop_type: str
    crop_growth_stage: str
    season: str
    irrigation_type: str
    application_date: str   # YYYY-MM-DD — date user plans to apply fertilizer


# =========================
# AUTH
# =========================

@app.post("/signup")
def signup(data: UserSignup, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(
        name=data.name,
        email=data.email,
        password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    return {"message": "User created successfully"}


@app.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"id": user.id, "name": user.name})
    return {"token": token}


@app.get("/me")
def get_me(user=Depends(get_current_user)):
    return user


# =========================
# TASK ROUTES
# =========================

@app.post("/tasks")
def add_task(data: TaskCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = Todo(user_id=user["id"], text=data.text, status="to do")
    db.add(task)
    db.commit()
    return {"message": "Task added"}


@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db), user=Depends(get_current_user)):
    tasks = db.query(Todo).filter(Todo.user_id == user["id"]).all()
    return [{"id": t.id, "text": t.text, "status": t.status} for t in tasks]


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = db.query(Todo).filter(Todo.id == task_id, Todo.user_id == user["id"]).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Deleted"}


@app.put("/tasks/{task_id}")
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = db.query(Todo).filter(Todo.id == task_id, Todo.user_id == user["id"]).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = data.status
    db.commit()
    return {"message": "Updated"}


# =========================
# DATA & PREDICTION
# =========================

@app.get("/")
def root():
    return FileResponse("index.html")


@app.get("/data")
def get_data(lat: float, lon: float, crop: str, season: str, stage: str, irrigation: str):
    """Fetch soil + weather for a location. Used to preview field conditions."""
    soil_data = get_soil_data(lat, lon)
    if "error" in soil_data:
        return soil_data

    weather = get_weather(lat, lon)
    if "error" in weather:
        return weather

    return {
        **soil_data,
        **weather,
        "Crop_Type": crop,
        "Crop_Growth_Stage": stage,
        "Season": season,
        "Irrigation_Type": irrigation,
    }


@app.post("/predict")
def predict(
    data: PredictRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    1. Fetch soil from shapefile (nearest polygon fallback)
    2. Fetch weather from WeatherAPI (seasonal fallback if key invalid)
    3. Encode features and classify fertilizer with ML model
    4. Calculate dosage using agronomic formula (ICAR/FAO)
    5. Save recommendation to DB
    6. Return result
    """
    # 1. Soil
    soil = get_soil_data(data.lat, data.lon)
    if "error" in soil:
        raise HTTPException(status_code=400, detail=f"Soil error: {soil['error']}")

    # 2. Weather
    weather = get_weather(data.lat, data.lon, data.season, data.application_date)
    weather.pop("_fallback", None)

    # 2a. Rain alert check — if >20mm forecast in 48 hours, withhold recommendation
    rain_alert  = weather.pop("rain_alert", False)
    rainfall_48h = weather.pop("Rainfall_48h", 0.0)

    if rain_alert:
        return {
            "rain_alert"  : True,
            "rainfall_48h": rainfall_48h,
            "message"     : (
                f"Heavy rainfall of {rainfall_48h}mm is forecast in the next 48 hours. "
                "Applying fertilizer now risks nutrient washoff and water pollution. "
                "Please wait until rainfall subsides before applying."
            ),
            "weather"     : weather,
            "soil"        : soil,
        }

    # 3. Encode features
    try:
        encoded = {
            "Soil_Type"         : label_encoders["Soil_Type"].transform([soil["Soil_Type"]])[0],
            "Soil_pH"           : soil["Soil_pH"],
            "Organic_Carbon"    : soil["Organic_Carbon"],
            "Nitrogen_Level"    : soil["Nitrogen_Level"],
            "Phosphorus_Level"  : soil["Phosphorus_Level"],
            "Potassium_Level"   : soil["Potassium_Level"],
            "Temperature"       : weather["Temperature"],
            "Humidity"          : weather["Humidity"],
            "Rainfall"          : weather["Rainfall"],
            "Crop_Type"         : label_encoders["Crop_Type"].transform([data.crop_type])[0],
            "Crop_Growth_Stage" : label_encoders["Crop_Growth_Stage"].transform([data.crop_growth_stage])[0],
            "Season"            : label_encoders["Season"].transform([data.season])[0],
            "Irrigation_Type"   : label_encoders["Irrigation_Type"].transform([data.irrigation_type])[0],
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Encoding error: {str(e)}")

    # 4. Classify fertilizer
    fertilizer = le_target.inverse_transform(clf.predict(pd.DataFrame([encoded])))[0]

    # 5. Calculate dosage by formula
    dosage_ha, basis = calculate_dosage(
        fertilizer,
        data.crop_type,
        data.crop_growth_stage,
        soil["Organic_Carbon"],
        soil["Nitrogen_Level"],
        soil["Phosphorus_Level"],
        soil["Potassium_Level"],
    )
    dosage_ropani = round(dosage_ha / HA_TO_ROPANI, 2)

    # 6. Save to DB
    result_payload = {
        "fertilizer"       : fertilizer,
        "dosage_ropani"    : dosage_ropani,
        "dosage_ha"        : dosage_ha,
        "basis"            : basis,
        "rain_alert"       : False,
        "rainfall_48h"     : rainfall_48h,
        "application_date" : data.application_date,
        "crop_growth_stage": data.crop_growth_stage,
        "season"           : data.season,
        "irrigation_type"  : data.irrigation_type,
        "soil"             : soil,
        "weather"          : weather,
    }

    rec = Recommendation(
        user_id          = user["id"],
        crop             = data.crop_type,
        lat              = str(data.lat),
        lon              = str(data.lon),
        result           = json.dumps(result_payload),
        application_date = data.application_date,
    )
    db.add(rec)
    db.commit()

    return result_payload


@app.get("/recommendations")
def get_recommendations(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Returns all past recommendations for the logged-in user."""
    recs = db.query(Recommendation).filter(Recommendation.user_id == user["id"]).all()
    return [
        {
            "id"              : r.id,
            "crop"            : r.crop,
            "lat"             : r.lat,
            "lon"             : r.lon,
            "created_at"      : str(r.created_at),
            "application_date": r.application_date,
            **json.loads(r.result),
        }
        for r in recs
    ]