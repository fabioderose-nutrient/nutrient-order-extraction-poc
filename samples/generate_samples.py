"""Generate the sample order confirmations used by the demo.

Every company, address and part number below is fictitious.

    pip install -r samples/requirements.txt
    python samples/generate_samples.py

Writes samples/order-confirmation-1.pdf to samples/order-confirmation-3.pdf. The three layouts use
different labels, date formats and table styles, like order confirmations from different suppliers.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = Path(__file__).resolve().parent
CUSTOMER = ["Pinecrest Machine Works Ltd.", "Attn. Purchasing", "14 Mill Lane", "Derby DE1 3AB", "United Kingdom"]

SAMPLES = [
    {
        "file": "order-confirmation-1.pdf",
        "pagesize": A4,
        "supplier": "Ashford Bearings Ltd.",
        "supplier_line": "Ashford Bearings Ltd. | 2 Canal Street | Sheffield S1 4QR | United Kingdom",
        "title": "Order Confirmation",
        "meta": [
            ("Order confirmation no.", "OC-2026-04711"),
            ("Date", "02/10/2026"),
            ("Customer no.", "10234"),
            ("Your order", "PO-88120 of 28/09/2026"),
            ("Contact", "Sales office, +44 114 000 0000"),
        ],
        "intro": "Thank you for your order. We confirm delivery under our general terms of sale:",
        "columns": ("Pos.", "Part no.", "Description", "Qty", "Unit", "Unit price GBP", "Total GBP"),
        "widths": (12, 26, 66, 14, 12, 22, 22),
        "rows": [
            ("001", "AB-4711-20", "Deep groove ball bearing 6204-2RS<br/>Your part no.: PMW-6204<br/>"
             "Delivery date: 20/10/2026", "50", "pcs", "3.45", "172.50"),
            ("002", "AB-5820-01", "Timing belt HTD 8M-1200-30<br/>Your part no.: PMW-1200<br/>"
             "Delivery date: 20/10/2026", "12", "pcs", "28.90", "346.80"),
            ("003", "AB-7310-05", "Pillow block bearing unit UCP205,<br/>cast iron housing<br/>"
             "Delivery date: 27/10/2026", "8", "pcs", "19.75", "158.00"),
        ],
        "grid": False,
        "totals": [("Net total", "677.30"), ("VAT 20%", "135.46"), ("Total", "812.76")],
        "footer": "Payment terms: 30 days net. Delivery: FCA Sheffield.",
    },
    {
        "file": "order-confirmation-2.pdf",
        "pagesize": LETTER,
        "supplier": "Crestline Fasteners Inc.",
        "supplier_line": "Crestline Fasteners Inc. | 900 Industrial Parkway | Dayton, OH 45404 | USA",
        "title": "Sales Order Acknowledgement",
        "meta": [
            ("Acknowledgement No.", "SOA-558213"),
            ("Acknowledgement Date", "October 5, 2026"),
            ("Customer Number", "C-77031"),
            ("Customer PO", "PO-88145"),
            ("Ship Via", "Ground freight"),
        ],
        "intro": "We acknowledge your purchase order. Prices are per 100 pieces where stated.",
        "columns": ("Line", "Item", "Description", "Quantity", "UoM", "Price", "Extended"),
        "widths": (12, 28, 62, 18, 12, 20, 22),
        "rows": [
            ("10", "CF-M8X30-A2", "Hex head cap screw M8 x 30, stainless A2<br/>Customer part no.: PMW-0830<br/>"
             "Delivery week: CW 42/2026", "1,000", "pcs", "12.40 /100", "124.00"),
            ("20", "CF-WSH-M8", "Flat washer M8, stainless A2<br/>Customer part no.: PMW-0008<br/>"
             "Delivery week: CW 42/2026", "1,000", "pcs", "2.10 /100", "21.00"),
            ("30", "CF-NUT-M8-NL", "Nylon insert lock nut M8<br/>Delivery week: CW 43/2026", "500", "pcs",
             "6.80 /100", "34.00"),
            ("40", "CF-KIT-SVC", "Assortment case, metric service kit<br/>Customer part no.: PMW-KIT1<br/>"
             "Delivery week: CW 44/2026", "2", "ea", "1,234.50", "2,469.00"),
        ],
        "grid": False,
        "totals": [("Merchandise total", "2,648.00"), ("Freight", "45.00"), ("Order total USD", "2,693.00")],
        "footer": "Terms: Net 45 days. All items ship from Dayton, OH.",
    },
    {
        "file": "order-confirmation-3.pdf",
        "pagesize": A4,
        "supplier": "Holloway Drive Systems Ltd.",
        "supplier_line": "Holloway Drive Systems Ltd. | Unit 5, Riverside Estate | Leeds LS10 1AA | United Kingdom",
        "title": "Order Acknowledgement",
        "meta": [
            ("Our reference", "HDS/OA/31877"),
            ("Document date", "07.10.2026"),
            ("Account no.", "PMW001"),
            ("Your purchase order", "PO-88152 dated 01.10.2026"),
        ],
        "intro": "Delivery dates are given per line. Please check this acknowledgement and report differences "
                 "within 3 working days.",
        "columns": ("Item", "Article", "Description", "Qty", "Unit", "Price each", "Line value", "Delivery"),
        "widths": (11, 24, 52, 12, 11, 20, 22, 20),
        "rows": [
            ("1", "HD-GM-0750", "Geared motor 0.75 kW, 1:20, IE3<br/>Customer article: PMW-GM075", "2", "pcs",
             "486.00", "972.00", "16.10.2026"),
            ("2", "HD-CPL-28", "Jaw coupling 28 mm, complete", "4", "pcs", "38.20", "152.80", "16.10.2026"),
            ("3", "HD-CHN-08B", "Roller chain 08B-1, 5 m reel", "1.5", "m", "14.60", "21.90", "23.10.2026"),
        ],
        "grid": True,
        "totals": [("Goods value", "1,146.70"), ("Packing", "12.00"), ("Net value", "1,158.70")],
        "footer": "All prices in GBP, excluding VAT. Delivery terms: DAP Derby.",
    },
]


def build(spec: dict, path: Path) -> None:
    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8.5, leading=11)
    tiny = ParagraphStyle("tiny", parent=small, fontSize=7, leading=9, textColor=colors.grey)
    title = ParagraphStyle("title", parent=styles["Heading1"], fontSize=15, spaceAfter=4)
    right = ParagraphStyle("right", parent=small, alignment=TA_RIGHT)
    doc = SimpleDocTemplate(str(path), pagesize=spec["pagesize"], leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm, title=spec["file"],
                            author="Sample generator", invariant=1)
    width = spec["pagesize"][0] - 36 * mm
    story = [Paragraph(f"<b>{spec['supplier']}</b>", styles["Heading2"]), Paragraph(spec["supplier_line"], tiny),
             Spacer(1, 6 * mm)]
    meta = "<br/>".join(f"{k}: <b>{v}</b>" for k, v in spec["meta"])
    head = Table([[Paragraph("<br/>".join(CUSTOMER), small), Paragraph(meta, small)]],
                 colWidths=[width * 0.5, width * 0.5])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [head, Spacer(1, 8 * mm), Paragraph(spec["title"], title), Paragraph(spec["intro"], small),
              Spacer(1, 4 * mm)]

    rows = [[Paragraph(f"<b>{c}</b>", small) for c in spec["columns"]]]
    rows += [[Paragraph(str(c), small) for c in row] for row in spec["rows"]]
    total_units = sum(spec["widths"])
    table = Table(rows, colWidths=[width * w / total_units for w in spec["widths"]], repeatRows=1)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
             ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.black)]
    if spec["grid"]:
        style.append(("GRID", (0, 0), (-1, -1), 0.3, colors.grey))
    table.setStyle(TableStyle(style))
    story += [table, Spacer(1, 6 * mm)]

    totals = Table([[Paragraph(k, right), Paragraph(f"<b>{v}</b>", right)] for k, v in spec["totals"]],
                   colWidths=[width * 0.8, width * 0.2])
    story += [totals, Spacer(1, 8 * mm), Paragraph(spec["footer"], small), Spacer(1, 4 * mm),
              Paragraph("Sample document generated for a demo. All names and numbers are fictitious.", tiny)]
    doc.build(story)


def main() -> None:
    for spec in SAMPLES:
        build(spec, HERE / spec["file"])
        print("wrote", spec["file"])


if __name__ == "__main__":
    main()
