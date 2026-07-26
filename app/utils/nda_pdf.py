"""Generate a Non-Disclosure Agreement PDF using fpdf2."""
from fpdf import FPDF, XPos, YPos
from datetime import datetime, timezone

GOLD = (201, 168, 76)
DARK = (17, 24, 39)
MID  = (55, 65, 81)
WHITE = (255, 255, 255)
LIGHT = (249, 250, 251)


class NDAPDF(FPDF):
    def header(self):
        self.set_fill_color(*GOLD)
        self.rect(0, 0, 210, 4, 'F')
        self.set_y(10)
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(*DARK)
        self.cell(0, 10, 'LAGO BRIAN', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*MID)
        self.cell(0, 5, 'Non-Disclosure Agreement', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
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
        self.cell(0, 4, 'Lago Brian · lagobrian.com · lagobrian@outlook.com', align='C')


def generate_nda(output_path):
    """Generate the standard NDA PDF."""
    pdf = NDAPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 8, 'NON-DISCLOSURE AGREEMENT', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*MID)
    pdf.cell(0, 6, f'Effective upon signature. Document generated: {datetime.now(timezone.utc).strftime("%B %d, %Y")}',
             align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    clauses = [
        ('Parties',
         'This Non-Disclosure Agreement ("Agreement") is entered into between Lago Brian, a freelance financial engineer and data scientist based in Nairobi, Kenya ("Disclosing Party"), and the undersigned client ("Receiving Party"). Both parties may be referred to individually as a "Party" and collectively as the "Parties."'),

        ('Purpose',
         'The Parties wish to explore and/or engage in a professional services relationship involving quantitative finance, data science, machine learning, statistical analysis, or related work. In connection with this engagement, the Disclosing Party may share proprietary methods, code, data, research, findings, and other confidential information with the Receiving Party, and vice versa.'),

        ('Definition of Confidential Information',
         'Confidential Information means any data or information that is proprietary to the disclosing Party and not generally known to the public, whether in tangible or intangible form, including but not limited to: technical data, trade secrets, financial data, business plans, research, software code, models, algorithms, client lists, pricing, and any information marked or reasonably understood to be confidential.'),

        ('Obligations of Receiving Party',
         'The Receiving Party agrees to: (a) hold all Confidential Information in strict confidence; (b) not disclose Confidential Information to any third party without prior written consent; (c) use Confidential Information solely for the purpose of the agreed project engagement; (d) take reasonable security precautions to protect Confidential Information; (e) promptly notify the Disclosing Party of any actual or suspected unauthorized disclosure.'),

        ('Exclusions',
         'This Agreement does not apply to information that: (a) is or becomes publicly known through no breach by the Receiving Party; (b) was rightfully known by the Receiving Party prior to disclosure; (c) is independently developed by the Receiving Party without use of Confidential Information; (d) is required to be disclosed by applicable law, regulation, or court order, provided the Receiving Party gives prompt written notice.'),

        ('Intellectual Property',
         'Nothing in this Agreement grants either Party any rights in the Confidential Information of the other Party except as expressly stated. All deliverables, code, models, and work product created by Lago Brian under a paid engagement become the property of the client upon receipt of final payment, unless otherwise agreed in writing.'),

        ('Term and Termination',
         'This Agreement shall remain in effect for a period of three (3) years from the effective date, or until the conclusion of the project engagement, whichever is later. Obligations regarding Confidential Information that constitutes a trade secret shall survive indefinitely.'),

        ('Return of Information',
         'Upon completion or termination of the engagement, or upon request by the Disclosing Party, the Receiving Party shall promptly return or destroy all Confidential Information and any copies thereof, and certify in writing that it has done so.'),

        ('No Warranty',
         'All Confidential Information is provided "as is." The Disclosing Party makes no warranties, express or implied, regarding accuracy, completeness, or fitness for a particular purpose.'),

        ('Remedies',
         'The Parties acknowledge that breach of this Agreement may cause irreparable harm for which monetary damages would be insufficient. The non-breaching Party shall be entitled to seek equitable relief, including injunction and specific performance, in addition to all other remedies available at law.'),

        ('Governing Law & Jurisdiction',
         'This Agreement shall be governed by and construed in accordance with the laws of Kenya. The Parties agree to first attempt to resolve any disputes through good-faith negotiation before resorting to formal legal proceedings.'),

        ('Entire Agreement',
         'This Agreement constitutes the entire agreement between the Parties regarding confidentiality and supersedes all prior discussions. Amendments must be in writing and signed by both Parties.'),
    ]

    for i, (title, body) in enumerate(clauses, 1):
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 6, f'{i}. {title}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(*MID)
        pdf.multi_cell(0, 5, body)
        pdf.ln(3)

    # Signature blocks
    pdf.ln(4)
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 6, 'SIGNATURES', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Two signature columns
    y = pdf.get_y()
    # Left: Lago Brian
    pdf.set_xy(10, y)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*DARK)
    pdf.cell(85, 5, 'Lago Brian (Service Provider)', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_xy(10, pdf.get_y() + 12)
    pdf.set_draw_color(*DARK)
    pdf.set_line_width(0.3)
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
    pdf.cell(80, 5, 'Date')

    # Right: Client
    pdf.set_xy(115, y)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*DARK)
    pdf.cell(85, 5, 'Client (Receiving Party)', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_xy(115, pdf.get_y() + 12)
    pdf.set_draw_color(*DARK)
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
    pdf.cell(80, 5, 'Date')

    pdf.ln(12)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(*MID)
    pdf.multi_cell(0, 5, 'Hint: You can sign this document using any PDF editor such as Adobe Acrobat Reader (free), Smallpdf.com, ilovepdf.com, or the built-in PDF viewer on Mac/iPhone. Simply open the file, add your signature, and upload the signed copy.')

    import os
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    pdf.output(output_path)
