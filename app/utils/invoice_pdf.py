"""Generate branded invoice and receipt PDFs using fpdf2."""
import os
from datetime import datetime, timezone
from fpdf import FPDF, XPos, YPos


# Brand colours (RGB)
GOLD = (201, 168, 76)
DARK = (17, 24, 39)
MID  = (55, 65, 81)
LIGHT = (249, 250, 251)
BORDER = (229, 231, 235)
WHITE = (255, 255, 255)


def _hex(r, g, b):
    return r, g, b


class InvoicePDF(FPDF):
    def __init__(self, doc_type='INVOICE'):
        super().__init__()
        self.doc_type = doc_type  # 'INVOICE' or 'RECEIPT'

    def header(self):
        # Gold top bar
        self.set_fill_color(*GOLD)
        self.rect(0, 0, 210, 4, 'F')

        self.set_y(10)
        # Left: name
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(*DARK)
        self.cell(100, 10, 'LAGO BRIAN', new_x=XPos.RIGHT, new_y=YPos.TOP)

        # Right: document type
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(*GOLD)
        self.cell(100, 10, self.doc_type, align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_font('Helvetica', '', 9)
        self.set_text_color(*MID)
        self.cell(100, 5, 'lagobrian.com', new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.cell(100, 5, 'lagobrian@outlook.com', align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Gold separator line
        self.ln(4)
        self.set_draw_color(*GOLD)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-20)
        self.set_draw_color(*GOLD)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(*MID)
        self.cell(0, 5, 'Lago Brian · lagobrian.com · lagobrian@outlook.com', align='C',
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font('Helvetica', '', 7)
        self.cell(0, 4, f'Page {self.page_no()}', align='C')

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*GOLD)
        self.set_fill_color(*DARK)
        self.cell(0, 7, f'  {title.upper()}', fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def kv_row(self, label, value, bold_value=False):
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*MID)
        self.cell(55, 6, label + ':', new_x=XPos.RIGHT, new_y=YPos.TOP)
        if bold_value:
            self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*DARK)
        self.multi_cell(0, 6, str(value) if value else '—')

    def two_col_row(self, l1, v1, l2, v2):
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*MID)
        self.cell(55, 6, l1 + ':', new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_text_color(*DARK)
        self.cell(45, 6, str(v1) if v1 else '—', new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_text_color(*MID)
        self.cell(30, 6, l2 + ':', new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_text_color(*DARK)
        self.cell(0, 6, str(v2) if v2 else '—', new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _fmt_amount(amount):
    if not amount:
        return '—'
    return f'${amount:,.2f}'


def _fmt_date(dt):
    if not dt:
        return '—'
    if hasattr(dt, 'strftime'):
        return dt.strftime('%B %d, %Y')
    return str(dt)


def generate_invoice(hr, invoice_number, output_path):
    """Generate invoice PDF for a hire request."""
    pdf = InvoicePDF('INVOICE')
    pdf.add_page()

    # ── Meta info ──────────────────────────────────────────────────
    pdf.section_title('Invoice Details')
    pdf.two_col_row('Invoice #', invoice_number,
                    'Date', _fmt_date(datetime.now(timezone.utc)))
    pdf.two_col_row('Status', 'UNPAID',
                    'Due', _fmt_date(hr.deadline) if hr.deadline else 'Upon agreement')
    pdf.ln(4)

    # ── Parties ────────────────────────────────────────────────────
    y = pdf.get_y()
    pdf.section_title('From')
    pdf.kv_row('Name', 'Lago Brian')
    pdf.kv_row('Email', 'lagobrian@outlook.com')
    pdf.kv_row('Website', 'lagobrian.com')
    pdf.ln(2)

    pdf.section_title('Bill To')
    if not hr.is_anonymous:
        pdf.kv_row('Name', hr.client_name)
    billing_email = hr.invoice_email if hr.invoice_email else hr.client_email
    pdf.kv_row('Email', billing_email)
    if hr.client_phone:
        pdf.kv_row('Phone', hr.client_phone)
    pdf.ln(4)

    # ── Project ────────────────────────────────────────────────────
    pdf.section_title('Project')
    pdf.kv_row('Title', hr.project_title, bold_value=True)
    if hr.project_description:
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(*MID)
        pdf.cell(55, 6, 'Description:', new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_text_color(*DARK)
        pdf.multi_cell(0, 6, hr.project_description[:400] + ('...' if len(hr.project_description) > 400 else ''))
    if hr.deliverables:
        pdf.kv_row('Deliverables', hr.deliverables[:300])
    if hr.deadline:
        pdf.kv_row('Deadline', _fmt_date(hr.deadline))
    pdf.ln(4)

    # ── Payment ────────────────────────────────────────────────────
    pdf.section_title('Payment')
    pdf.two_col_row('Method', (hr.payment_method or '—').title(),
                    'Pricing', (hr.pricing_type or '—').title())
    pdf.kv_row('Schedule', (hr.payment_schedule or '—').replace('_', ' ').title())
    pdf.ln(3)

    # Payment table
    pdf.set_fill_color(*DARK)
    pdf.set_text_color(*WHITE)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(120, 8, '  Description', fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(0, 8, 'Amount', align='R', fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_fill_color(*LIGHT)
    pdf.set_text_color(*DARK)
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(120, 7, f'  {hr.project_title[:60]}', fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(0, 7, _fmt_amount(hr.total_amount), align='R', fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if hr.deposit_amount and hr.payment_schedule in ('deposit', 'installments'):
        pdf.set_fill_color(*WHITE)
        pdf.cell(120, 7, '  Deposit / First Payment', fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(0, 7, _fmt_amount(hr.deposit_amount), align='R', fill=True,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_fill_color(*LIGHT)
        remaining = (hr.total_amount or 0) - (hr.deposit_amount or 0)
        pdf.cell(120, 7, '  Remaining Balance', fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(0, 7, _fmt_amount(remaining), align='R', fill=True,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Total row
    pdf.set_fill_color(*GOLD)
    pdf.set_text_color(*DARK)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(120, 9, '  TOTAL', fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(0, 9, _fmt_amount(hr.total_amount), align='R', fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # ── Terms & Conditions ──────────────────────────────────────────
    _add_terms(pdf, hr)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)


def generate_receipt(hr, invoice_number, receipt_number, output_path, confirmed_at=None):
    """Generate receipt PDF once payment is confirmed."""
    pdf = InvoicePDF('RECEIPT')
    pdf.add_page()

    # ── Meta ───────────────────────────────────────────────────────
    pdf.section_title('Receipt Details')
    pdf.two_col_row('Receipt #', receipt_number,
                    'Date', _fmt_date(confirmed_at or datetime.now(timezone.utc)))
    pdf.two_col_row('Invoice Ref', invoice_number,
                    'Status', 'PAID')
    pdf.ln(4)

    # ── Parties ────────────────────────────────────────────────────
    pdf.section_title('From')
    pdf.kv_row('Name', 'Lago Brian')
    pdf.kv_row('Email', 'lagobrian@outlook.com')
    pdf.kv_row('Website', 'lagobrian.com')
    pdf.ln(2)

    pdf.section_title('Receipt For')
    if not hr.is_anonymous:
        pdf.kv_row('Name', hr.client_name)
    billing_email = hr.invoice_email if hr.invoice_email else hr.client_email
    pdf.kv_row('Email', billing_email)
    pdf.ln(4)

    # ── Project ────────────────────────────────────────────────────
    pdf.section_title('Project')
    pdf.kv_row('Title', hr.project_title, bold_value=True)
    if hr.deadline:
        pdf.kv_row('Deadline', _fmt_date(hr.deadline))
    pdf.ln(4)

    # ── Payment confirmed ──────────────────────────────────────────
    pdf.section_title('Payment Received')
    pdf.two_col_row('Method', (hr.payment_method or '—').title(),
                    'Pricing', (hr.pricing_type or '—').title())
    pdf.ln(3)

    # Payment table
    pdf.set_fill_color(*DARK)
    pdf.set_text_color(*WHITE)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(120, 8, '  Description', fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(0, 8, 'Amount', align='R', fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_fill_color(*LIGHT)
    pdf.set_text_color(*DARK)
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(120, 7, f'  {hr.project_title[:60]}', fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(0, 7, _fmt_amount(hr.total_amount), align='R', fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Total
    pdf.set_fill_color(*GOLD)
    pdf.set_text_color(*DARK)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(120, 9, '  TOTAL PAID', fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(0, 9, _fmt_amount(hr.total_amount), align='R', fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Paid stamp
    pdf.set_font('Helvetica', 'B', 28)
    pdf.set_text_color(*GOLD)
    pdf.cell(0, 14, 'PAID', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # ── Terms ──────────────────────────────────────────────────────
    _add_terms(pdf, hr)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)


def _add_terms(pdf, hr):
    """Append T&C section."""
    pdf.section_title('Terms & Conditions')
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(*MID)

    terms = [
        ('1. Scope of Work', 'Services are delivered as described in the project brief and any written agreements. Changes in scope require written agreement and may affect pricing and timelines.'),
        ('2. Payment', 'Invoices are due as per the agreed schedule. Late payments may result in work suspension. A 50% deposit is required to begin work unless otherwise agreed in writing.'),
        ('3. Revisions', 'Up to two rounds of revisions are included. Additional revisions are billed at the agreed hourly rate.'),
        ('4. Intellectual Property', 'Full ownership of all deliverables is transferred to the client upon receipt of final payment. Lago Brian retains the right to list the project in the portfolio unless otherwise agreed.'),
        ('5. Confidentiality', f'{"A Non-Disclosure Agreement (NDA) was signed for this project. All information shared is treated as strictly confidential." if hr.nda_signed else "No NDA was signed for this project. Standard professional discretion applies."}'),
        ('6. Liability', 'Lago Brian is not liable for decisions made based on deliverables, or for losses arising from use of the work. Total liability is limited to the amount paid.'),
        ('7. Governing Law', 'This agreement is governed by the laws of Kenya. Disputes shall be resolved through good-faith negotiation before any formal proceedings.'),
        ('8. Communication', 'All project communications should be conducted via email. Response time is typically within 24 hours on business days.'),
    ]

    for title, body in terms:
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 5, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(*MID)
        pdf.multi_cell(0, 5, body)
        pdf.ln(1)

    # NDA status box
    pdf.ln(2)
    if hr.nda_signed:
        pdf.set_fill_color(34, 197, 94)  # green
    else:
        pdf.set_fill_color(*MID)
    pdf.set_text_color(*WHITE)
    pdf.set_font('Helvetica', 'B', 8)
    nda_text = 'NDA: SIGNED — This project is subject to a Non-Disclosure Agreement.' if hr.nda_signed else 'NDA: NOT SIGNED — No confidentiality agreement in place beyond standard T&C.'
    pdf.cell(0, 7, f'  {nda_text}', fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
