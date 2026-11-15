from apt_db import APARTMENT_LISTING, NIGERIAN_STATES
from apt_script import render_apt_script

def render_apartment_app() -> str:
    states_options = "".join(
        f'<option value="{st}" {"selected" if st == "Lagos" else ""}>{st}</option>'
        for st in sorted(NIGERIAN_STATES)
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{APARTMENT_LISTING['title']} — Secure House Inspection</title>
    <style>
        * {{ box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; }}
        body {{ margin: 0; background: #090d1a; color: #f8fafc; }}
        .bar {{ background: linear-gradient(135deg, #1e1b4b, #312e81); padding: 18px 20px; border-bottom: 1px solid #3730a3; display: flex; justify-content: space-between; align-items: center; }}
        .wrap {{ max-width: 520px; margin: 0 auto; padding: 16px; }}
        .hero {{ background: linear-gradient(135deg, #312e81, #0f172a); border: 1px solid #4338ca; border-radius: 18px; padding: 18px; margin-bottom: 14px; }}
        .badge {{ display: inline-block; background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.35); padding: 4px 10px; border-radius: 999px; font-size: 0.76rem; font-weight: 700; }}
        .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 16px; padding: 16px; margin-bottom: 14px; }}
        input, select {{ width: 100%; padding: 11px 12px; margin-top: 8px; border-radius: 10px; border: 1px solid #374151; background: #0b1021; color: #f8fafc; font-size: 0.94rem; }}
        button {{ width: 100%; padding: 12px; margin-top: 12px; border: none; border-radius: 12px; font-weight: 700; font-size: 0.95rem; cursor: pointer; background: linear-gradient(135deg, #f59e0b, #d97706); color: #090d1a; }}
        .btn-dark {{ background: #1f2937; color: #f8fafc; border: 1px solid #374151; }}
        .btn-danger {{ background: #7f1d1d; color: #fecaca; }}
        .tabs {{ display: flex; gap: 6px; margin-bottom: 12px; }}
        .tab {{ flex: 1; margin: 0; padding: 10px 6px; font-size: 0.84rem; background: #1f2937; color: #cbd5e1; }}
        .tab.active {{ background: #4f46e5; color: white; }}
        .pass-box {{ background: #052e16; border: 1px solid #16a34a; border-radius: 14px; padding: 14px; margin-top: 12px; }}
        .host-item {{ background: #0b1021; border: 1px solid #2a3963; border-radius: 12px; padding: 12px; margin-top: 10px; font-size: 0.85rem; line-height: 1.5; }}
        .err {{ color: #fb7185; font-size: 0.86rem; margin-top: 8px; }}
        .ok {{ color: #34d399; font-size: 0.86rem; margin-top: 8px; }}
    </style>
</head>
<body>
    <div class="bar">
        <div>
            <div style="font-weight:800;font-size:1.1rem;color:#fbbf24;">🏢 {APARTMENT_LISTING['title']}</div>
            <div style="font-size:0.78rem;color:#cbd5e1;">Verified Tenant Inspection Portal</div>
        </div>
        <span class="badge">🛡️ ID & Gate PIN Verified</span>
    </div>

    <div class="wrap">
        <div class="hero">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-weight:700;font-size:1.05rem;">📍 {APARTMENT_LISTING['area']}</span>
                <span style="color:#fbbf24;font-weight:800;">{APARTMENT_LISTING['rent_annual']}</span>
            </div>
            <p style="font-size:0.84rem;color:#cbd5e1;margin:8px 0 0;line-height:1.5;">
                🔒 For resident safety, the exact house street address and <strong>4-Digit Gate Security PIN</strong> are unlocked immediately after your booking is confirmed.
            </p>
        </div>

        <div class="tabs">
            <button id="btnBook" class="tab active" onclick="showTab('book')">📅 Book Tour</button>
            <button id="btnPass" class="tab" onclick="showTab('pass')">🎟️ Gate Pass</button>
            <button id="btnHost" class="tab" onclick="showTab('host')">🔐 Host</button>
        </div>

        <div id="secBook" class="card">
            <h3 style="margin-top:0;">Schedule Your Physical Tour</h3>
            <label style="font-size:0.8rem;color:#94a3b8;">1. Choose Inspection Date & Time Slot</label>
            <input id="visitDate" type="date" onchange="loadSlots()" />
            <select id="visitTime">
                <option value="10:00 AM">10:00 AM — Morning Tour</option>
                <option value="12:00 PM">12:00 PM — Midday Tour</option>
                <option value="02:30 PM">02:30 PM — Afternoon Tour</option>
                <option value="04:30 PM">04:30 PM — Evening Tour</option>
            </select>

            <label style="display:block;margin-top:12px;font-size:0.8rem;color:#94a3b8;">2. Visitor Security Verification (Nigeria)</label>
            <input id="fullName" placeholder="Real First & Last Name (as on ID)" />
            <input id="email" type="email" placeholder="Email Address" />
            <input id="phone" type="tel" placeholder="Nigerian Phone (e.g. 08031234567)" />
            <select id="visitorState">{states_options}</select>
            <input id="visitorAddress" placeholder="Your Current Home / Office Street Address" />
            <select id="idType">
                <option value="NIN Slip">Government ID: NIN Slip / Card</option>
                <option value="Driver's License">Government ID: Driver's License</option>
                <option value="Voter's Card">Government ID: Voter's Card</option>
                <option value="International Passport">Government ID: International Passport</option>
            </select>
            <select id="guests">
                <option value="1">1 Visitor (Solo Inspection)</option>
                <option value="2">2 Visitors (Max Allowed for Security)</option>
            </select>

            <button onclick="submitBooking()">🔒 Confirm Booking & Unlock Address</button>
            <p id="bookErr" class="err"></p>
            <div id="gatePassCard" style="display:none;" class="pass-box"></div>
        </div>

        <div id="secPass" class="card" style="display:none;">
            <h3 style="margin-top:0;">🎟️ Retrieve or Cancel Gate Pass</h3>
            <input id="lookupCode" placeholder="Booking Code (e.g. FAV-A1B2C3)" />
            <input id="lookupContact" placeholder="Registered Phone Number or Email" />
            <button class="btn-dark" onclick="findPass()">🔍 Unlock My Gate Pass</button>
            <p id="lookupMsg" class="err"></p>
            <div id="foundPassBox" style="display:none;" class="pass-box"></div>
        </div>

        <div id="secHost" class="card" style="display:none;">
            <h3 style="margin-top:0;">🔐 Landlord & Gate Security Portal</h3>
            <input id="hostPasscode" type="password" placeholder="Enter Host Passcode (Default: 246810)" />
            <button onclick="loadHostInspections()">🛡️ Unlock Visitor Manifest</button>
            <p id="hostMsg" class="err"></p>
            <div id="hostList"></div>
        </div>
    </div>
    {render_apt_script()}
</body>
</html>"""
