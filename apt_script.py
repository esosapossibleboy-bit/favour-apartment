from apt_db import APARTMENT_LISTING

def render_apt_script() -> str:
    return f"""
    <script>
        const tomorrow = new Date(Date.now() + 86400000).toISOString().split("T");
        visitDate.min = tomorrow;
        visitDate.value = tomorrow;

        function showTab(name) {{
            secBook.style.display = name === "book" ? "block" : "none";
            secPass.style.display = name === "pass" ? "block" : "none";
            secHost.style.display = name === "host" ? "block" : "none";
            btnBook.className = "tab" + (name === "book" ? " active" : "");
            btnPass.className = "tab" + (name === "pass" ? " active" : "");
            btnHost.className = "tab" + (name === "host" ? " active" : "");
        }}

        async function loadSlots() {{
            if (!visitDate.value) return;
            const res = await fetch("/api/slots?visit_date=" + encodeURIComponent(visitDate.value) + "&unit_name=" + encodeURIComponent(unitName.value));
            const data = await res.json();
            const taken = new Set(data.booked || []);
            for (const opt of visitTime.options) {{
                const base = opt.value;
                opt.disabled = taken.has(base);
                opt.textContent = taken.has(base) ? `${{base}} — RESERVED` : `${{base}} — Available`;
            }}
        }}

        function renderPassHTML(d, allowCancel = false) {{
            return `
                <div style="font-weight:800;color:#4ade80;font-size:1.05rem;">✅ CONFIRMED INSPECTION PASS</div>
                <div style="margin-top:8px;font-size:0.9rem;line-height:1.6;">
                    <div><strong>Property:</strong> {APARTMENT_LISTING['title']} — ${{d.unit_name}}</div>
                    <div><strong>Booking Code:</strong> <span style="color:#fbbf24;font-weight:800;">${{d.booking_code}}</span></div>
                    <div><strong>Gate Security PIN:</strong> <span style="background:#14532d;padding:2px 8px;border-radius:6px;color:#fef08a;font-weight:800;">${{d.gate_pin}}</span></div>
                    <div><strong>Visitor:</strong> ${{d.full_name}} (${{d.guests}} guest(s))</div>
                    <div><strong>ID Required at Gate:</strong> ${{d.id_type}}</div>
                    <div><strong>Date & Time:</strong> ${{d.visit_date}} at ${{d.visit_time}}</div>
                    <div style="margin-top:6px;padding:8px;background:#090d1a;border-radius:8px;border:1px solid #15803d;">
                        <strong>📍 Exact House Address:</strong><br/>${{d.exact_address}}<br/>
                        <strong>📞 Host Contact:</strong> ${{d.host_phone}}
                    </div>
                </div>
                ${{allowCancel && d.status === "CONFIRMED" ? `<button class="btn-danger" onclick="cancelPass('${{d.booking_code}}')">❌ Cancel This Inspection</button>` : ""}}
            `;
        }}

        async function submitBooking() {{
            bookErr.textContent = ""; gatePassCard.style.display = "none";
            const payload = {{
                unit_name: unitName.value,
                full_name: fullName.value, email: email.value, phone: phone.value,
                visitor_state: visitorState.value, visitor_address: visitorAddress.value,
                id_type: idType.value, guests: parseInt(guests.value),
                visit_date: visitDate.value, visit_time: visitTime.value
            }};
            const res = await fetch("/api/book", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify(payload)
            }});
            const d = await res.json();
            if (!res.ok) return bookErr.textContent = d.detail || "Booking failed";
            gatePassCard.innerHTML = renderPassHTML(d, false);
            gatePassCard.style.display = "block";
            loadSlots();
        }}

        async function findPass() {{
            lookupMsg.textContent = ""; foundPassBox.style.display = "none";
            const res = await fetch("/api/pass", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ booking_code: lookupCode.value, phone_or_email: lookupContact.value }})
            }});
            const d = await res.json();
            if (!res.ok) return lookupMsg.textContent = d.detail || "Booking not found";
            foundPassBox.innerHTML = renderPassHTML(d, true);
            foundPassBox.style.display = "block";
        }}

        async function cancelPass(code) {{
            const res = await fetch("/api/cancel", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ booking_code: code, phone_or_email: lookupContact.value }})
            }});
            if (res.ok) {{ foundPassBox.style.display = "none"; lookupMsg.className = "ok"; lookupMsg.textContent = "✅ Inspection cancelled."; loadSlots(); }}
        }}

        async function loadHostInspections() {{
            hostMsg.textContent = ""; hostList.innerHTML = "";
            const res = await fetch("/api/host/inspections", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ passcode: hostPasscode.value }})
            }});
            const d = await res.json();
            if (!res.ok) return hostMsg.textContent = d.detail || "Access denied";
            if (!d.inspections.length) return hostMsg.textContent = "No inspections scheduled yet.";
            hostList.innerHTML = d.inspections.map(v => `
                <div class="host-item">
                    <div style="display:flex;justify-content:space-between;">
                        <strong style="color:#fbbf24;">${{v.booking_code}} • PIN: ${{v.gate_pin}}</strong>
                        <span style="color:${{v.status==='CHECKED_IN'?'#34d399':(v.status==='CANCELLED'?'#fb7185':'#93c5fd')}};font-weight:700;">${{v.status}}</span>
                    </div>
                    <div style="color:#fde68a;font-weight:600;">🏠 ${{v.unit_name}}</div>
                    <div><strong>${{v.full_name}}</strong> (${{v.guests}} guest(s))</div>
                    <div>📞 ${{v.phone}} | ✉️ ${{v.email}}</div>
                    <div>🪪 ID: ${{v.id_type}} | 📍 ${{v.visitor_address}}, ${{v.visitor_state}}</div>
                    <div>📅 ${{v.visit_date}} at ${{v.visit_time}}</div>
                    ${{v.status === "CONFIRMED" ? `<button style="padding:8px;margin-top:8px;" onclick="checkInVisitor('${{v.booking_code}}')">✅ Check In at Gate</button>` : ""}}
                </div>
            `).join("");
        }}

        async function checkInVisitor(code) {{
            const res = await fetch("/api/host/checkin", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ passcode: hostPasscode.value, booking_code: code }})
            }});
            if (res.ok) loadHostInspections();
        }}

        loadSlots();
    </script>
    """
