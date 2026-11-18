from apt_db import APARTMENT_LISTING
from apt_pass_js import render_pass_js

def render_apt_script() -> str:
    return f"""
    <script>
        const tomorrow = new Date(Date.now() + 86400000).toISOString().split("T");
        const maxDate = new Date(Date.now() + 30 * 86400000).toISOString().split("T");
        visitDate.min = tomorrow;
        visitDate.max = maxDate;
        visitDate.value = tomorrow;

        let mathA = 2, mathB = 3;
        function refreshMathChallenge() {{
            mathA = Math.floor(Math.random() * 8) + 1;
            mathB = Math.floor(Math.random() * 8) + 1;
            mathPrompt.textContent = `Human Security Check: What is ${{mathA}} + ${{mathB}}?`;
            mathAnswer.value = "";
        }}

        function formatApiError(d, fallback) {{
            if (!d || !d.detail) return fallback;
            if (typeof d.detail === "string") return d.detail;
            if (Array.isArray(d.detail)) {{
                return d.detail.map(e => {{
                    const field = (e.loc || []).slice(-1);
                    return field ? `${{field}}: ${{e.msg}}` : e.msg;
                }}).join(" | ");
            }}
            return fallback;
        }}

        function showTab(name) {{
            secBook.style.display = name === "book" ? "block" : "none";
            secPass.style.display = name === "pass" ? "block" : "none";
            secAi.style.display = name === "ai" ? "block" : "none";
            secHost.style.display = name === "host" ? "block" : "none";
            btnBook.className = "tab" + (name === "book" ? " active" : "");
            btnPass.className = "tab" + (name === "pass" ? " active" : "");
            btnAi.className = "tab" + (name === "ai" ? " active" : "");
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

        {render_pass_js(APARTMENT_LISTING['title'])}

        async function submitBooking() {{
            bookErr.textContent = ""; gatePassCard.style.display = "none";
            const payload = {{
                unit_name: unitName.value,
                full_name: fullName.value.trim(), email: email.value.trim(), phone: phone.value.trim(),
                visitor_state: visitorState.value, visitor_address: visitorAddress.value.trim(),
                id_type: idType.value, id_number: idNumber.value.trim(), guests: parseInt(guests.value),
                visit_date: visitDate.value, visit_time: visitTime.value,
                website_url: websiteUrl.value, math_a: mathA, math_b: mathB, math_answer: parseInt(mathAnswer.value || "0")
            }};
            const res = await fetch("/api/book", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify(payload)
            }});
            const d = await res.json();
            refreshMathChallenge();
            if (!res.ok) return bookErr.textContent = formatApiError(d, "Booking failed");
            idNumber.value = "";
            renderPassSafe(gatePassCard, d, false);
            loadSlots();
        }}

        async function findPass() {{
            lookupMsg.textContent = ""; foundPassBox.style.display = "none";
            const res = await fetch("/api/pass", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ booking_code: lookupCode.value.trim(), phone_or_email: lookupContact.value.trim() }})
            }});
            const d = await res.json();
            if (!res.ok) return lookupMsg.textContent = formatApiError(d, "Booking not found");
            renderPassSafe(foundPassBox, d, true);
        }}

        async function cancelPass(code) {{
            const res = await fetch("/api/cancel", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ booking_code: code, phone_or_email: lookupContact.value.trim() }})
            }});
            if (res.ok) {{ foundPassBox.style.display = "none"; lookupMsg.className = "ok"; lookupMsg.textContent = "✅ Inspection cancelled."; loadSlots(); }}
        }}

        async function askAiAssistant() {{
            aiErr.textContent = ""; aiReplyBox.style.display = "none";
            const res = await fetch("/api/ask-ai", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ question: aiQuestion.value.trim() }})
            }});
            const d = await res.json();
            if (!res.ok) return aiErr.textContent = formatApiError(d, "Unable to answer right now");
            aiReplyBox.textContent = d.answer;
            aiReplyBox.style.display = "block";
        }}

        async function loadHostInspections() {{
            hostMsg.textContent = ""; hostList.replaceChildren(); auditList.replaceChildren();
            const res = await fetch("/api/host/inspections", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ passcode: hostPasscode.value }})
            }});
            const d = await res.json();
            if (!res.ok) return hostMsg.textContent = formatApiError(d, "Access denied");
            if (!d.inspections.length) hostMsg.textContent = "No inspections scheduled yet.";
            for (const v of d.inspections) {{
                const card = Object.assign(document.createElement("div"), {{ className: "host-item" }});
                const rows = [
                    `${{v.booking_code}} • PIN: ${{v.gate_pin}} [${{v.status}}]`,
                    `Unit: ${{v.unit_name}}`,
                    `Visitor: ${{v.full_name}} (${{v.guests}} guest(s))`,
                    `Visitor Phone: ${{v.phone}}`,
                    `Visitor Email: ${{v.email}}`,
                    `Verified ID: ${{v.id_type}}`,
                    `Home Address: ${{v.visitor_address}}, ${{v.visitor_state}}`,
                    `Schedule: ${{v.visit_date}} at ${{v.visit_time}}`
                ];
                for (const line of rows) card.appendChild(Object.assign(document.createElement("div"), {{ textContent: line }}));
                if (v.status === "CONFIRMED") {{
                    card.appendChild(Object.assign(document.createElement("button"), {{ style: "padding:8px;margin-top:8px;", textContent: "✅ Check In at Gate", onclick: () => checkInVisitor(v.booking_code) }}));
                }}
                hostList.appendChild(card);
            }}
            for (const a of (d.audit_logs || [])) {{
                const row = Object.assign(document.createElement("div"), {{ className: "host-item", style: `border-color:${{a.severity==='ALERT'?'#be123c':'#1e3a8a'}};` }});
                row.textContent = `[${{a.time}}] ${{a.event}}`;
                auditList.appendChild(row);
            }}
        }}

        async function checkInVisitor(code) {{
            const res = await fetch("/api/host/checkin", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ passcode: hostPasscode.value, booking_code: code }})
            }});
            if (res.ok) loadHostInspections();
        }}

        refreshMathChallenge();
        loadSlots();
    </script>
    """
