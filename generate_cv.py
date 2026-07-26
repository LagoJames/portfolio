"""Generate Lago Brian's CV as a professionally styled PDF."""
from fpdf import FPDF


class CV(FPDF):
    GOLD = (212, 175, 55)
    DARK = (40, 40, 40)
    MID = (80, 80, 80)
    LIGHT = (120, 120, 120)
    BG = (248, 248, 248)

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=18)
        self.set_left_margin(18)
        self.set_right_margin(18)
        self.usable = 174  # 210 - 18 - 18

    def header(self):
        pass

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(*self.LIGHT)
        self.cell(0, 8, f'Lago Brian  |  lagobrian@outlook.com  |  +254 114 209 088  |  Page {self.page_no()}/{{nb}}', align='C')

    def section(self, title):
        self.ln(2)
        self.set_font('Helvetica', 'B', 10.5)
        self.set_text_color(*self.DARK)
        self.cell(0, 7, title.upper(), new_x='LMARGIN', new_y='NEXT')
        self.set_draw_color(*self.GOLD)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.l_margin + self.usable, self.get_y())
        self.ln(3)

    def role(self, title, dates):
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*self.DARK)
        w_title = self.usable - 45
        self.cell(w_title, 5, title)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self.LIGHT)
        self.cell(45, 5, dates, align='R', new_x='LMARGIN', new_y='NEXT')

    def subtitle(self, text):
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self.MID)
        self.cell(0, 4.5, text, new_x='LMARGIN', new_y='NEXT')
        self.ln(1)

    def bullet(self, text):
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self.MID)
        x = self.l_margin
        self.set_x(x)
        self.cell(4, 4, '-')
        self.multi_cell(self.usable - 4, 4, text)
        self.ln(0.5)

    def para(self, text):
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self.MID)
        self.multi_cell(self.usable, 4.2, text)
        self.ln(1)

    def skill_line(self, cat, skills):
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(*self.DARK)
        self.cell(32, 4.5, cat)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self.MID)
        self.multi_cell(self.usable - 32, 4.5, skills)
        self.ln(0.5)


