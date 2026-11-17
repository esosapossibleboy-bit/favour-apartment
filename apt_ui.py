from apt_db import APARTMENT_LISTING, NIGERIAN_STATES
from apt_script import render_apt_script
from apt_styles import render_apt_head

def render_apartment_app() -> str:
    states_options = "".join(
        f'<option value="{st}" {"selected" if st == "Edo" else ""}>{st}</option>'
        for st in sorted(NIGERIAN_STATES)
    )
    return f"""<!DOCTYPE html>
<html lang="en">
{render_apt_head(APARTMENT_LISTING['title'])}
<body>
    <div class="bar">
        <div>
            <div style="font-weight:800;font-size:1.1rem;color:#fbbf24;">🏢 {APARTMENT_LISTING['title']}</div>
            <div style="font-size:0.78rem;color:#cbd5e1;">Benin City, Edo State • Tenant Inspection Portal</div>
        </div>
        <span class="badge">🛡️ BVN/NIN & AI Guarded</span>
    </div>

    <div class="wrap">
        <div class="hero">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-weight:700;font-size:1.05rem;">📍 {APARTMENT_LISTING['area']}</span>
                <span style="color:#fbbf24;font-weight:800;font-size:0.88rem;">{APARTMENT_LISTING['rent_annual']}</span>
            </div>
            <div style="font-size:0.85rem;color:#e2e8f0;margin-top:6px;font-weight:600;">
                🏠 3 Modern Self-Contained Units Available
            </div>
            <div class="room-grid">
                <div class="room-card"><div style="font-size:1.3rem;">🛏️</div><strong>1 Bedroom</strong><div style="color:#94a3b8;font-size:0.7rem;">Spacious & Airy</div></div>
                <div class="room-card"><div style="font-size:1.3rem;">🛋️</div><strong>Sitting Room</strong><div style="color:#94a3b8;font-size:0.7rem;">Private Lounge</div></div>
                <div class="room-card"><div style="font-size:1.3rem;">🍳</div><strong>Kitchen</strong><div style="color:#94a3b8;font-size:0.7rem;">Private Fitted</div></div>
                <div class="room-card"><div style="font-size:1.3rem;">🚿</div><strong>Bathroom</strong><div style="color:#94a3b8;font-size:0.7rem;">Modern Tiled</div></div>
                <div class="room-card"><div style="font-size:1.3rem;">🚽</div><strong>Toilet</strong><div style="color:#94a3b8;font-size:0.7rem;">Private WC</div></div>
                <div class="room-card"><div style="font-size:1.3rem;">🛡️</div><strong>Gated</strong><div style="color:#94a3b8;font-size:0.7rem;">PIN Check-In</div></div>
            </div>
            <p style="font-size:0.82rem;color:#cbd5e1;margin:10px 0 0;line-height:1.5;">
                🔒 Visitors must verify their real Nigerian phone, house address, and <strong>11-digit NIN or BVN</strong> (encrypted & masked). One active booking per person.
            </p>
        </div>

        <div class="tabs">
            <button id="btnBook" class="tab active" onclick="showTab('book')">📅 Book</button>
            <button id="btnPass" class="tab" onclick="showTab('pass')">🎟️ Pass</button>
            <button id="btnAi" class="tab" onclick="showTab('ai')">🤖 Ask AI</button>
            <button id="btnHost" class="tab" onclick="showTab('host')">🔐 Host</button>
        </div>

        <div id="secBook" class="card">
            <h3 style="margin-top:0;">Schedule Your Physical Tour</h3>
            <label style="font-size:0.8rem;color:#94a3b8;">1. Choose Self-Contained Unit, Date & Time</label>
            <select id="unitName" onchange="loadSlots()">
                <option value="Unit 1 (1-Bed Self-Contain)">Unit 1 — 1-Bed Self-Contain (Room, Sitting Room, Kitchen, Bath & Toilet)</option>
                <option value="Unit 2 (1-Bed Self-Contain)">Unit 2 — 1-Bed Self-Contain (Room, Sitting Room, Kitchen, Bath & Toilet)</option>
                <option value="Unit 3 (1-Bed Self-Contain)">Unit 3 — 1-Bed Self-Contain (Room, Sitting Room, Kitchen, Bath & Toilet)</option>
            </select>
            <input id="visitDate" type="date" onchange="loadSlots()" />
            <select id="visitTime">
                <option value="10:00 AM">10:00 AM — Morning Tour</option>
                <option value="12:00 PM">12:00 PM — Midday Tour</option>
                <option value="02:30 PM">02:30 PM — Afternoon Tour</option>
                <option value="04:30 PM">04:30 PM — Evening Tour</option>
            </select>

            <label style="display:block;margin-top:12px;font-size:0.8rem;color:#94a3b8;">2. Real Visitor Identity Verification (Nigeria)</label>
            <input id="fullName" placeholder="Real First & Last Name (as on NIN/BVN)" />
            <input id="email" type="email" placeholder="Real Email Address" />
            <input id="phone" type="tel" placeholder="Real Nigerian Phone (e.g. 08031234567)" />
            <select id="visitorState">{states_options}</select>
            <input id="visitorAddress" placeholder="Real House Number & Street Address (e.g. 15 Airport Rd)" />
            <div style="display:flex;gap:8px;">
                <select id="idType" style="width:120px;">
                    <option value="NIN">NIN (11 Digits)</option>
                    <option value="BVN">BVN (11 Digits)</option>
                </select>
                <input id="idNumber" maxlength="11" inputmode="numeric" placeholder="Enter 11-Digit NIN or BVN" />
            </div>
            <select id="guests">
                <option value="1">1 Visitor (Solo Inspection)</option>
                <option value="2">2 Visitors (Max Allowed for Security)</option>
            </select>

            <input id="websiteUrl" autocomplete="off" tabindex="-1" style="position:absolute;left:-9999px;" />
            <div style="margin-top:10px;padding:10px;background:#0b1021;border:1px solid #2a3963;border-radius:10px;">
                <label id="mathPrompt" style="font-size:0.82rem;color:#fbbf24;font-weight:700;">Human Security Check: What is 2 + 3?</label>
                <input id="mathAnswer" type="number" inputmode="numeric" placeholder="Enter answer" />
            </div>

            <button onclick="submitBooking()">🔒 Verify & Unlock House Address</button>
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

        <div id="secAi" class="card" style="display:none;">
            <h3 style="margin-top:0;">🤖 Favour Apartment AI Assistant</h3>
            <p style="font-size:0.82rem;color:#94a3b8;margin-top:0;">Ask about annual rent, room layout, security verification, or inspection hours.</p>
            <input id="aiQuestion" placeholder="e.g. How much is the annual rent?" />
            <button onclick="askAiAssistant()">✨ Ask Assistant</button>
            <p id="aiErr" class="err"></p>
            <div id="aiReplyBox" style="display:none;" class="ai-box"></div>
        </div>

        <div id="secHost" class="card" style="display:none;">
            <h3 style="margin-top:0;">🔐 Landlord & Security Audit Portal</h3>
            <input id="hostPasscode" type="password" placeholder="Enter Host Passcode (Default: 246810)" />
            <button onclick="loadHostInspections()">🛡️ Unlock Manifest & Security Logs</button>
            <p id="hostMsg" class="err"></p>
            <div id="hostList"></div>
            <h4 style="margin:14px 0 6px;color:#fbbf24;">📜 Security Audit Trail</h4>
            <div id="auditList"></div>
        </div>
    </div>
    {render_apt_script()}
</body>
</html>"""
