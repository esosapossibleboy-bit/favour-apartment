import re
import secrets
from datetime import datetime
from apt_pg_adapter import open_apartment_db
from apt_security import (
    APARTMENT_LISTING,
    APARTMENT_UNITS,
    NIGERIAN_STATES,
    hash_gov_id,
    normalize_ng_phone,
    sanitize_text,
    validate_gov_id,
    validate_real_email,
    validate_visit_window,
    verify_host_passcode,
    verify_human_challenge,
)

def get_conn(db_path: str = "apartment_tours.db"):
    conn = open_apartment_db(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_code TEXT UNIQUE NOT NULL,
            gate_pin TEXT NOT NULL,
            unit_name TEXT NOT NULL DEFAULT 'Unit 1 (1-Bed Self-Contain)',
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            visitor_state TEXT NOT NULL,
            visitor_address TEXT NOT NULL,
            id_type TEXT NOT NULL,
            id_hash TEXT NOT NULL DEFAULT '',
            id_masked TEXT NOT NULL DEFAULT '',
            guests INTEGER NOT NULL DEFAULT 1,
            visit_date TEXT NOT NULL,
            visit_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'CONFIRMED',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS security_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            severity TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_slot ON inspections(unit_name, visit_date, visit_time, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_guest ON inspections(phone, email, id_hash)")
    conn.commit()
    return conn

def log_audit(conn, event: str, severity: str = "INFO"):
    ts = datetime.now().strftime("%d %b %Y, %H:%M")
    conn.execute("INSERT INTO security_audit (event, severity, created_at) VALUES (?, ?, ?)", (event, severity, ts))
    conn.commit()

def get_audit_logs(conn) -> list[dict]:
    cur = conn.cursor()
    cur.execute("SELECT event, severity, created_at FROM security_audit ORDER BY id DESC LIMIT 15")
    return [{"event": e, "severity": s, "time": t} for e, s, t in cur.fetchall()]

def book_inspection(
    conn,
    full_name: str,
    email: str,
    phone: str,
    visitor_state: str,
    visitor_address: str,
    id_type: str,
    id_number: str,
    guests: int,
    visit_date: str,
    visit_time: str,
    unit_name: str = "Unit 1 (1-Bed Self-Contain)",
    honeypot: str = "",
    math_a: int = 2,
    math_b: int = 3,
    math_answer: int = 5,
) -> dict:
    if not verify_human_challenge(honeypot, math_a, math_b, math_answer):
        log_audit(conn, "Blocked automated bot or wrong security math answer", "ALERT")
        return {"ok": False, "error": "Human verification failed. Please solve the security math question."}

    window_err = validate_visit_window(visit_date, visit_time)
    if window_err:
        return {"ok": False, "error": window_err}

    clean_name = sanitize_text(full_name)
    parts = [p for p in clean_name.split() if len(p) >= 2 and p.isalpha()]
    if len(parts) < 2:
        return {"ok": False, "error": "Enter your real First Name and Last Name (letters only)"}

    clean_email = validate_real_email(email)
    if not clean_email:
        return {"ok": False, "error": "Enter a real, active email address"}

    clean_phone = normalize_ng_phone(phone)
    if not clean_phone:
        return {"ok": False, "error": "Enter a real Nigerian phone number (e.g. 08031234567)"}

    if visitor_state not in NIGERIAN_STATES:
        return {"ok": False, "error": "Select your Nigerian state of residence"}

    clean_addr = sanitize_text(visitor_address)
    if len(clean_addr) < 10 or not re.search(r"\d", clean_addr) or not re.search(r"[A-Za-z]{3,}", clean_addr):
        return {"ok": False, "error": "Enter your real street address including house number and street name"}

    clean_id = validate_gov_id(id_type, id_number)
    if not clean_id:
        return {"ok": False, "error": f"Enter a valid 11-digit {id_type} number"}

    if unit_name not in APARTMENT_UNITS:
        return {"ok": False, "error": "Select Unit 1, Unit 2, or Unit 3"}

    if guests < 1 or guests > 2:
        return {"ok": False, "error": "Maximum of 2 visitors allowed per inspection"}

    id_hash = hash_gov_id(id_type, clean_id)
    id_masked = f"{id_type}: *******{clean_id[-4:]}"

    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM inspections WHERE (phone = ? OR email = ? OR id_hash = ?) AND status = 'CONFIRMED'",
        (clean_phone, clean_email, id_hash),
    )
    if cur.fetchone():
        return {"ok": False, "error": "You already have an active booking. Cancel it first before booking again."}

    cur.execute(
        "SELECT id FROM inspections WHERE unit_name = ? AND visit_date = ? AND visit_time = ? AND status = 'CONFIRMED'",
        (unit_name, visit_date.strip(), visit_time.strip()),
    )
    if cur.fetchone():
        return {"ok": False, "error": f"{unit_name} on {visit_date} at {visit_time} is already booked."}

    code = "FAV-" + secrets.token_hex(3).upper()
    gate_pin = str(1000 + secrets.randbelow(9000))
    ts = datetime.now().strftime("%d %b %Y, %H:%M")

    cur.execute(
        """INSERT INTO inspections
           (booking_code, gate_pin, unit_name, full_name, email, phone, visitor_state, visitor_address, id_type, id_hash, id_masked, guests, visit_date, visit_time, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?)""",
        (code, gate_pin, unit_name, clean_name, clean_email, clean_phone, visitor_state, clean_addr, id_type, id_hash, id_masked, guests, visit_date.strip(), visit_time.strip(), ts),
    )
    conn.commit()
    log_audit(conn, f"Booking {code} confirmed for {clean_name} ({id_masked})", "OK")
    return {
        "ok": True,
        "booking_code": code,
        "gate_pin": gate_pin,
        "unit_name": unit_name,
        "full_name": clean_name,
        "email": clean_email,
        "phone": clean_phone,
        "id_type": id_masked,
        "guests": guests,
        "visit_date": visit_date.strip(),
        "visit_time": visit_time.strip(),
        "exact_address": APARTMENT_LISTING["exact_address"],
        "host_phone": APARTMENT_LISTING["host_phone"],
    }

def lookup_visitor_booking(conn, booking_code: str, phone_or_email: str) -> dict | None:
    ident = phone_or_email.strip().lower()
    norm_phone = normalize_ng_phone(ident) or ident
    cur = conn.cursor()
    cur.execute(
        """SELECT booking_code, gate_pin, unit_name, full_name, email, phone, visitor_state, visitor_address, id_masked, guests, visit_date, visit_time, status
           FROM inspections WHERE UPPER(booking_code) = ? AND (phone = ? OR LOWER(email) = ?)""",
        (booking_code.strip().upper(), norm_phone, ident),
    )
    row = cur.fetchone()
    if not row:
        return None
    cols = ["booking_code", "gate_pin", "unit_name", "full_name", "email", "phone", "visitor_state", "visitor_address", "id_type", "guests", "visit_date", "visit_time", "status"]
    data = dict(zip(cols, row))
    data["exact_address"] = APARTMENT_LISTING["exact_address"] if data["status"] in ("CONFIRMED", "CHECKED_IN") else "Hidden (Cancelled)"
    data["host_phone"] = APARTMENT_LISTING["host_phone"]
    return data

def cancel_visitor_booking(conn, booking_code: str, phone_or_email: str) -> bool:
    ident = phone_or_email.strip().lower()
    norm_phone = normalize_ng_phone(ident) or ident
    cur = conn.cursor()
    cur.execute(
        "UPDATE inspections SET status = 'CANCELLED' WHERE UPPER(booking_code) = ? AND (phone = ? OR LOWER(email) = ?) AND status = 'CONFIRMED'",
        (booking_code.strip().upper(), norm_phone, ident),
    )
    conn.commit()
    if cur.rowcount > 0:
        log_audit(conn, f"Booking {booking_code.strip().upper()} cancelled by visitor", "INFO")
        return True
    return False

def get_booked_slots(conn, visit_date: str, unit_name: str = "Unit 1 (1-Bed Self-Contain)") -> list[str]:
    cur = conn.cursor()
    cur.execute(
        "SELECT visit_time FROM inspections WHERE unit_name = ? AND visit_date = ? AND status IN ('CONFIRMED', 'CHECKED_IN')",
        (unit_name, visit_date.strip()),
    )
    return [r for r in cur.fetchall()]

def host_list_inspections(conn) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        """SELECT booking_code, gate_pin, unit_name, full_name, email, phone, visitor_state, visitor_address, id_masked, guests, visit_date, visit_time, status
           FROM inspections ORDER BY id DESC LIMIT 50"""
    )
    cols = ["booking_code", "gate_pin", "unit_name", "full_name", "email", "phone", "visitor_state", "visitor_address", "id_type", "guests", "visit_date", "visit_time", "status"]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def host_checkin_visitor(conn, booking_code: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "UPDATE inspections SET status = 'CHECKED_IN' WHERE UPPER(booking_code) = ? AND status = 'CONFIRMED'",
        (booking_code.strip().upper(),),
    )
    conn.commit()
    if cur.rowcount > 0:
        log_audit(conn, f"Visitor checked in at gate ({booking_code.strip().upper()})", "OK")
        return True
    return False
