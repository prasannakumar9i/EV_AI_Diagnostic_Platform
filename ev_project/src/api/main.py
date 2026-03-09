"""
api/main.py
Production-grade FastAPI REST API for EV AI Diagnostics.
"""
import time
import logging
import os
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

try:
    from prometheus_client import (Counter, Histogram, Gauge,
                                    generate_latest, CONTENT_TYPE_LATEST)
    from fastapi.responses import Response as FastResponse
    PROM_OK = True
except ImportError:
    PROM_OK = False

logger = logging.getLogger(__name__)

# ── Prometheus metrics ────────────────────────────────────────────────────────
if PROM_OK:
    REQ_COUNTER  = Counter("ev_api_requests_total", "Total requests", ["endpoint"])
    REQ_LATENCY  = Histogram("ev_api_latency_seconds", "Request latency", ["endpoint"])
    ACTIVE_USERS = Gauge("ev_active_users", "Active sessions")
    FLEET_RISK   = Gauge("ev_high_risk_vehicles", "High-risk vehicles in fleet")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "EV AI Diagnostic Platform API",
    description = "AI-powered EV diagnostic platform — Resume Project v2.0",
    version     = "2.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

# ── Simple demo auth ──────────────────────────────────────────────────────────
security = HTTPBearer(auto_error=False)
DEMO_TOKEN = "ev-demo-token-2024"   # In production: use JWT

def get_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    if creds and creds.credentials == DEMO_TOKEN:
        return {"user": "technician", "role": "admin"}
    return {"user": "anonymous", "role": "viewer"}


# ── Pydantic models ───────────────────────────────────────────────────────────
class DiagRequest(BaseModel):
    vehicle_id:   str                 = Field(...,  example="EV-001")
    brand:        str                 = Field("Unknown", example="Tesla")
    model:        str                 = Field("Unknown", example="Model 3")
    year:         int                 = Field(2023, ge=2010, le=2030)
    dtc_codes:    List[str]           = Field([],   example=["P0A0F", "P0C6B"])
    soc:          float               = Field(0.0,  ge=0, le=100)
    battery_temp: float               = Field(0.0,  ge=-40, le=120)
    motor_temp:   float               = Field(0.0,  ge=-40, le=180)
    question:     Optional[str]       = Field(None, example="Why is my battery overheating?")


class DiagResponse(BaseModel):
    vehicle_id:      str
    severity:        str
    safe_to_drive:   bool
    dtc_analysis:    dict
    recommendations: List[str]
    rag_answer:      Optional[str]
    processing_ms:   int


class VehicleFleetItem(BaseModel):
    vehicle_id:   str
    brand:        str
    soh_pct:      float
    soc_pct:      float
    risk_level:   str
    fault_count:  int


# ── DTC mini-database ─────────────────────────────────────────────────────────
DTC_DB = {
    "P0A0F": ("Battery Pack Overvoltage",       "HIGH",     False, "Check charger and BMS firmware"),
    "P0A1B": ("Battery Temperature Sensor",     "MEDIUM",   True,  "Inspect sensor wiring"),
    "P0A1D": ("Cell Voltage Imbalance",         "HIGH",     False, "Run full cell-balancing cycle"),
    "P0A80": ("Battery Replacement Required",   "CRITICAL", False, "Schedule battery replacement"),
    "P0AFA": ("Battery SOH Below Threshold",    "HIGH",     True,  "Plan battery service within 3 months"),
    "P0C6B": ("Battery Cooling Fault",          "HIGH",     False, "Check coolant pump and level"),
    "P0B23": ("Motor Temperature Too High",     "HIGH",     False, "Allow cooling; check circuit"),
    "P0B40": ("Inverter Overcurrent",           "CRITICAL", False, "Replace inverter assembly"),
    "P0D30": ("Charging Port Fault",            "MEDIUM",   True,  "Inspect port pins and latch"),
    "U0100": ("CAN Bus Communication Lost",     "MEDIUM",   False, "Check CAN wiring and termination"),
}


# ── Request timing middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start    = time.time()
    response = await call_next(request)
    ms       = int((time.time() - start) * 1000)
    response.headers["X-Process-Time-Ms"] = str(ms)
    if PROM_OK:
        REQ_COUNTER.labels(request.url.path).inc()
        REQ_LATENCY.labels(request.url.path).observe(time.time() - start)
    return response


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/", tags=["info"])
def root():
    return {
        "api":     "EV AI Diagnostic Platform",
        "version": "2.0.0",
        "docs":    "/docs",
        "status":  "running",
    }


