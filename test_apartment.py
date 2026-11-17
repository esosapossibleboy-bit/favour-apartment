import os
from datetime import date, timedelta
from fastapi.testclient import TestClient
import apt_server
from apt_ai_cache import SLOT_CACHE
from apt_notifications import NOTIFICATION_LOG

client = TestClient(apt_server.app)

def test_favour_apartment_alerts_pdf_and_security(monkeypatch):
    test_db = "temp_apartment_tours.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    monkeypatch.setattr(apt_server, "DB_PATH", test_db)
    apt_server.IP_HISTORY.clear()
    SLOT_CACHE.clear()
    NOTIFICATION_LOG.clear()

    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()

    # 1. Book inspection -> triggers Email & SMS alerts + invalidates slot cache
    ok_res = client.post("/api/book", json={
        "unit_name": "Unit 1 (1-Bed Self-Contain)",
        "full_name": "Chinedu Okafor",
        "email": "chinedu.okafor@gmail.com",
        "phone": "+2348037294815",
        "visitor_state": "Edo",
        "visitor_address": "15 Airport Road, GRA, Benin City",
        "id_type": "NIN",
        "id_number": "48291047362",
        "guests": 2,
        "visit_date": tomorrow_str,
        "visit_time": "10:00 AM",
        "math_a": 4,
        "math_b": 3,
        "math_answer": 7,
    })
    assert ok_res.status_code == 200
    booking = ok_res.json()
    assert booking["alerts_dispatched"] is True
    assert len(NOTIFICATION_LOG) == 1
    entry = NOTIFICATION_LOG[0]
    assert entry["email"] == "chinedu.okafor@gmail.com"
    assert entry["phone"] == "08037294815"

    # 2. Download valid PDF Appointment Pass containing Booking Code & Gate PIN
    pdf_res = client.post("/api/pass/pdf", json={
        "booking_code": booking["booking_code"],
        "phone_or_email": "08037294815",
    })
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF-1.4")
    assert booking["booking_code"].encode("ascii") in pdf_res.content
    assert booking["gate_pin"].encode("ascii") in pdf_res.content

    os.remove(test_db)
