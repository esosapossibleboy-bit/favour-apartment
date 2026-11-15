import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from apt_db import (
    book_inspection,
    cancel_visitor_booking,
    get_booked_slots,
    get_conn,
    host_checkin_visitor,
    host_list_inspections,
    lookup_visitor_booking,
    verify_host_passcode,
)
from apt_ui import render_apartment_app

app = FastAPI(title="Favour Apartment — Secure Inspection Portal")
DB_PATH = "apartment_tours.db"
IP_HISTORY: dict[str, list[float]] = {}

def _check_rate_limit(ip: str, limit: int = 8, window: float = 60.0):
    now = time.time()
    recent = [t for t in IP_HISTORY.get(ip, []) if now - t < window]
    if len(recent) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests. Please wait 1 minute.")
    recent.append(now)
    IP_HISTORY[ip] = recent

class BookingReq(BaseModel):
    full_name: str = Field(min_length=4, max_length=80)
    email: str = Field(min_length=5, max_length=100)
    phone: str = Field(min_length=10, max_length=20)
    visitor_state: str = Field(min_length=3, max_length=30)
    visitor_address: str = Field(min_length=6, max_length=160)
    id_type: str = Field(min_length=4, max_length=40)
    guests: int = Field(ge=1, le=2)
    visit_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    visit_time: str = Field(min_length=4, max_length=20)

class LookupReq(BaseModel):
    booking_code: str = Field(min_length=6, max_length=20)
    phone_or_email: str = Field(min_length=5, max_length=100)

class HostAuthReq(BaseModel):
    passcode: str = Field(min_length=4, max_length=32)

class HostCheckinReq(BaseModel):
    passcode: str = Field(min_length=4, max_length=32)
    booking_code: str = Field(min_length=6, max_length=20)

@app.get("/", response_class=HTMLResponse)
def home():
    return render_apartment_app()

@app.get("/api/slots")
def api_slots(visit_date: str):
    conn = get_conn(DB_PATH)
    booked = get_booked_slots(conn, visit_date)
    conn.close()
    return {"visit_date": visit_date, "booked": booked}

@app.post("/api/book")
def api_book(req: BookingReq, request: Request):
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip)
    conn = get_conn(DB_PATH)
    res = book_inspection(
        conn,
        req.full_name,
        req.email,
        req.phone,
        req.visitor_state,
        req.visitor_address,
        req.id_type,
        req.guests,
        req.visit_date,
        req.visit_time,
    )
    conn.close()
    if not res["ok"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.post("/api/pass")
def api_lookup_pass(req: LookupReq, request: Request):
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip, limit=12)
    conn = get_conn(DB_PATH)
    data = lookup_visitor_booking(conn, req.booking_code, req.phone_or_email)
    conn.close()
    if not data:
        raise HTTPException(status_code=404, detail="No matching inspection pass found")
    return data

@app.post("/api/cancel")
def api_cancel_pass(req: LookupReq):
    conn = get_conn(DB_PATH)
    ok = cancel_visitor_booking(conn, req.booking_code, req.phone_or_email)
    conn.close()
    if not ok:
        raise HTTPException(status_code=404, detail="Active booking not found")
    return {"ok": True}

@app.post("/api/host/inspections")
def api_host_list(req: HostAuthReq, request: Request):
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip, limit=6)
    if not verify_host_passcode(req.passcode):
        raise HTTPException(status_code=401, detail="Wrong Host Passcode")
    conn = get_conn(DB_PATH)
    rows = host_list_inspections(conn)
    conn.close()
    return {"inspections": rows}

@app.post("/api/host/checkin")
def api_host_checkin(req: HostCheckinReq):
    if not verify_host_passcode(req.passcode):
        raise HTTPException(status_code=401, detail="Wrong Host Passcode")
    conn = get_conn(DB_PATH)
    ok = host_checkin_visitor(conn, req.booking_code)
    conn.close()
    if not ok:
        raise HTTPException(status_code=404, detail="Booking not found or already checked in")
    return {"ok": True}
