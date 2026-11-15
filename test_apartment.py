import os
from fastapi.testclient import TestClient
import apt_server

client = TestClient(apt_server.app)

def test_favour_apartment_booking_and_security(monkeypatch):
    test_db = "temp_apartment_tours.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    monkeypatch.setattr(apt_server, "DB_PATH", test_db)
    apt_server.IP_HISTORY.clear()

    # 1. Verify homepage renders Favour Apartment in Benin City, Edo State and hides exact address before booking
    home_html = client.get("/").text
    assert "Favour Apartment" in home_html
    assert "Benin City, Edo State" in home_html
    assert "Exact Street Unlocked on Confirmation" not in home_html

    # 2. Reject invalid Nigerian phone number
    bad_phone = client.post("/api/book", json={
        "unit_name": "Unit 1 (1-Bed Self-Contain)",
        "full_name": "Chinedu Okafor",
        "email": "chinedu@example.com",
        "phone": "1234567890",
        "visitor_state": "Edo",
        "visitor_address": "15 Airport Road, Benin City",
        "id_type": "NIN Slip",
        "guests": 1,
        "visit_date": "2026-12-01",
        "visit_time": "10:00 AM",
    })
    assert bad_phone.status_code == 400

    # 3. Book valid inspection for Unit 1 -> unlocks Gate PIN & exact house address
    ok_res = client.post("/api/book", json={
        "unit_name": "Unit 1 (1-Bed Self-Contain)",
        "full_name": "Chinedu Okafor",
        "email": "chinedu@example.com",
        "phone": "+2348031234567",
        "visitor_state": "Edo",
        "visitor_address": "15 Airport Road, Benin City",
        "id_type": "NIN Slip",
        "guests": 2,
        "visit_date": "2026-12-01",
        "visit_time": "10:00 AM",
    })
    assert ok_res.status_code == 200
    booking = ok_res.json()
    assert booking["booking_code"].startswith("FAV-")
    assert len(booking["gate_pin"]) == 4
    assert "Benin City, Edo State" in booking["exact_address"]

    # 4. Prevent double-booking Unit 1 on the exact same date & time slot
    double_book = client.post("/api/book", json={
        "unit_name": "Unit 1 (1-Bed Self-Contain)",
        "full_name": "Amina Bello",
        "email": "amina@example.com",
        "phone": "08098765432",
        "visitor_state": "Edo",
        "visitor_address": "22 Sapele Road, Benin City",
        "id_type": "International Passport",
        "guests": 1,
        "visit_date": "2026-12-01",
        "visit_time": "10:00 AM",
    })
    assert double_book.status_code == 400

    # 5. Another visitor CAN book Unit 2 at the same time slot!
    unit2_book = client.post("/api/book", json={
        "unit_name": "Unit 2 (1-Bed Self-Contain)",
        "full_name": "Amina Bello",
        "email": "amina@example.com",
        "phone": "08098765432",
        "visitor_state": "Edo",
        "visitor_address": "22 Sapele Road, Benin City",
        "id_type": "International Passport",
        "guests": 1,
        "visit_date": "2026-12-01",
        "visit_time": "10:00 AM",
    })
    assert unit2_book.status_code == 200

    # 6. Host Dashboard requires valid Host Passcode & allows Gate Check-In
    assert client.post("/api/host/inspections", json={"passcode": "000000"}).status_code == 401
    host_res = client.post("/api/host/inspections", json={"passcode": "246810"})
    assert host_res.status_code == 200
    assert len(host_res.json()["inspections"]) == 2
    assert client.post("/api/host/checkin", json={"passcode": "246810", "booking_code": booking["booking_code"]}).status_code == 200

    os.remove(test_db)
