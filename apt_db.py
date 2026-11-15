import hmac
import os
import re
import secrets
import sqlite3
from datetime import datetime

NIGERIAN_STATES = {
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue", "Borno",
    "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "FCT - Abuja", "Gombe",
    "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara", "Lagos",
    "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo", "Plateau", "Rivers", "Sokoto",
    "Taraba", "Yobe", "Zamfara",
}

ALLOWED_ID_TYPES = {"NIN Slip", "Driver's License", "Voter's Card", "International Passport"}
APARTMENT_UNITS = {
    "Unit 1 (1-Bed Self-Contain)",
    "Unit 2 (1-Bed Self-Contain)",
    "Unit 3 (1-Bed Self-Contain)",
}

APARTMENT_LISTING = {
    "title": os.getenv("APT_TITLE", "Favour Apartment"),
    "area": os.getenv("APT_AREA", "Benin City, Edo State"),
    "features": os.getenv("APT_FEATURES", "3 Units Available • Each: 1 Bedroom, Sitting Room, Kitchen, Toilet & Bathroom"),
    "exact_address": os.getenv("APT_EXACT_ADDRESS", "Favour Apartment, Benin City, Edo State (Exact Street Unlocked on Confirmation)"),
    "rent_annual": os.getenv("APT_RENT", "Contact Host for Rent"),
    "host_phone": os.getenv("APT_HOST_PHONE", "0803 000 0000"),
    "host_passcode": os.getenv("APT_HOST_PASSCODE", "246810"),
}

def verify_host_passcode(passcode: str) -> bool:
    return hmac.compare_digest((passcode or "").strip(), APARTMENT_LISTING["host_passcode"])

def get_conn(db_path: str = "apartment_tours.db"):
    conn = sqlite3.connect(db_path)
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
            guests INTEGER NOT NULL DEFAULT 1,
            visit_date TEXT NOT NULL,
            visit_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'CONFIRMED',
            created_at TEXT NOT NULL
        )
    """)
    try:
        conn.execute("ALTER TABLE inspections ADD COLUMN unit_name TEXT NOT NULL DEFAULT 'Unit 1 (1-Bed Self-Contain)'")
    except Exception:
        pass
    conn.execute("CREATE INDEX IF NOT EXISTS idx_slot ON inspections(unit_name, visit_date, visit_time, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_guest ON inspections(phone, email)")
    conn.commit()
    return conn

def normalize_ng_phone(phone: str) -> str | None:
    cleaned = re.sub(r"[\s\-()]", "", phone.strip())
    if re.fullmatch(r"0(70|80|81|90|91)\d{8}", cleaned):
        return cleaned
    if re.fullmatch(r"\+?234(70|80|81|90|91)\d{8}", cleaned):
        digits = cleaned.lstrip("+")
        return "0" + digits[3:]
    return None

def book_inspection(
    conn,
    full_name: str,
    email: str,
    phone: str,
    visitor_state: str,
    visitor_address: str,
    id_type: str,
    guests: int,
    visit_date: str,
    visit_time: str,
    unit_name: str = "Unit 1 (1-Bed Self-Contain)",
) -> dict:
    clean_name = full_name.strip()
    if len(clean_name.split()) < 2:
        return {"ok": False, "error": "Enter your real First Name and Last Name"}

    clean_email = email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", clean_email):
        return {"ok": False, "error": "Enter a valid email address"}

    clean_phone = normalize_ng_phone(phone)
    if not clean_phone:
        return {"ok": False, "error": "Enter a valid Nigerian phone number (e.g. 08031234567)"}

    if visitor_state not in NIGERIAN_STATES:
        return {"ok": False, "error": "Select your current Nigerian state of residence"}

    if len(visitor_address.strip()) < 6:
        return {"ok": False, "error": "Enter your current home or office address in Nigeria"}

    if id_type not in ALLOWED_ID_TYPES:
        return {"ok": False, "error": "Select a valid government ID you will present at the gate"}

    if unit_name not in APARTMENT_UNITS:
        return {"ok": False, "error": "Select Unit 1, Unit 2, or Unit 3"}

    if guests < 1 or guests > 2:
        return {"ok": False, "error": "For security, a maximum of 2 visitors is allowed per inspection"}

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM inspections WHERE phone = ? AND status = 'CONFIRMED'", (clean_phone,))
    (active_count,) = cur.fetchone() or (0,)
    if active_count >= 2:
        return {"ok": False, "error": "You already have 2 active inspection bookings"}

    cur.execute(
        "SELECT id FROM inspections WHERE unit_name = ? AND visit_date = ? AND visit_time = ? AND status = 'CONFIRMED'",
        (unit_name, visit_date.strip(), visit_time.strip()),
    )
    if cur.fetchone():
        return {"ok": False, "error": f"{unit_name} on {visit_date} at {visit_time} is already reserved."}

    code = "FAV-" + secrets.token_hex(3).upper()
    gate_pin = str(1000 + secrets.randbelow(9000))
    ts = datetime.now().strftime("%d %b %Y, %H:%M")

    cur.execute(
        """INSERT INTO inspections
           (booking_code, gate_pin, unit_name, full_name, email, phone, visitor_state, visitor_address, id_type, guests, visit_date, visit_time, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?)""",
        (code, gate_pin, unit_name, clean_name, clean_email, clean_phone, visitor_state, visitor_address.strip(), id_type, guests, visit_date.strip(), visit_time.strip(), ts),
    )
    conn.commit()
    return {
        "ok": True,
        "booking_code": code,
        "gate_pin": gate_pin,
        "unit_name": unit_name,
        "full_name": clean_name,
        "phone": clean_phone,
        "id_type": id_type,
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
        """SELECT booking_code, gate_pin, unit_name, full_name, email, phone, visitor_state, visitor_address, id_type, guests, visit_date, visit_time, status
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
    return cur.rowcount > 0

def get_booked_slots(conn, visit_date: str, unit_name: str = "Unit 1 (1-Bed Self-Contain)") -> list[str]:
    cur = conn.cursor()
    cur.execute(
        "SELECT visit_time FROM inspections WHERE unit_name = ? AND visit_date = ? AND status IN ('CONFIRMED', 'CHECKED_IN')",
        (unit_name, visit_date.strip()),
    )
    return [r[0] for r in cur.fetchall()]

def host_list_inspections(conn) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        """SELECT booking_code, gate_pin, unit_name, full_name, email, phone, visitor_state, visitor_address, id_type, guests, visit_date, visit_time, status
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
    return cur.rowcount > 0
