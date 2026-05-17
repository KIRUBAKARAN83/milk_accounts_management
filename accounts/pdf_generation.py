from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
from io import BytesIO
from decimal import Decimal


def generate_bill_pdf(
    customer,
    entries,
    total_ml,
    total_litres,
    total_amount,
    price_per_litre,
    year=None,
    month=None
):
    """
    RULE (FINAL):
    - customer.balance_amount = unpaid till previous month
    - total_amount = current billing amount
    - total payable = previous balance + current billing amount
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading3'],
        fontSize=11,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )

    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontSize=9,   # slightly smaller to save space
        spaceAfter=4
    )

    elements = []

    # ---------------- TITLE ----------------
    elements.append(Paragraph("Milk Billing Invoice", title_style))

    # ---------------- BILLING PERIOD ----------------
    if entries:
        start_date = min(e.date for e in entries)
        end_date = max(e.date for e in entries)

        if start_date.month == end_date.month and start_date.year == end_date.year:
            period_text = f"Billing Period: {start_date.strftime('%B %Y')}"
        else:
            period_text = (
                f"Billing Period: "
                f"{start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}"
            )
    else:
        period_text = "Billing Period: No entries"

    elements.append(
        Paragraph(
            f"{period_text}<br/>Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M')}",
            normal_style
        )
    )

    elements.append(Spacer(1, 0.15 * inch))

    # ---------------- CUSTOMER SUMMARY ----------------
    previous_balance = Decimal(customer.balance_amount or 0)
    current_amount = Decimal(total_amount)
    total_payable = previous_balance + current_amount

    elements.append(Paragraph("Customer Summary", heading_style))

    summary_table = Table(
        [
            ["Customer Name", customer.name or "N/A"],
            ["Previous Balance (Unpaid)", f"₹ {previous_balance:.2f}"],
            ["Total Litres", f"{total_litres:.2f} L"],
            ["Current Month Amount", f"₹ {current_amount:.2f}"],
            ["Total Payable", f"₹ {total_payable:.2f}"],
        ],
        colWidths=[3 * inch, 2 * inch]
    )

    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.2 * inch))

    # ---------------- ENTRIES TABLE ----------------
    elements.append(Paragraph("Milk Entries", heading_style))

    table_data = [
        ["Date", "Quantity (ml)", "Litres", "Rate (₹)", "Amount (₹)"]
    ]

    if entries:
        for entry in entries:
            table_data.append([
                entry.date.strftime('%d-%m-%Y'),
                str(entry.quantity_ml),
                f"{entry.litres:.3f}",
                f"{Decimal(price_per_litre):.2f}",
                f"{entry.amount:.2f}",
            ])
    else:
        table_data.append(["No entries", "", "", "", ""])

    # Add totals row
    table_data.append([
        "TOTAL",
        str(total_ml),
        f"{total_litres:.2f}",
        f"{Decimal(price_per_litre):.2f}",
        f"{current_amount:.2f}",
    ])

    # --- Dynamic row height calculation ---
    # Available height for entries table ≈ 6.5 inches (A4 minus margins and summary)
    available_height = 6.5 * inch
    row_count = len(table_data)
    row_height = available_height / row_count

    entries_table = Table(
        table_data,
        colWidths=[1.0*inch, 1.0*inch, 1.0*inch, 1.0*inch, 1.2*inch],
        rowHeights=[row_height] * row_count
    )

    entries_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # compact font
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
    ]))

    elements.append(entries_table)
    elements.append(Spacer(1, 0.2 * inch))

    # ---------------- FOOTER ----------------
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    )

    elements.append(
        Paragraph("Thank you for your business.", footer_style)
    )

    doc.build(elements)
    buffer.seek(0)
    return buffer