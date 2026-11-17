def render_pass_js(apt_title: str) -> str:
    return f"""
        function sharePassWhatsApp(d) {{
            const text = `🏢 *{apt_title} — Inspection Pass*\\n` +
                `• *Booking Code:* ${{d.booking_code}}\\n` +
                `• *Gate PIN:* ${{d.gate_pin}}\\n` +
                `• *Unit:* ${{d.unit_name}}\\n` +
                `• *Visitor:* ${{d.full_name}}\\n` +
                `• *Verified ID:* ${{d.id_type}}\\n` +
                `• *Date & Time:* ${{d.visit_date}} at ${{d.visit_time}}\\n` +
                `• *Address:* ${{d.exact_address}}`;
            window.open("https://wa.me" + encodeURIComponent(text), "_blank");
        }}

        async function downloadPassPDF(code, contact) {{
            const res = await fetch("/api/pass/pdf", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ booking_code: code, phone_or_email: contact }})
            }});
            if (!res.ok) return alert("Could not download PDF right now.");
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = Object.assign(document.createElement("a"), {{ href: url, download: `${{code}}_Pass.pdf` }});
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        }}

        function renderPassSafe(targetBox, d, allowCancel = false) {{
            targetBox.replaceChildren();
            const head = Object.assign(document.createElement("div"), {{ textContent: "✅ CONFIRMED INSPECTION PASS", style: "font-weight:800;color:#4ade80;font-size:1.05rem;" }});
            const alertNote = Object.assign(document.createElement("div"), {{ textContent: `📩 Email & 📱 SMS alerts dispatched to ${{d.email}} & ${{d.phone}}`, style: "font-size:0.8rem;color:#fde68a;margin-top:4px;" }});
            const body = Object.assign(document.createElement("div"), {{ style: "margin-top:8px;font-size:0.9rem;line-height:1.6;" }});
            const lines = [
                `Property: {apt_title} — ${{d.unit_name}}`,
                `Booking Code: ${{d.booking_code}}`,
                `Gate Security PIN: ${{d.gate_pin}}`,
                `Visitor: ${{d.full_name}} (${{d.guests}} guest(s))`,
                `Verified ID: ${{d.id_type}}`,
                `Date & Time: ${{d.visit_date}} at ${{d.visit_time}}`,
                `Exact House Address: ${{d.exact_address}}`,
                `Host Contact: ${{d.host_phone}}`
            ];
            for (const line of lines) {{
                body.appendChild(Object.assign(document.createElement("div"), {{ textContent: line }}));
            }}
            const pdfBtn = Object.assign(document.createElement("button"), {{ className: "btn-dark", textContent: "📄 Download Appointment PDF", onclick: () => downloadPassPDF(d.booking_code, d.phone) }});
            const waBtn = Object.assign(document.createElement("button"), {{ className: "btn-wa", textContent: "📲 Save / Share Pass on WhatsApp", onclick: () => sharePassWhatsApp(d) }});
            targetBox.append(head, alertNote, body, pdfBtn, waBtn);
            if (allowCancel && d.status === "CONFIRMED") {{
                targetBox.appendChild(Object.assign(document.createElement("button"), {{ className: "btn-danger", textContent: "❌ Cancel This Inspection", onclick: () => cancelPass(d.booking_code) }}));
            }}
            targetBox.style.display = "block";
        }}
    """
