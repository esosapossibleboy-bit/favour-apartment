import json
import os
import smtplib
import urllib.request
from email.message import EmailMessage

NOTIFICATION_LOG: list[dict] = []

def send_email_alert(to_email: str, booking: dict) -> str:
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").strip()
    body = (
        f"Hello {booking['full_name']},\n\n"
        f"Your Favour Apartment tour is CONFIRMED!\n"
        f"Booking Code: {booking['booking_code']}\n"
        f"Gate Security PIN: {booking['gate_pin']}\n"
        f"Unit: {booking['unit_name']}\n"
        f"Date & Time: {booking['visit_date']} at {booking['visit_time']}\n"
        f"Address: {booking['exact_address']}\n"
        f"Host Phone: {booking['host_phone']}\n"
    )
    if smtp_host and smtp_user and smtp_pass:
        msg = EmailMessage()
        msg["Subject"] = f"Favour Apartment Pass — {booking['booking_code']} (PIN: {booking['gate_pin']})"
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg.set_content(body)
        with smtplib.SMTP_SSL(smtp_host, int(os.getenv("SMTP_PORT", "465")), timeout=8) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return "EMAIL_SENT_SMTP"
    return "EMAIL_QUEUED_READY"

def send_sms_alert(to_phone: str, booking: dict) -> str:
    sms_key = os.getenv("SMS_API_KEY", "").strip()
    intl_phone = "234" + to_phone[1:] if to_phone.startswith("0") else to_phone.lstrip("+")
    sms_text = (
        f"Favour Apartment: Tour CONFIRMED! Code {booking['booking_code']}, "
        f"Gate PIN {booking['gate_pin']}, {booking['unit_name']} on {booking['visit_date']} {booking['visit_time']}."
    )
    if sms_key:
        payload = json.dumps({
            "to": intl_phone,
            "from": os.getenv("SMS_SENDER_ID", "FavourApt"),
            "sms": sms_text,
            "type": "plain",
            "channel": "generic",
            "api_key": sms_key,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://termii.com",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status in (200, 201):
                return "SMS_SENT_TERMII"
    return "SMS_QUEUED_READY"

def dispatch_booking_alerts(booking: dict) -> dict:
    email_status = send_email_alert(booking["email"], booking)
    sms_status = send_sms_alert(booking["phone"], booking)
    record = {
        "booking_code": booking["booking_code"],
        "email": booking["email"],
        "phone": booking["phone"],
        "email_status": email_status,
        "sms_status": sms_status,
    }
    NOTIFICATION_LOG.append(record)
    return record

def build_appointment_pdf(booking: dict) -> bytes:
    """Generates a valid standalone PDF document for the visitor's Appointment Pass."""
    def esc(val: str) -> str:
        return str(val).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    lines = [
        "FAVOUR APARTMENT - BENIN CITY, EDO STATE",
        "OFFICIAL CONFIRMED INSPECTION PASS",
        "----------------------------------------------------",
        f"Booking Code: {booking['booking_code']}",
        f"Gate Security PIN: {booking['gate_pin']}",
        f"Selected Unit: {booking['unit_name']}",
        f"Visitor Name: {booking['full_name']} ({booking['guests']} guest(s))",
        f"Verified ID: {booking['id_type']}",
        f"Appointment: {booking['visit_date']} at {booking['visit_time']}",
        f"House Address: {booking['exact_address']}",
        f"Host Contact: {booking['host_phone']}",
        "----------------------------------------------------",
        "Present this PDF Pass & your ID at the security gate.",
    ]
    ops = ["BT", "/F1 13 Tf", "50 750 Td", "18 TL"]
    for idx, line in enumerate(lines):
        if idx == 2:
            ops.append("/F1 11 Tf")
        ops.append(f"({esc(line)}) Tj")
        ops.append("T*")
    ops.append("ET")
    stream = "\n".join(ops).encode("latin-1", errors="replace")

    objs = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n",
        f"4 0 obj << /Length {len(stream)} >> stream\n".encode("ascii") + stream + b"\nendstream endobj\n",
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for obj in objs:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for off in offsets:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer << /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii"))
    return bytes(pdf)
