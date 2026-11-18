import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field
from apt_ai_cache import SLOT_CACHE, ask_tenant_ai
from apt_db import (
    book_inspection,
    cancel_visitor_booking,
    get_audit_logs,
    get_booked_slots,
    get_conn,
    host_checkin_visitor,
    host_list_inspections,
    log_audit,
    lookup_visitor_booking,
    verify_host_passcode,
)
from apt_notifications import build_appointment_pdf, dispatch_booking_alerts
from apt_ui import render_apartment_app

app = FastAPI(title="Favour Apartment Benin City — Secure Inspection Portal", docs_url=None, redoc_url=None)
DB_PATH = "apartment_tours.db"
IP_HISTORY: dict[str, list[float]] = {}

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'self'; form-action 'self';"
    return response

def _check_rate_limit(ip: str, bucket: str, limit: int = 8, window: float = 60.0):
    now = time.time()
    key = f"{bucket}:{ip}"
    recent = [t for t in IP_HISTORY.get(key, []) if now - t < window]
    if len(recent) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests. Please wait 1 minute.")
    recent.append(now)
    IP_HISTORY[key] = recent

class BookingReq(BaseModel):
    unit_name: str = Field(default="Unit 1 (1-Bed Self-Contain)", min_length=4, max_length=50)
    full_name: str = Field(min_length=4, max_length=80)
    email: str = Field(min_length=5, max_length=100)
    phone: str = Field(min_length=10, max_length=20)
    visitor_state: str = Field(min_length=3, max_length=30)
    visitor_address: str = Field(min_length=10, max_length=160)
    id_type: str = Field(pattern=r"^(NIN|BVN)$")
    id_number: str = Field(pattern=r"^\d{11}$")
    guests: int = Field(ge=1, le=2)
    visit_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    visit_time: str = Field(min_length=4, max_length=20)
    website_url: str = Field(default="", max_length=100)
    math_a: int = Field(default=2, ge=1, le=9)
    math_b: int = Field(default=3, ge=1, le=9)
    math_answer: int = Field(default=5, ge=2, le=18)

class LookupReq(BaseModel):
    booking_code: str = Field(min_length=6, max_length=20)
    phone_or_email: str = Field(min_length=5, max_length=100)

class HostAuthReq(BaseModel):
    passcode: str = Field(min_length=4, max_length=32)

class HostCheckinReq(BaseModel):
    passcode: str = Field(min_length=4, max_length=32)
    booking_code: str = Field(min_length=6, max_length=20)

class AskAIReq(BaseModel):
    question: str = Field(min_length=2, max_length=250)

@app.get("/", response_class=HTMLResponse)
def home():
    return render_apartment_app()

@app.get("/api/slots")
def api_slots(visit_date: str, unit_name: str = "Unit 1 (1-Bed Self-Contain)"):
    cache_key = f"{unit_name}:{visit_date.strip()}"
    cached = SLOT_CACHE.get(cache_key)
    if cached is not None:
        return {"visit_date": visit_date, "unit_name": unit_name, "booked": cached, "cached": True}

    conn = get_conn(DB_PATH)
    booked = get_booked_slots(conn, visit_date, unit_name)
    conn.close()
    SLOT_CACHE.set(cache_key, booked)
    return {"visit_date": visit_date, "unit_name": unit_name, "booked": booked, "cached": False}

@app.post("/api/book")
def api_book(req: BookingReq, request: Request):
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip, "book", limit=6)
    conn = get_conn(DB_PATH)
    res = book_inspection(
        conn,
        req.full_name,
        req.email,
        req.phone,
        req.visitor_state,
        req.visitor_address,
        req.id_type,
        req.id_number,
        req.guests,
        req.visit_date,
        req.visit_time,
        req.unit_name,
        req.website_url,
        req.math_a,
        req.math_b,
        req.math_answer,
    )
    if not res["ok"]:
        conn.close()
        raise HTTPException(status_code=400, detail=res["error"])

    SLOT_CACHE.invalidate(f"{req.unit_name}:{req.visit_date.strip()}")
    alert_res = dispatch_booking_alerts(res)
    log_audit(conn, f"Alerts for {res['booking_code']}: {alert_res['email_status']} | {alert_res['sms_status']}", "INFO")
    conn.close()
    res["alerts_dispatched"] = True
    res["email_status"] = alert_res["email_status"]
    res["sms_status"] = alert_res["sms_status"]
    return res

@app.post("/api/pass")
def api_lookup_pass(req: LookupReq, request: Request):
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip, "pass", limit=5)
    conn = get_conn(DB_PATH)
    data = lookup_visitor_booking(conn, req.booking_code, req.phone_or_email)
    conn.close()
    if not data:
        raise HTTPException(status_code=404, detail="No matching inspection pass found")
    return data

@app.post("/api/pass/pdf")
def api_download_pass_pdf(req: LookupReq, request: Request):
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip, "pdf", limit=8)
    conn = get_conn(DB_PATH)
    data = lookup_visitor_booking(conn, req.booking_code, req.phone_or_email)
    conn.close()
    if not data or data["status"] == "CANCELLED":
        raise HTTPException(status_code=404, detail="Active inspection pass not found")
    pdf_bytes = build_appointment_pdf(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{data["booking_code"]}_Pass.pdf"'},
    )

@app.post("/api/cancel")
def api_cancel_pass(req: LookupReq, request: Request):
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip, "cancel", limit=5)
    conn = get_conn(DB_PATH)
    ok = cancel_visitor_booking(conn, req.booking_code, req.phone_or_email)
    conn.close()
    if not ok:
        raise HTTPException(status_code=404, detail="Active booking not found")
    SLOT_CACHE.clear()
    return {"ok": True}

@app.post("/api/ask-ai")
def api_ask_ai(req: AskAIReq, request: Request):
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip, "ask_ai", limit=15)
    res = ask_tenant_ai(req.question)
    if res["blocked"]:
        conn = get_conn(DB_PATH)
        log_audit(conn, f"Blocked AI prompt injection attempt from {ip}", "ALERT")
        conn.close()
        raise HTTPException(status_code=400, detail=res["answer"])
    return res

@app.post("/api/host/inspections")
def api_host_list(req: HostAuthReq, request: Request):
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip, "host", limit=6)
    conn = get_conn(DB_PATH)
    ok, err_msg = verify_host_passcode(req.passcode)
    if not ok:
        log_audit(conn, f"Failed Host Passcode attempt from {ip}", "ALERT")
        conn.close()
        raise HTTPException(status_code=401, detail=err_msg)
    rows = host_list_inspections(conn)
    audits = get_audit_logs(conn)
    conn.close()
    return {"inspections": rows, "audit_logs": audits}

@app.post("/api/host/checkin")
def api_host_checkin(req: HostCheckinReq):
    ok, err_msg = verify_host_passcode(req.passcode)
    if not ok:
        raise HTTPException(status_code=401, detail=err_msg)
    conn = get_conn(DB_PATH)
    checked = host_checkin_visitor(conn, req.booking_code)
    conn.close()
    if not checked:
        raise HTTPException(status_code=404, detail="Booking not found or already checked in")
    return {"ok": True}
