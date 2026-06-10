from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from datetime import date
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from app.database import get_db
from app.models.sales import Invoice, InvoiceItem, Customer
from app.models.purchase import PurchaseOrder, PurchaseOrderItem, Supplier
from app.models.accounting import Transaction
from app.core.security import require_any_role
from app.core.config import settings

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def build_pdf_invoice(invoice, customer) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle("Header", parent=styles["Heading1"], fontSize=24, textColor=colors.HexColor("#1e40af"), spaceAfter=4)
    story.append(Paragraph(settings.APP_NAME, header_style))
    story.append(Paragraph("Tax Invoice", ParagraphStyle("sub", fontSize=14, textColor=colors.gray)))
    story.append(Spacer(1, 0.3*inch))

    # Invoice details table
    inv_data = [
        ["Invoice Number:", invoice.invoice_number, "Invoice Date:", str(invoice.date)],
        ["Status:", invoice.status.upper(), "Due Date:", str(invoice.due_date or "N/A")],
    ]
    inv_table = Table(inv_data, colWidths=[2.5*cm*3, 4*cm, 3*cm, 4*cm])
    inv_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,0), (0,-1), colors.HexColor("#374151")),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(inv_table)
    story.append(Spacer(1, 0.2*inch))

    # Bill To
    bill_style = ParagraphStyle("BillHeader", fontSize=11, fontName="Helvetica-Bold", textColor=colors.HexColor("#1e40af"))
    story.append(Paragraph("Bill To:", bill_style))
    story.append(Paragraph(customer.name, styles["Normal"]))
    if customer.company:
        story.append(Paragraph(customer.company, styles["Normal"]))
    if customer.email:
        story.append(Paragraph(customer.email, styles["Normal"]))
    if customer.phone:
        story.append(Paragraph(customer.phone, styles["Normal"]))
    story.append(Spacer(1, 0.3*inch))

    # Items table
    headers = ["#", "Description", "Qty", "Unit Price", "Discount", "Tax", "Total"]
    table_data = [headers]
    for i, item in enumerate(invoice.items, 1):
        table_data.append([
            str(i),
            item.description,
            f"{item.quantity:.2f}",
            f"₹{item.unit_price:.2f}",
            f"{item.discount:.1f}%",
            f"{item.tax_rate:.1f}%",
            f"₹{item.total:.2f}",
        ])

    items_table = Table(table_data, colWidths=[0.5*cm*2, 7*cm, 2*cm, 3*cm, 2.5*cm, 2*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ALIGN", (2,0), (-1,-1), "RIGHT"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f3f4f6")]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.2*inch))

    # Totals
    totals_data = [
        ["", "Subtotal:", f"₹{invoice.subtotal:.2f}"],
        ["", "Discount:", f"-₹{invoice.discount:.2f}"],
        ["", "Tax:", f"₹{invoice.tax_amount:.2f}"],
        ["", "TOTAL:", f"₹{invoice.total:.2f}"],
        ["", "Paid:", f"₹{invoice.paid_amount:.2f}"],
        ["", "Balance Due:", f"₹{invoice.balance_due:.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[10*cm, 4*cm, 4*cm])
    totals_table.setStyle(TableStyle([
        ("FONTNAME", (1,0), (-1,-1), "Helvetica"),
        ("FONTNAME", (1,3), (-1,3), "Helvetica-Bold"),
        ("FONTNAME", (1,5), (-1,5), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("FONTSIZE", (1,3), (-1,3), 12),
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("TEXTCOLOR", (1,3), (-1,3), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (1,5), (-1,5), colors.HexColor("#dc2626")),
        ("LINEABOVE", (1,3), (-1,3), 1, colors.HexColor("#d1d5db")),
        ("LINEABOVE", (1,5), (-1,5), 1, colors.HexColor("#d1d5db")),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(totals_table)

    if invoice.notes:
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Notes:", ParagraphStyle("NotesH", fontName="Helvetica-Bold", fontSize=10)))
        story.append(Paragraph(invoice.notes, styles["Normal"]))

    story.append(Spacer(1, 0.5*inch))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d1d5db")))
    story.append(Paragraph(f"Generated by {settings.APP_NAME} • {date.today()}", ParagraphStyle("footer", fontSize=8, textColor=colors.gray, alignment=TA_CENTER)))

    doc.build(story)
    buffer.seek(0)
    return buffer


@router.get("/invoice/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()

    pdf_buffer = build_pdf_invoice(invoice, customer)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice-{invoice.invoice_number}.pdf"},
    )


@router.get("/financial-summary/pdf")
async def download_financial_summary_pdf(
    year: int = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    from sqlalchemy import extract, func
    year = year or date.today().year

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(settings.APP_NAME, ParagraphStyle("H", fontSize=22, textColor=colors.HexColor("#1e40af"))))
    story.append(Paragraph(f"Financial Summary — {year}", styles["Heading2"]))
    story.append(Spacer(1, 0.3*inch))

    income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == "income", extract("year", Transaction.date) == year
    ).scalar() or 0

    expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == "expense", extract("year", Transaction.date) == year
    ).scalar() or 0

    summary_data = [
        ["Metric", "Amount"],
        ["Total Income", f"₹{income:,.2f}"],
        ["Total Expenses", f"₹{expense:,.2f}"],
        ["Net Profit / (Loss)", f"₹{income - expense:,.2f}"],
    ]
    t = Table(summary_data, colWidths=[10*cm, 7*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,3), (-1,3), "Helvetica-Bold"),
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f3f4f6")]),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3*inch))

    # Monthly breakdown
    monthly = db.query(
        extract("month", Transaction.date).label("month"),
        Transaction.type,
        func.sum(Transaction.amount).label("total"),
    ).filter(extract("year", Transaction.date) == year).group_by(
        extract("month", Transaction.date), Transaction.type
    ).order_by(extract("month", Transaction.date)).all()

    months_map = {}
    for row in monthly:
        m = int(row.month)
        if m not in months_map:
            months_map[m] = {"income": 0.0, "expense": 0.0}
        months_map[m][row.type] = float(row.total)

    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    monthly_data = [["Month", "Income", "Expense", "Net"]]
    for m in range(1, 13):
        d = months_map.get(m, {"income": 0, "expense": 0})
        monthly_data.append([
            month_names[m-1],
            f"₹{d['income']:,.2f}",
            f"₹{d['expense']:,.2f}",
            f"₹{d['income'] - d['expense']:,.2f}",
        ])

    mt = Table(monthly_data, colWidths=[4*cm, 5*cm, 5*cm, 5*cm])
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#374151")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f9fafb")]),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(Paragraph("Monthly Breakdown", styles["Heading3"]))
    story.append(mt)

    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=financial-summary-{year}.pdf"},
    )
