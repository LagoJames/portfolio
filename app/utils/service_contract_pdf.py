"""Generate a standard client services agreement PDF using fpdf2."""
from fpdf import FPDF, XPos, YPos
from datetime import datetime, timezone

GOLD = (201, 168, 76)
DARK = (17, 24, 39)
MID = (55, 65, 81)


class ServicesAgreementPDF(FPDF):
    def header(self):
        self.set_fill_color(*GOLD)
        self.rect(0, 0, 210, 4, 'F')
        self.set_y(10)
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(*DARK)
        self.cell(0, 10, 'LAGO BRIAN', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*MID)
        self.cell(0, 5, 'Client Services Agreement', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)
        self.set_draw_color(*GOLD)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-18)
        self.set_draw_color(*GOLD)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(*MID)
        self.cell(0, 4, 'Lago Brian | lagobrian.com | lagobrian@outlook.com', align='C')


def generate_services_agreement(output_path):
    pdf = ServicesAgreementPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 8, 'STANDARD CLIENT SERVICES AGREEMENT', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*MID)
    pdf.multi_cell(
        0,
        5,
        (
            f'Document generated: {datetime.now(timezone.utc).strftime("%B %d, %Y")}. '
            'This template is intended for freelance professional services governed by Kenyan law. '
            'It is structured as a contract for services and not as a contract of service or employment agreement.'
        ),
    )
    pdf.ln(5)

    clauses = [
        (
            'Parties',
            'This Client Services Agreement ("Agreement") is between Lago Brian, an independent freelance financial engineer and data scientist based in Nairobi, Kenya ("Service Provider"), and the undersigned client ("Client").',
        ),
        (
            'Nature of Relationship',
            'This Agreement is a contract for services. It does not create an employer-employee relationship, partnership, joint venture, agency, or exclusive arrangement. The Service Provider controls the manner and means of performing the work, subject to the agreed deliverables, and remains responsible for his own taxes, statutory remittances, tools, and work methods.',
        ),
        (
            'Services and Scope',
            'The Service Provider shall provide the freelance services, analyses, code, models, documents, reports, dashboards, or other deliverables described in the agreed project brief, proposal, invoice, statement of work, or subsequent written scope update. Any work outside the agreed scope requires written approval by both parties.',
        ),
        (
            'Client Responsibilities',
            'The Client shall provide timely instructions, accurate information, approvals, access credentials, datasets, and feedback reasonably required for performance of the services. Delays caused by missing information, late approvals, or changes in instructions may move delivery dates and milestones.',
        ),
        (
            'Fees and Payment',
            'The Client shall pay the agreed fees, deposits, milestone payments, or hourly charges stated in the proposal, hire form, or invoice. Unless otherwise agreed in writing, invoices are payable on receipt. The Service Provider may pause work for overdue invoices or unpaid deposits. Payments already made for work performed are non-refundable except where required by law.',
        ),
        (
            'Changes, Revisions, and Expanded Scope',
            'The original fee covers only the agreed scope. Additional revisions, changed assumptions, new deliverables, or materially expanded scope may require a revised fee, timeline, or both. The Service Provider is not obliged to perform out-of-scope work without written agreement.',
        ),
        (
            'Timelines and Deadlines',
            'Any delivery dates are planning targets unless expressly confirmed in writing as fixed milestones. The Service Provider works with soft deadlines by default to allow for contingencies, quality control, client feedback, data issues, infrastructure problems, and third-party dependencies. The parties shall cooperate in good faith if a timeline needs to be adjusted.',
        ),
        (
            'Confidentiality and Data Handling',
            'Each party shall keep the other party\'s confidential information confidential and use it only for the project. Where an NDA is signed, its terms apply in addition to this Agreement. Personal data shared for the project shall be handled only for legitimate project administration, communication, invoicing, delivery, and record-keeping purposes, subject to applicable Kenyan data protection law.',
        ),
        (
            'Intellectual Property',
            'Unless otherwise agreed in writing, the Service Provider retains ownership of pre-existing tools, templates, libraries, know-how, and reusable methods. Upon full payment of all amounts due for the project, the Client receives ownership of the final paid-for deliverables specifically created for that project, excluding the Service Provider\'s general know-how and reusable internal tooling.',
        ),
        (
            'Warranties and Professional Standard',
            'The Service Provider shall perform the services with reasonable skill, care, and diligence consistent with professional freelance practice. Except as expressly stated in this Agreement, the services and deliverables are provided without any guarantee of a specific commercial, financial, regulatory, trading, or investment outcome.',
        ),
        (
            'Limitation of Liability',
            'To the maximum extent permitted by law, neither party shall be liable to the other for indirect, incidental, special, exemplary, or consequential loss, including loss of profits, trading losses, or loss of opportunity. The Service Provider\'s aggregate liability arising from the project shall not exceed the total fees actually paid by the Client for that project, except where liability cannot lawfully be limited.',
        ),
        (
            'Term, Suspension, and Termination',
            'This Agreement begins on the date of signature and continues until completion of the services unless terminated earlier. Either party may terminate on written notice if the other commits a material breach and fails to cure it within a reasonable time, or if continued performance becomes unlawful or impracticable. The Service Provider may suspend performance for non-payment or missing client inputs.',
        ),
        (
            'Dispute Resolution and Governing Law',
            'This Agreement is governed by the laws of Kenya. The parties shall first attempt to resolve disputes through good-faith discussion and, where appropriate, mediation before court proceedings. The courts of Kenya shall have jurisdiction unless the parties agree otherwise in writing.',
        ),
        (
            'Electronic Signatures and Entire Agreement',
            'The parties may sign this Agreement physically or electronically. A scanned, typed, or electronically affixed signature exchanged by email or uploaded through the Service Provider\'s workflow is intended to evidence acceptance, subject to applicable Kenyan law. This Agreement, together with any proposal, statement of work, invoice, and NDA, forms the full agreement for the project unless amended in writing.',
        ),
    ]

    for i, (title, body) in enumerate(clauses, 1):
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 6, f'{i}. {title}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(*MID)
        pdf.multi_cell(0, 5, body)
        pdf.ln(2.5)

    pdf.ln(4)
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 6, 'SIGNATURES', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    y = pdf.get_y()

    pdf.set_xy(10, y)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(85, 5, 'Lago Brian (Service Provider)', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_xy(10, pdf.get_y() + 12)
    pdf.set_draw_color(*DARK)
    pdf.line(10, pdf.get_y(), 90, pdf.get_y())
    pdf.ln(2)
    pdf.set_xy(10, pdf.get_y())
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(*MID)
    pdf.cell(80, 5, 'Signature')
    pdf.ln(5)
    pdf.set_xy(10, pdf.get_y())
    pdf.line(10, pdf.get_y(), 90, pdf.get_y())
    pdf.ln(2)
    pdf.set_xy(10, pdf.get_y())
    pdf.cell(80, 5, 'Name / Date')

    pdf.set_xy(115, y)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*DARK)
    pdf.cell(85, 5, 'Client', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_xy(115, pdf.get_y() + 12)
    pdf.line(115, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    pdf.set_xy(115, pdf.get_y())
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(*MID)
    pdf.cell(80, 5, 'Signature')
    pdf.ln(5)
    pdf.set_xy(115, pdf.get_y())
    pdf.line(115, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    pdf.set_xy(115, pdf.get_y())
    pdf.cell(80, 5, 'Name / Date')

    pdf.ln(12)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(*MID)
    pdf.multi_cell(
        0,
        5,
        'Signing note: The client should sign this agreement before work starts. The NDA remains optional unless the project requires one. Electronic signatures and scanned signatures are intended to be acceptable for workflow purposes.',
    )

    import os
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    pdf.output(output_path)
