import hashlib
import hmac
import os
import re
import time
from datetime import date, timedelta

NIGERIAN_STATES = {
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue", "Borno",
    "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "FCT - Abuja", "Gombe",
    "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara", "Lagos",
    "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo", "Plateau", "Rivers", "Sokoto",
    "Taraba", "Yobe", "Zamfara",
}

ALLOWED_ID_TYPES = {"NIN", "BVN"}
ALLOWED_TIME_SLOTS = {"10:00 AM", "12:00 PM", "02:30 PM", "04:30 PM"}
APARTMENT_UNITS = {
    "Unit 1 (1-Bed Self-Contain)",
    "Unit 2 (1-Bed Self-Contain)",
    "Unit 3 (1-Bed Self-Contain)",
}

BLOCKED_EMAIL_DOMAINS = {"mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com", "yopmail.com", "fake.com", "test.com"}
FAKE_NUMBERS = {"00000000000", "11111111111", "22222222222", "12345678901", "01234567890", "98765432109"}

APARTMENT_LISTING = {
    "title": os.getenv("APT_TITLE", "Favour Apartment"),
    "area": os.getenv("APT_AREA", "Benin City, Edo State"),
    "exact_address": os.getenv("APT_EXACT_ADDRESS", "Favour Apartment, Off Agbor Road, Benin City, Edo State"),
    "rent_annual": os.getenv("APT_RENT", "₦200,000 / year"),
    "host_phone": os.getenv("APT_HOST_PHONE", "+2348060317852"),
    "host_passcode": os.getenv("APT_HOST_PASSCODE", "246810"),
    "id_pepper": os.getenv("APT_ID_PEPPER", "favour_apt_benin_pepper_2026"),
}

HOST_FAILS = {"count": 0, "locked_until": 0.0}

def verify_host_passcode(passcode: str) -> tuple[bool, str]:
    now = time.time()
    if HOST_FAILS["locked_until"] > now:
        mins = max(1, int((HOST_FAILS["locked_until"] - now + 59) // 60))
        return False, f"Host portal locked after 5 failed attempts. Try again in {mins} min(s)."
    ok = hmac.compare_digest((passcode or "").strip(), APARTMENT_LISTING["host_passcode"])
    if ok:
        HOST_FAILS["count"] = 0
        HOST_FAILS["locked_until"] = 0.0
        return True, ""
    HOST_FAILS["count"] += 1
    if HOST_FAILS["count"] >= 5:
        HOST_FAILS["locked_until"] = now + 900
    return False, "Wrong Host Passcode"

def hash_gov_id(id_type: str, id_number: str) -> str:
    raw = f"{id_type}:{id_number}:{APARTMENT_LISTING['id_pepper']}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def sanitize_text(val: str) -> str:
    return re.sub(r"[<>\"';]", "", (val or "").strip())

def validate_visit_window(visit_date_str: str, visit_time: str) -> str | None:
    if visit_time not in ALLOWED_TIME_SLOTS:
        return "Select a valid daytime inspection slot (10:00 AM - 04:30 PM)"
    try:
        chosen = date.fromisoformat(visit_date_str.strip())
    except ValueError:
        return "Invalid inspection date format"
    tomorrow = date.today() + timedelta(days=1)
    max_day = date.today() + timedelta(days=30)
    if chosen < tomorrow:
        return "Inspections must be booked at least 1 day in advance (starting tomorrow)"
    if chosen > max_day:
        return "Inspections can only be booked up to 30 days ahead"
    return None

def verify_human_challenge(honeypot: str, math_a: int, math_b: int, math_answer: int) -> bool:
    if (honeypot or "").strip():
        return False
    if not (1 <= math_a <= 9 and 1 <= math_b <= 9):
        return False
    return math_answer == (math_a + math_b)

def normalize_ng_phone(phone: str) -> str | None:
    cleaned = re.sub(r"[\s\-()]", "", phone.strip())
    if re.fullmatch(r"0(70|80|81|90|91)\d{8}", cleaned):
        num = cleaned
    elif re.fullmatch(r"\+?234(70|80|81|90|91)\d{8}", cleaned):
        num = "0" + cleaned.lstrip("+")[3:]
    else:
        return None
    if len(set(num[3:])) <= 2 or num in FAKE_NUMBERS:
        return None
    return num

def validate_real_email(email: str) -> str | None:
    clean = email.strip().lower()
    if not re.fullmatch(r"[a-z0-9._%+-]{2,}@[a-z0-9.-]+\.[a-z]{2,}", clean):
        return None
    _, domain = clean.split("@", 1)
    if domain in BLOCKED_EMAIL_DOMAINS or domain.endswith(".invalid"):
        return None
    return clean

def validate_gov_id(id_type: str, id_number: str) -> str | None:
    if id_type not in ALLOWED_ID_TYPES:
        return None
    digits = re.sub(r"\s+", "", (id_number or "").strip())
    if not re.fullmatch(r"\d{11}", digits):
        return None
    if len(set(digits)) <= 2 or digits in FAKE_NUMBERS:
        return None
    return digits
