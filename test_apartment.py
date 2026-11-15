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

    # 1. Verify homepage renders Favour Apartment and hides exact address before booking
    home_html = client.get("/").text
    assert "Favour Apartment" in home_html
    assert "Plot 14 Admiralty Way" not in home_html

    # 2. Reject invalid Nigerian phone number
    bad_phone = client.post("/api/book", json={
        "full_name": "Chinedu Okafor",
        "email": "chinedu@example.com",
        "phone": "1234567890",
        "visitor_state": "Lagos",
        "visitor_address": "15 Allen Avenue, Ikeja",
        "id_type": "NIN Slip",
        "guests": 1,
        "visit_date": "2026-12-01",
        "visit_time": "10:00 AM",
    })
    assert bad_phone.status_code == 400

    # 3. Book valid inspection -> unlocks Gate PIN & exact house address
    ok_res = client.post("/api/book", json={
        "full_name": "Chinedu Okafor",
        "email": "chinedu@example.com",
        "phone": "+2348031234567",
        "visitor_state": "Lagos",
        "visitor_address": "15 Allen Avenue, Ikeja",
        "id_type": "NIN Slip",
        "guests": 2,
        "visit_date": "2026-12-01",
        "visit_time": "10:00 AM",
    })
    assert ok_res.status_code == 200
    booking = ok_res.json()
    assert booking["booking_code"].startswith("FAV-")
    assert len(booking["gate_pin"]) == 4
    assert "Plot 14 Admiralty Way" in booking["exact_address"]

    # 4. Prevent double-booking the exact same date & time slot
    double_book = client.post("/api/book", json={
        "full_name": "Amina Bello",
        "email": "amina@example.com",
        "phone": "08098765432",
        "visitor_state": "FCT - Abuja",
        "visitor_address": "22 Wuse Zone 4, Abuja",
        "id_type": "International Passport",
        "guests": 1,
        "visit_date": "2026-12-01",
        "visit_time": "10:00 AM",
    })
    assert double_book.status_code == 400

    # 5. Private Gate Pass lookup requires matching phone/email
    wrong_person = client.post("/api/pass", json={
        "booking_code": booking["booking_code"],
        "phone_or_email": "08098765432",
    })
    assert wrong_person.status_code == 404

    right_person = client.post("/api/pass", json={
        "booking_code": booking["booking_code"],
        "phone_or_email": "08031234567",
    })
    assert right_person.status_code == 200
    assert right_person.json()["gate_pin"] == booking["gate_pin"]

    # 6. Cancel inspection and verify slot frees up again
    cancel_res = client.post("/api/cancel", json={
        "booking_code": booking["booking_code"],
        "phone_or_email": "chinedu@example.com",
    })
    assert cancel_res.status_code == 200
    assert client.get("/api/slots?visit_date=2026-12-01").json()["booked"] == []

    os.remove(test_db)
