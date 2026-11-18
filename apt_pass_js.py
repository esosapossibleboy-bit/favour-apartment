def render_pass_js(apt_title: str) -> str:
    return f"""
        async function fetchPassPdfBlob(code, contact) {{
            const res = await fetch("/api/pass/pdf", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ booking_code: code, phone_or_email: contact }})
            }});
            if (!res.ok) return null;
            return await res.blob();
        }}

        async function sharePassWhatsApp(d) {{
            const blob = await fetchPassPdfBlob(d.booking_code, d.phone);
            if (!blob) return alert("Could not generate PDF pass right now.");

            const filename = `${{d.booking_code}}_Pass.pdf`;
            const pdfFile = new File([blob], filename, {{ type: "application/pdf" }});

            if (navigator.canShare && navigator.canShare({{ files: [pdfFile] }})) {{
                try {{
                    await navigator.share({{
                        files: [pdfFile],
                        title: {apt_title!r} + " Inspection Pass",
                        text: `Official Inspection Pass (${{d.booking_code}}) — Gate PIN: ${{d.gate_pin}}`
                    }});
                    return;
                }} catch (err) {{
                    if (err && err.name === "AbortError") return;
                }}
            }}

            const url = URL.createObjectURL(blob);
            const a = Object.assign(document.createElement("a"), {{ href: url, download: filename }});
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);

            const waUrl = new URL("https://wa.me");
            waUrl.searchParams.set("text", `🏢 *${{{apt_title!r}}} Inspection Pass (${{d.booking_code}})* — Please see my attached PDF pass (${{filename}}).`);
            window.open(waUrl.toString(), "_blank", "noopener,noreferrer");
        }}

        async function downloadPassPDF(code, contact) {{
            const blob = await fetchPassPdfBlob(code, contact);
            if (!blob) return alert("Could not download PDF right now.");
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
            const emailAlert = Object.assign(document.createElement("div"), {{ textContent: `📩 Email Alert: ${{d.email}}`, style: "font-size:0.8rem;color:#fde68a;margin-top:4px;" }});
            const smsAlert = Object.assign(document.createElement("div"), {{ textContent: `📱 Phone Alert: ${{d.phone}}`, style: "font-size:0.8rem;color:#fde68a;margin-top:2px;" }});
            const body = Object.assign(document.createElement("div"), {{ style: "margin-top:8px;font-size:0.9rem;line-height:1.6;" }});
            const lines = [
                `Property: {apt_title} — ${{d.unit_name}}`,
                `Booking Code: ${{d.booking_code}}`,
                `Gate Security PIN: ${{d.gate_pin}}`,
                `Visitor: ${{d.full_name}} (${{d.guests}} guest(s))`,
                `Visitor Email: ${{d.email}}`,
                `Visitor Phone: ${{d.phone}}`,
                `Verified ID: ${{d.id_type}}`,
                `Date & Time: ${{d.visit_date}} at ${{d.visit_time}}`,
                `Exact House Address: ${{d.exact_address}}`,
                `Host Contact: ${{d.host_phone}}`
            ];
            for (const line of lines) {{
                body.appendChild(Object.assign(document.createElement("div"), {{ textContent: line }}));
            }}
            const pdfBtn = Object.assign(document.createElement("button"), {{ className: "btn-dark", textContent: "📄 Download Appointment PDF", onclick: () => downloadPassPDF(d.booking_code, d.phone) }});
            const waBtn = Object.assign(document.createElement("button"), {{ className: "btn-wa", textContent: "📲 Share PDF Pass on WhatsApp", onclick: () => sharePassWhatsApp(d) }});
            targetBox.append(head, emailAlert, smsAlert, body, pdfBtn, waBtn);
            if (allowCancel && d.status === "CONFIRMED") {{
                targetBox.appendChild(Object.assign(document.createElement("button"), {{ className: "btn-danger", textContent: "❌ Cancel This Inspection", onclick: () => cancelPass(d.booking_code) }}));
            }}
            targetBox.style.display = "block";
        }}
    """