@app.get("/health", tags=["info"])
def health():
    return {
        "status": "healthy",
        "uptime": time.time(),
        "version": "2.0.0",
    }


@app.post("/api/v2/diagnose", response_model=DiagResponse, tags=["diagnostics"])
def diagnose(req: DiagRequest, user=Depends(get_user)):
    """
    Full diagnostic scan for a vehicle.
    - Analyses all DTC codes
    - Evaluates battery and motor temperatures
    - Returns severity, safety status, and recommendations
    """
    t0     = time.time()
    sev_ord = {"OK": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    max_sev = "OK"
    safe    = True
    dtc_out = {}
    actions = []

    for code in req.dtc_codes:
        if code in DTC_DB:
            desc, sev, drive_ok, action = DTC_DB[code]
            dtc_out[code] = {"description": desc, "severity": sev, "action": action}
            actions.append(action)
            if not drive_ok:
                safe = False
            if sev_ord.get(sev, 0) > sev_ord.get(max_sev, 0):
                max_sev = sev
        else:
            dtc_out[code] = {"description": "Unknown DTC", "severity": "UNKNOWN",
                             "action": "Consult official service manual"}

    if req.battery_temp > 55:
        actions.append("CRITICAL: Stop driving — battery overtemperature")
        safe    = False
        max_sev = "CRITICAL"
    elif req.battery_temp > 45:
        actions.append("Battery temp elevated — stop fast charging")
        if sev_ord.get(max_sev, 0) < sev_ord["HIGH"]:
            max_sev = "HIGH"

    if req.motor_temp > 100:
        actions.append("Motor overtemperature — reduce load")

    if req.soc < 10:
        actions.append("Battery critically low — charge immediately")

    if not actions:
        actions = ["No immediate action required — continue monitoring"]

    ms = int((time.time() - t0) * 1000)

    if PROM_OK and max_sev in ("HIGH", "CRITICAL"):
        FLEET_RISK.inc()

    return DiagResponse(
        vehicle_id      = req.vehicle_id,
        severity        = max_sev,
        safe_to_drive   = safe,
        dtc_analysis    = dtc_out,
        recommendations = list(dict.fromkeys(actions)),   # deduplicate
        rag_answer      = req.question and f"[RAG] Query received: '{req.question}'. Connect RAG pipeline for full answer.",
        processing_ms   = ms,
    )


@app.get("/api/v2/fleet/summary", tags=["fleet"])
def fleet_summary(user=Depends(get_user)):
    """Fleet-level KPI summary."""
    import random
    random.seed(42)
    return {
        "total_vehicles":    50,
        "high_risk":         7,
        "needs_service":     12,
        "avg_soh_pct":       86.3,
        "avg_soc_pct":       64.1,
        "total_faults_today":18,
        "critical_alerts":   2,
    }


@app.get("/api/v2/fleet/vehicles", response_model=List[VehicleFleetItem], tags=["fleet"])
def fleet_vehicles(limit: int = 20, user=Depends(get_user)):
    """Return a list of fleet vehicles with health metrics."""
    import random
    random.seed(99)
    brands = ["Tesla", "Nissan", "Hyundai", "BMW", "Kia"]
    risks  = ["LOW", "LOW", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    return [
        VehicleFleetItem(
            vehicle_id  = f"EV-{i:03d}",
            brand       = random.choice(brands),
            soh_pct     = round(random.uniform(55, 100), 1),
            soc_pct     = round(random.uniform(10, 100), 1),
            risk_level  = random.choice(risks),
            fault_count = random.randint(0, 8),
        )
        for i in range(min(limit, 50))
    ]


@app.get("/api/v2/dtc/{code}", tags=["diagnostics"])
def lookup_dtc(code: str):
    """Look up a single DTC code."""
    code = code.upper()
    if code in DTC_DB:
        desc, sev, safe, action = DTC_DB[code]
        return {"code": code, "description": desc, "severity": sev,
                "safe_to_drive": safe, "action": action}
    raise HTTPException(status_code=404, detail=f"DTC {code} not in local database")


if PROM_OK:
    @app.get("/metrics", tags=["monitoring"])
    def metrics():
        return FastResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ── Run directly ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