def generate():
    pdf = CV()
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── NAME ──
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 9, 'LAGO BRIAN', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'Financial Engineer  &  Data Scientist', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)

    # ── CONTACT BAR ──
    pdf.set_font('Helvetica', '', 7.5)
    pdf.set_text_color(80, 80, 80)
    pdf.set_fill_color(248, 248, 248)
    bar_h = 14
    pdf.rect(pdf.l_margin, pdf.get_y(), pdf.usable, bar_h, 'F')
    y0 = pdf.get_y() + 2
    pdf.set_xy(pdf.l_margin + 3, y0)
    pdf.cell(0, 4, 'Nairobi, Kenya   |   +254 114 209 088   |   lagobrian@outlook.com   |   github.com/LagoJames', new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(pdf.l_margin + 3)
    pdf.cell(0, 4, 'quanthedge.substack.com   |   jaridalahisa.substack.com   |   upwork.com/freelancers/jamesl34')
    pdf.set_y(y0 + bar_h - 1)
    pdf.ln(4)

    # ── PROFILE ──
    pdf.section('Profile')
    pdf.para(
        'Financial Engineer with a BSc from JKUAT and 5+ years of freelance experience in quantitative '
        'finance, machine learning, and data science. Completed 52+ projects on Upwork spanning volatility '
        'modelling, derivatives pricing, trading systems, and statistical research. Founder of Quant (h)Edge, '
        'a quantitative finance newsletter. Research featured in Spectra Markets and cited by MarketWatch. '
        'CFA Level I candidate. Self-taught across ML, deep learning, and trading systems.'
    )

    # ── EXPERIENCE ──
    pdf.section('Professional Experience')

    pdf.role('Freelance Quantitative Analyst & Data Scientist', '2020 - Present')
    pdf.subtitle('Upwork  |  52+ completed projects  |  $9K+ earned')
    pdf.bullet('Built ARMA-GARCH-Copula portfolio optimisation models, volatility spillover analyses, and ESG-integrated efficient frontiers.')
    pdf.bullet('Developed deep learning models: medical image segmentation (U-Net), loan default prediction (XGBoost/SHAP), market sentiment NLP (BERT/VADER), fault detection (GRU).')
    pdf.bullet('Converted Antoine Savine\'s Differential Deep Learning from TensorFlow to PyTorch with 2+ second speed gains for derivatives pricing.')
    pdf.bullet('Created PineScript indicators and backtesting frameworks. Built algorithmic strategies using VectorBT, IBKR API, and Alpaca.')
    pdf.bullet('Authored 35+ academic papers (ghostwritten, confidential) in econometrics, quantitative finance, and ML/DL.')
    pdf.ln(2)

    pdf.role('Founder & Author -- Quant (h)Edge', '2023 - Present')
    pdf.subtitle('quanthedge.substack.com  |  Quantitative Finance Newsletter')
    pdf.bullet('Publish data-driven research: Barron\'s cover study (1,300+ covers), crypto breadth backtests, FX volatility profiles for 60+ pairs, vine copula sector analysis.')
    pdf.bullet('Featured by Brent Donnelly at Spectra Markets am/FX (May 2024). Cited by MarketWatch (Jan 2025).')
    pdf.ln(2)

    pdf.role('Founder & Author -- Jarida La Hisa', '2026 - Present')
    pdf.subtitle('jaridalahisa.substack.com  |  Daily Kenyan Stock Market Newsletter (NSE)')
    pdf.bullet('Daily coverage of Nairobi Securities Exchange for local investors and traders. English and Swahili.')
    pdf.ln(2)

    pdf.role('Military Service', 'Kenya')
    pdf.subtitle('Veteran -- Kenya Defence Forces')
    pdf.ln(2)

    # ── EDUCATION ──
    pdf.section('Education')

    pdf.role('BSc Financial Engineering', '2013 - 2018')
    pdf.subtitle('Jomo Kenyatta University of Agriculture and Technology (JKUAT), Nairobi')
    pdf.ln(1)

    pdf.role('CFA Level I Candidate', '2026 - Present')
    pdf.subtitle('CFA Institute')
    pdf.ln(1)

    pdf.role('MSc Financial Engineering (Upcoming)', '2026')
    pdf.subtitle('WorldQuant University')
    pdf.ln(2)

    # ── SKILLS ──
    pdf.section('Technical Skills')
    pdf.skill_line('Languages', 'Python, R, MATLAB/Octave, Stata, SPSS, EViews, LaTeX, PineScript')
    pdf.skill_line('ML / AI', 'PyTorch, TensorFlow, Scikit-learn, XGBoost, Keras, NLTK/spaCy, BERT')
    pdf.skill_line('Quant Finance', 'GARCH/ARCH, Vine Copulas, VectorBT, IBKR API, Alpaca, Option Pricing, Portfolio Optimisation, Risk Modelling')
    pdf.skill_line('Statistics', 'Bayesian Methods, Time Series, Econometrics, Stochastic Calculus, Hypothesis Testing')
    pdf.skill_line('Tools', 'Jupyter/Colab, Git/GitHub, PostgreSQL, pandas/NumPy, matplotlib/seaborn, Flask, Docker')
    pdf.ln(2)

    # ── PRESS ──
    pdf.section('Press & Publications')
    pdf.role('Spectra Markets am/FX -- Named Feature', 'May 2024')
    pdf.para('"Thanks again to Brian for doing God\'s work in Excel." -- Brent Donnelly')
    pdf.role('MarketWatch (Dow Jones) -- Data Citation', 'January 2025')
    pdf.para('"Crypto market also suffering from bad breadth." -- live market coverage')
    pdf.ln(1)

    # ── PROJECTS ──
    pdf.section('Selected Projects')
    projects = [
        ('Barron\'s Cover Contrarian Study', 'Catalogued 1,300+ covers. Featured in Spectra Markets.'),
        ('Crypto Breadth Backtesting', '% coins above 50/100/200-DMA as signals. Cited by MarketWatch.'),
        ('Differential Deep Learning (TF->PyTorch)', 'Twin networks for derivatives pricing. 2s+ speed gain.'),
        ('Medical Image Segmentation', 'U-Net pipeline for clinical imaging in PyTorch.'),
        ('Bayesian IV via Gibbs Sampling', 'Posterior estimation of education effects on income with MCMC.'),
        ('TDA for Epileptic Seizure Detection', 'Persistent homology + GRU/LSTM for classification.'),
        ('0DTE Options Trading Model', 'PyTorch DL for Nifty options from 1-min data.'),
        ('S&P 500 Vine Copula Analysis', 'Single-stock sector representatives via copula dependency.'),
    ]
    for title, desc in projects:
        pdf.bullet(f'{title} -- {desc}')
    pdf.ln(2)

    # ── INTERESTS & LANGUAGES ──
    pdf.section('Interests & Languages')
    pdf.para('Formula 1  |  Trading (FX, crypto, equities)  |  House Music  |  Art')
    pdf.para('English (Fluent)  |  Swahili (Native)')

    # ── OUTPUT ──
    out = 'app/static/samples/Lago_Brian_CV.pdf'
    pdf.output(out)
    print(f'CV generated: {out}')


if __name__ == '__main__':
    generate()
