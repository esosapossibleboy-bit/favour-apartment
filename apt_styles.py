def render_apt_head(title: str) -> str:
    return f"""<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title} — Powered by ESOSATECH</title>
    <link rel="icon" type="image/jpeg" href="/esosatech-logo.jpg" />
    <style>
        * {{ box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; }}
        body {{ margin: 0; background: #090d1a; color: #f8fafc; }}
        .bar {{ background: linear-gradient(135deg, #1e1b4b, #312e81); padding: 14px 18px; border-bottom: 1px solid #3730a3; display: flex; justify-content: space-between; align-items: center; gap: 10px; }}
        .brand-row {{ display: flex; align-items: center; gap: 10px; }}
        .brand-logo {{ width: 42px; height: 42px; border-radius: 10px; object-fit: cover; border: 1.5px solid #fbbf24; background: #ffffff; }}
        .wrap {{ max-width: 520px; margin: 0 auto; padding: 16px; }}
        .hero {{ background: linear-gradient(135deg, #312e81, #0f172a); border: 1px solid #4338ca; border-radius: 18px; padding: 18px; margin-bottom: 14px; }}
        .badge {{ display: inline-block; background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.35); padding: 4px 10px; border-radius: 999px; font-size: 0.72rem; font-weight: 700; white-space: nowrap; }}
        .room-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 12px; }}
        .room-card {{ background: rgba(15, 23, 42, 0.85); border: 1px solid #3730a3; border-radius: 12px; padding: 10px 8px; text-align: center; font-size: 0.78rem; }}
        .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 16px; padding: 16px; margin-bottom: 14px; }}
        input, select {{ width: 100%; padding: 11px 12px; margin-top: 8px; border-radius: 10px; border: 1px solid #374151; background: #0b1021; color: #f8fafc; font-size: 0.94rem; }}
        button {{ width: 100%; padding: 12px; margin-top: 12px; border: none; border-radius: 12px; font-weight: 700; font-size: 0.95rem; cursor: pointer; background: linear-gradient(135deg, #f59e0b, #d97706); color: #090d1a; }}
        .btn-dark {{ background: #1f2937; color: #f8fafc; border: 1px solid #374151; }}
        .btn-wa {{ background: #16a34a; color: #ffffff; }}
        .btn-danger {{ background: #7f1d1d; color: #fecaca; }}
        .tabs {{ display: flex; gap: 5px; margin-bottom: 12px; }}
        .tab {{ flex: 1; margin: 0; padding: 10px 4px; font-size: 0.8rem; background: #1f2937; color: #cbd5e1; }}
        .tab.active {{ background: #4f46e5; color: white; }}
        .pass-box {{ background: #052e16; border: 1px solid #16a34a; border-radius: 14px; padding: 14px; margin-top: 12px; }}
        .ai-box {{ background: #0b1021; border: 1px solid #4338ca; border-radius: 12px; padding: 12px; margin-top: 12px; font-size: 0.9rem; line-height: 1.55; color: #e2e8f0; }}
        .host-item {{ background: #0b1021; border: 1px solid #2a3963; border-radius: 12px; padding: 12px; margin-top: 10px; font-size: 0.85rem; line-height: 1.5; }}
        .footer-brand {{ display: flex; align-items: center; justify-content: center; gap: 8px; padding: 14px 8px 24px; color: #94a3b8; font-size: 0.78rem; }}
        .err {{ color: #fb7185; font-size: 0.86rem; margin-top: 8px; }}
        .ok {{ color: #34d399; font-size: 0.86rem; margin-top: 8px; }}
    </style>
</head>"""
