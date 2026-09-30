from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from bus_state import buses
from bunching_detector import detect_bunching

from database import (
    initialize_database,
    save_bus_observation,
    save_bunching_event,
    get_metrics,
    create_run,
    CURRENT_RUN_ID,
    CONTROL_MODE
)


app = FastAPI(
    title="FedHold Bus Bunching System",
    description="Intelligent Bus Bunching Detection and Control System",
    version="1.0.0"
)


# ==========================================
# Database initialization
# ==========================================

initialize_database()


# ==========================================
# Create current experiment
# ==========================================

create_run(
    CURRENT_RUN_ID,
    f"FedHold {CONTROL_MODE} Experiment",
    CONTROL_MODE
)


active_bunching_pairs = set()


# ==========================================
# Data Models
# ==========================================

class BusData(BaseModel):
    bus_id: str
    position: float
    speed: float
    passengers: int


class BusUpdate(BaseModel):
    buses: list[BusData]


# ==========================================
# API Endpoints
# ==========================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "run_id": CURRENT_RUN_ID,
        "control_mode": CONTROL_MODE
    }


# ==========================================
# Bus Status
# ==========================================

@app.get("/bus-status")
def bus_status():

    return {
        "buses": buses
    }


# ==========================================
# Update Bus Data
# ==========================================

@app.post("/update-buses")
def update_buses(data: BusUpdate):

    buses.clear()

    for bus in data.buses:

        bus_data = bus.model_dump()

        buses.append(bus_data)

        save_bus_observation(bus_data)

    return {
        "status": "updated",
        "total_buses": len(buses)
    }


# ==========================================
# Bunching Detection
# ==========================================

@app.get("/detect-bunching")
def detect_bus_bunching():

    global active_bunching_pairs

    alerts = detect_bunching(buses)

    current_bunching_pairs = set()

    for alert in alerts:

        pair = (
            alert["bus_id"],
            alert["following_bus"]
        )

        current_bunching_pairs.add(pair)

        # Save only when a new bunching event begins
        if pair not in active_bunching_pairs:

            save_bunching_event(alert)

    active_bunching_pairs = current_bunching_pairs

    return {
        "total_buses": len(buses),
        "bunching_detected": len(alerts) > 0,
        "alerts": alerts
    }


# ==========================================
# Control Decisions
# ==========================================

@app.get("/control-decisions")
def control_decisions():

    alerts = detect_bunching(buses)

    decisions = []

    for alert in alerts:

        decisions.append({
            "bus_id": alert["bus_id"],
            "following_bus": alert["following_bus"],
            "severity": alert["severity"],
            "action": "HOLD",
            "hold_seconds": alert["hold_seconds"],
            "reason": (
                f"Headway is {alert['headway']} stops. "
                "Bus bunching detected."
            )
        })

    if not decisions:

        return {
            "status": "NORMAL",
            "message": "No bus bunching detected",
            "decisions": []
        }

    return {
        "status": "INTERVENTION_REQUIRED",
        "decisions": decisions
    }


# ==========================================
# Experiment Metrics
# ==========================================

@app.get("/metrics")
def metrics():

    return get_metrics()


# ==========================================
# Frontend
# ==========================================

app.mount(
    "/",
    StaticFiles(
        directory="../frontend",
        html=True
    ),
    name="frontend"
)