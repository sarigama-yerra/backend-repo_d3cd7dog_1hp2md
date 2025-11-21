import os
import random
from datetime import datetime
from typing import List, Literal
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RackTelemetry(BaseModel):
    rack_id: int
    temperature_c: float
    humidity_pct: float
    light_lux: int
    moisture_pct: float
    growth_status: Literal["Early", "Mid", "Harvest"]


class TelemetryResponse(BaseModel):
    timestamp: str
    racks: List[RackTelemetry]


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


@app.get("/api/telemetry", response_model=TelemetryResponse)
def get_telemetry(racks: int = Query(6, ge=1, le=24)):
    """Generate realistic-looking live telemetry for the farm racks."""
    racks_data: List[RackTelemetry] = []
    now = datetime.utcnow()
    # Base environment ranges for a night scene
    base_temp = random.uniform(18.0, 22.0)
    base_humidity = random.uniform(55.0, 75.0)
    base_lux = random.randint(12000, 18000)  # LED grow lights intensity
    for i in range(racks):
        # Slight variations per rack
        t = round(base_temp + random.uniform(-0.8, 0.8), 1)
        h = round(base_humidity + random.uniform(-3.5, 3.5), 1)
        lux = max(8000, int(base_lux + random.randint(-1500, 1500)))
        moisture = round(random.uniform(55.0, 85.0), 1)
        phase_roll = random.random()
        if phase_roll < 0.33:
            phase = "Early"
        elif phase_roll < 0.78:
            phase = "Mid"
        else:
            phase = "Harvest"
        racks_data.append(RackTelemetry(
            rack_id=i + 1,
            temperature_c=t,
            humidity_pct=h,
            light_lux=lux,
            moisture_pct=moisture,
            growth_status=phase
        ))
    return TelemetryResponse(
        timestamp=now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        racks=racks_data
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
