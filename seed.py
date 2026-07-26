"""Seed script — populates the database with all portfolio data."""
import os
import bcrypt
from app import create_app, db
from app.models import (AdminUser, Project, Testimonial, Skill, Setting,
                        Notebook, PMClient, PMProject, PMTask)
from app.utils.helpers import slugify

app = create_app()


def seed_admin():
    if AdminUser.query.first():
        print("  Admin already exists, skipping.")
        return
    email = os.environ.get('ADMIN_EMAIL', 'lagobrian@outlook.com')
    password = os.environ.get('ADMIN_PASSWORD')
    if not password:
        raise RuntimeError("ADMIN_PASSWORD environment variable is required to seed the admin user.")
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    admin = AdminUser(email=email, password_hash=hashed)
    db.session.add(admin)
    db.session.commit()
    print(f"  Admin created: {email}")


def seed_settings():
    defaults = {
        'display_name': 'Lago Brian',
        'tagline': 'Quant by training. Freelance by trade. Writer by curiosity.',
        'about_short': 'Financial Engineer and Data Scientist based in Nairobi. Founder of Quant (h)Edge. Featured in Spectra Markets.',
        'contact_email': 'lagobrian@outlook.com',
        'availability_status': 'available',
        'availability_note': '',
        'stat_projects': '52',
        'stat_earnings': '$9K+',
        'stat_years': '5+',
        'stat_papers': '35+',
        'github_username': 'LagoJames',
        'substack_quant_url': 'https://quanthedge.substack.com',
        'substack_jarida_url': 'https://jaridalahisa.substack.com',
        'upwork_url': 'https://www.upwork.com/freelancers/jamesl34',
        'linkedin_url': '',
        'meta_description': 'Lago Brian — Financial Engineer & Data Scientist. Quantitative finance models, ML systems, and data science. Founder of Quant (h)Edge. Featured in Spectra Markets. Cited by MarketWatch.',
    }
    for key, value in defaults.items():
        existing = Setting.query.filter_by(key=key).first()
        if not existing:
            db.session.add(Setting(key=key, value=value))
    db.session.commit()
    print(f"  {len(defaults)} settings seeded.")


def seed_skills():
    if Skill.query.first():
        print("  Skills already exist, skipping.")
        return
    skills = [
        ("Python", "languages", 1), ("R", "languages", 2),
        ("MATLAB / OCTAVE", "languages", 3), ("Stata", "languages", 4),
        ("SPSS", "languages", 5), ("EViews", "languages", 6),
        ("LaTeX", "languages", 7), ("PineScript", "languages", 8),
        ("PyTorch", "ml_frameworks", 1), ("TensorFlow", "ml_frameworks", 2),
        ("Scikit-learn", "ml_frameworks", 3), ("XGBoost", "ml_frameworks", 4),
        ("NLTK / spaCy", "ml_frameworks", 5), ("Keras", "ml_frameworks", 6),
        ("GARCH / ARCH Models", "quant_finance", 1),
        ("Vine Copulas", "quant_finance", 2),
        ("VectorBT", "quant_finance", 3), ("IBKR API", "quant_finance", 4),
        ("Alpaca", "quant_finance", 5), ("Option Pricing", "quant_finance", 6),
        ("Portfolio Optimisation", "quant_finance", 7),
        ("Risk Modelling", "quant_finance", 8),
        ("Bayesian Statistics", "statistics", 1),
        ("Time Series Analysis", "statistics", 2),
        ("Econometrics", "statistics", 3),
        ("Stochastic Calculus", "statistics", 4),
        ("Quantitative Analysis", "statistics", 5),
        ("Hypothesis Testing", "statistics", 6),
        ("Jupyter / Colab", "tools", 1), ("Git / GitHub", "tools", 2),
        ("PostgreSQL", "tools", 3), ("pandas / NumPy", "tools", 4),
        ("matplotlib / seaborn", "tools", 5),
    ]
    for name, cat, order in skills:
        db.session.add(Skill(name=name, category=cat, sort_order=order))
    db.session.commit()
    print(f"  {len(skills)} skills seeded.")


def seed_projects():
    if Project.query.first():
        print("  Projects already exist, skipping.")
        return

    projects_data = [
        # Financial Engineering (12)
        {"title": "Modelling Rotated ARCH Models", "category": "financial_engineering", "source": "upwork",
         "short_description": "Implemented rotated ARCH volatility models for financial time series analysis.",
         "full_description": "Built rotated ARCH models for advanced volatility modelling of financial time series. Implemented estimation procedures and diagnostic tests in Python.",
         "tools_used": "Python, ARCH, statsmodels, matplotlib", "upwork_rating": 5.0, "is_featured": True, "sort_order": 3},

        {"title": "ARMA-GARCH-Copula Portfolio Optimisation", "category": "financial_engineering", "source": "upwork",
         "short_description": "Multivariate dependency modelling for portfolio construction using vine copulas and GARCH volatility.",
         "full_description": "Combined ARMA-GARCH marginal models with vine copula dependency structures for portfolio optimisation. Demonstrated superior risk-adjusted returns compared to traditional mean-variance approaches.",
         "tools_used": "Python, R, GARCH, Copula, VectorBT, matplotlib", "upwork_rating": 4.5, "sort_order": 4},

        {"title": "ESG Integration + Efficient Frontier", "category": "financial_engineering", "source": "upwork",
         "short_description": "Integrated ESG scores into mean-variance portfolio optimisation framework.",
         "tools_used": "Python, pandas, scipy, matplotlib", "sort_order": 5},

        {"title": "Portfolio Backtest (30 US + EU Equities)", "category": "financial_engineering", "source": "upwork",
         "short_description": "Backtested portfolio strategies across 30 US and European equities.",
         "tools_used": "Python, VectorBT, pandas", "upwork_rating": 5.0, "sort_order": 6},

        {"title": "VIX Index Replication", "category": "financial_engineering", "source": "upwork",
         "short_description": "Replicated the CBOE VIX methodology using options data.",
         "tools_used": "Python, pandas, numpy", "sort_order": 7},

        {"title": "Option Pricing (Cox-Ross-Rubinstein)", "category": "financial_engineering", "source": "upwork",
         "short_description": "Implemented binomial option pricing model with Greeks calculation.",
         "tools_used": "Python, numpy, matplotlib", "sort_order": 8},

        {"title": "Stochastic Life Insurance Model", "category": "financial_engineering", "source": "upwork",
         "short_description": "Built stochastic simulation model for life insurance pricing and reserving.",
         "tools_used": "Python, numpy, scipy", "sort_order": 9},

        {"title": "Volatility + Return Spillover Analysis", "category": "financial_engineering", "source": "upwork",
         "short_description": "Analysed volatility and return spillover effects across financial markets.",
         "tools_used": "Python, R, GARCH, VAR", "sort_order": 10},

        {"title": "GARCH Volatility Modelling in R", "category": "financial_engineering", "source": "upwork",
         "short_description": "Fitted GARCH family models to financial returns data in R.",
         "tools_used": "R, rugarch, ggplot2", "sort_order": 11},

        {"title": "Risk Ranges for Stock Pricing", "category": "financial_engineering", "source": "upwork",
         "short_description": "Designed model for calculating risk ranges for stock price movements.",
         "tools_used": "Python, pandas, scipy", "sort_order": 12},

        {"title": "Financial Modelling", "category": "financial_engineering", "source": "upwork",
         "short_description": "General financial modelling project for client.",
         "tools_used": "Python, Excel, pandas", "upwork_rating": 5.0, "sort_order": 13},

        {"title": "Stochastic Calculus II Academic Lessons", "category": "financial_engineering", "source": "upwork",
         "short_description": "Delivered academic lessons on advanced stochastic calculus topics.",
         "tools_used": "LaTeX, Python, MATLAB", "upwork_rating": 4.0, "sort_order": 14},

        # Machine Learning & AI (12)
        {"title": "Medical Image Segmentation (ML)", "category": "machine_learning", "source": "upwork",
         "short_description": "Deep learning model for medical image segmentation using convolutional neural networks.",
         "full_description": "Developed a deep learning pipeline for medical image segmentation. Used U-Net architecture with PyTorch, achieving high accuracy on clinical imaging data.",
         "tools_used": "Python, PyTorch, U-Net, OpenCV, PIL", "is_featured": True, "sort_order": 1},

        {"title": "Loan Default Prediction", "category": "machine_learning", "source": "upwork",
         "short_description": "Machine learning model for predicting loan defaults using historical lending data.",
         "full_description": "Built an end-to-end ML pipeline for loan default prediction. Compared Random Forest, XGBoost, and logistic regression. Included SHAP explainability analysis.",
         "tools_used": "Python, scikit-learn, XGBoost, SHAP, pandas", "is_featured": True, "sort_order": 2},

        {"title": "Implement Statistical Tests in Python", "category": "machine_learning", "source": "upwork",
         "short_description": "Implemented comprehensive suite of statistical tests in Python.",
         "tools_used": "Python, scipy, statsmodels, pandas", "upwork_rating": 5.0, "sort_order": 15},

        {"title": "Neural Network: TensorFlow to PyTorch", "category": "machine_learning", "source": "upwork",
         "short_description": "Converted deep learning model from TensorFlow to PyTorch framework.",
         "tools_used": "Python, TensorFlow, PyTorch", "upwork_rating": 5.0, "sort_order": 16},

        {"title": "Residual Pesticide Efficacy Study", "category": "machine_learning", "source": "upwork",
         "short_description": "Statistical analysis and ML modelling for pesticide efficacy research.",
         "tools_used": "Python, R, scikit-learn, pandas", "sort_order": 17},

        {"title": "Market Sentiment NLP Model", "category": "machine_learning", "source": "upwork",
         "short_description": "NLP model for financial market sentiment analysis using deep learning.",
         "full_description": "Built a market sentiment classifier using NLP techniques including BERT and VADER. Applied to financial news and social media data for trading signals.",
         "tools_used": "Python, BERT, VADER, NLP, TensorFlow", "upwork_rating": 5.0, "is_featured": True, "sort_order": 3},

        {"title": "Machine Learning / Deep Learning Expert", "category": "machine_learning", "source": "upwork",
         "short_description": "Expert ML/DL consulting and implementation project.",
         "tools_used": "Python, PyTorch, TensorFlow, scikit-learn", "upwork_rating": 5.0, "sort_order": 18},

        {"title": "Wind Power Forecasting", "category": "machine_learning", "source": "upwork",
         "short_description": "ML model for wind power generation forecasting.",
         "tools_used": "Python, scikit-learn, LSTM, pandas", "sort_order": 19},

        {"title": "Topological Data Analysis for AI", "category": "machine_learning", "source": "upwork",
         "short_description": "Applied topological data analysis methods to AI/ML problems.",
         "tools_used": "Python, TDA, scikit-learn, matplotlib", "upwork_rating": 4.2, "sort_order": 20},

        {"title": "Log Analysis with Autoencoders", "category": "machine_learning", "source": "upwork",
         "short_description": "Anomaly detection in system logs using autoencoder neural networks.",
         "tools_used": "Python, PyTorch, pandas, autoencoder", "upwork_rating": 3.1, "sort_order": 21},

        {"title": "Machine Learning for Business (R)", "category": "machine_learning", "source": "upwork",
         "short_description": "Applied ML techniques to business analytics problems in R.",
         "tools_used": "R, caret, ggplot2, dplyr", "sort_order": 22},

        {"title": "Alternative Asset Diversification Dissertation", "category": "machine_learning", "source": "upwork",
         "short_description": "Dissertation on portfolio diversification with alternative assets using ML.",
         "tools_used": "Python, R, scikit-learn, pandas", "upwork_rating": 3.7, "sort_order": 23},

        # Trading & Quant (8)
        {"title": "Implement and Test Strategies (PineScript)", "category": "trading_quant", "source": "upwork",
         "short_description": "Implemented and backtested trading strategies in PineScript on TradingView.",
         "tools_used": "PineScript, TradingView", "upwork_rating": 4.3, "sort_order": 24},

        {"title": "Constructing a Reversal Strategy", "category": "trading_quant", "source": "upwork",
         "short_description": "Designed and tested mean-reversion trading strategy.",
         "tools_used": "Python, VectorBT, pandas", "upwork_rating": 5.0, "sort_order": 25},

        {"title": "PineScript Backtesting", "category": "trading_quant", "source": "upwork",
         "short_description": "Backtesting framework for trading strategies in PineScript.",
         "tools_used": "PineScript, TradingView", "upwork_rating": 4.8, "sort_order": 26},

        {"title": "Create TradingView Indicator", "category": "trading_quant", "source": "upwork",
         "short_description": "Custom TradingView indicator development in PineScript.",
         "tools_used": "PineScript, TradingView", "sort_order": 27},

        {"title": "Poker Odds Probability Calculator", "category": "trading_quant", "source": "upwork",
         "short_description": "Probability calculator for poker hand odds and expected values.",
         "tools_used": "Python, probability, combinatorics", "upwork_rating": 5.0, "sort_order": 28},

        {"title": "Barron's Cover Contrarian Indicator Study", "category": "trading_quant", "source": "quant_hedge",
         "short_description": "Catalogued and analysed 1,300+ Barron's covers as market indicators. Featured in Spectra Markets.",
         "full_description": "Manually catalogued 1,300+ Barron's magazine covers from 1997 onwards, assessed tradability direction, and determined covers are coincident (not contrarian). Data shared with Brent Donnelly at Spectra Markets.\n\nFeatured in [Spectra Markets am/FX](https://www.spectramarkets.com/amfx/are-barrons-covers-contrarian/).",
         "tools_used": "Python, pandas, Excel, data mining",
         "substack_url": "https://quanthedge.substack.com/p/are-barrons-covers-contrarian",
         "is_featured": True, "sort_order": 0},

        {"title": "Autocorrelation TradingView Indicator", "category": "trading_quant", "source": "quant_hedge",
         "short_description": "PineScript autocorrelation indicator for trend confirmation on TradingView.",
         "tools_used": "PineScript, TradingView, autocorrelation",
         "substack_url": "https://quanthedge.substack.com/p/autocorrelation-tradingview",
         "sort_order": 29},

        {"title": "Crypto Breadth Backtesting", "category": "trading_quant", "source": "quant_hedge",
         "short_description": "Backtested crypto breadth indicators. Cited in MarketWatch.",
         "full_description": "Full backtest of crypto breadth indicators (% of coins above 50/100/200-DMA) as entry/exit signals. Analysis was cited by MarketWatch in January 2025.",
         "tools_used": "Python, pandas, CoinMarketCap, VectorBT",
         "substack_url": "https://quanthedge.substack.com/p/your-new-best-friend-in-crypto-trading",
         "is_featured": True, "sort_order": 1},

        # Statistical Analysis & Research (14)
        {"title": "Statistical Analysis for Biology Experiment", "category": "statistical_analysis", "source": "upwork",
         "short_description": "Comprehensive statistical analysis for biology research experiment.",
         "tools_used": "R, Python, ANOVA, regression", "upwork_rating": 5.0, "sort_order": 30},

        {"title": "Fall 2022 Studies (Entomology)", "category": "statistical_analysis", "source": "upwork",
         "short_description": "Statistical analysis for entomology research — repeat client engagement.",
         "tools_used": "R, Python, mixed models, ANOVA", "upwork_rating": 5.0, "sort_order": 31},

        {"title": "Analyze Fall 2021 Data (Entomology)", "category": "statistical_analysis", "source": "upwork",
         "short_description": "Data analysis for entomology field experiment data.",
         "tools_used": "R, Python, statistical testing", "upwork_rating": 5.0, "sort_order": 32},

        {"title": "Serial Correlation Analysis #1", "category": "statistical_analysis", "source": "upwork",
         "short_description": "Statistical analysis of serial correlation in time series data.",
         "tools_used": "Python, statsmodels, pandas", "upwork_rating": 5.0, "sort_order": 33},

        {"title": "Serial Correlation Analysis #2", "category": "statistical_analysis", "source": "upwork",
         "short_description": "Follow-up serial correlation analysis with extended methodology.",
         "tools_used": "Python, statsmodels, pandas", "upwork_rating": 5.0, "sort_order": 34},

        {"title": "Statistical Inference / Weibull Distribution", "category": "statistical_analysis", "source": "upwork",
         "short_description": "Statistical inference using Weibull distribution for reliability analysis.",
         "tools_used": "Python, scipy, Weibull, MLE", "upwork_rating": 4.7, "sort_order": 35},

        {"title": "Data Analysis - Networks Data", "category": "statistical_analysis", "source": "upwork",
         "short_description": "Network data analysis and visualisation project.",
         "tools_used": "Python, NetworkX, pandas, matplotlib", "upwork_rating": 5.0, "sort_order": 36},

        {"title": "R SIR Model (Epidemiological)", "category": "statistical_analysis", "source": "upwork",
         "short_description": "SIR epidemiological model implementation in R.",
         "tools_used": "R, deSolve, ggplot2", "upwork_rating": 5.0, "sort_order": 37},

        {"title": "Africa Ethnicity Coding", "category": "statistical_analysis", "source": "upwork",
         "short_description": "Research coding and classification of African ethnic groups.",
         "tools_used": "Python, pandas, research methodology", "upwork_rating": 5.0, "sort_order": 38},

        {"title": "Financial Engineering Analysis", "category": "statistical_analysis", "source": "upwork",
         "short_description": "Financial engineering analysis and modelling project.",
         "tools_used": "Python, R, financial modelling", "upwork_rating": 5.0, "sort_order": 39},

        {"title": "AI / Python Algorithms Expert", "category": "statistical_analysis", "source": "upwork",
         "short_description": "AI and Python algorithm consulting and implementation.",
         "tools_used": "Python, algorithms, data structures", "upwork_rating": 5.0, "sort_order": 40},

        {"title": "Medical Data Modelling", "category": "statistical_analysis", "source": "upwork",
         "short_description": "Statistical modelling of medical research data.",
         "tools_used": "Python, R, biostatistics, regression", "upwork_rating": 5.0, "sort_order": 41},

        {"title": "Stata - Fed Survey of Consumer Finances", "category": "statistical_analysis", "source": "upwork",
         "short_description": "Analysis of Federal Reserve Survey of Consumer Finances data in Stata.",
         "tools_used": "Stata, survey statistics, regression", "sort_order": 42},

        {"title": "Mathematical Derivation (LaTeX)", "category": "statistical_analysis", "source": "upwork",
         "short_description": "Mathematical derivations and proofs typeset in LaTeX.",
         "tools_used": "LaTeX, mathematics", "upwork_rating": 3.3, "sort_order": 43},

        # Research projects from Quant (h)Edge
        {"title": "S&P 500 Sector Representatives via Vine Copulas", "category": "research", "source": "quant_hedge",
         "short_description": "Used Vine Copulas to find single-stock sector representatives across S&P 500.",
         "full_description": "Applied Vine Copulas to capture complex multivariate dependency structures across S&P 500 sectors. Identified single stocks that best represent each sector's risk-return profile. Code and data included.",
         "tools_used": "Python, vine copulas, pyvinecopulib, pandas",
         "substack_url": "https://quanthedge.substack.com/p/finding-single-name-vine-copulas",
         "sort_order": 44},

        {"title": "FX Volatility Profiles (60+ Currencies)", "category": "research", "source": "quant_hedge",
         "short_description": "Comprehensive intraday volatility analysis of 60+ currency pairs by session and time-of-day.",
         "tools_used": "Python, pandas, FX data, BIS",
         "substack_url": "https://quanthedge.substack.com/p/seasonality-intraday-fx-volatility",
         "sort_order": 45},

        {"title": "FOMC Statements NLP Dataset", "category": "research", "source": "quant_hedge",
         "short_description": "Free comprehensive dataset of FOMC statements, speeches, minutes, and press conferences.",
         "tools_used": "Python, NLP, web scraping, Federal Reserve",
         "substack_url": "https://quanthedge.substack.com/p/fomc-dataset",
         "sort_order": 46},
    ]

    for p in projects_data:
        p['slug'] = slugify(p['title'])
        project = Project(**p)
        db.session.add(project)

    db.session.commit()
    print(f"  {len(projects_data)} projects seeded.")


def seed_testimonials():
    if Testimonial.query.first():
        print("  Testimonials already exist, skipping.")
        return

    testimonials = [
        {"client_name": "Client, United States", "job_title": "Create a Market Sentiment NLP Model",
         "review_text": "James has been incredible, he has great knowledge of the financial market as well as AI. Thank you so much James!",
         "rating": 5.0, "sort_order": 1},
        {"client_name": "Client, United States", "job_title": "Statistical Analysis (Entomology) - Repeat Client",
         "review_text": "James is extremely patient and very effectively addresses any of my questions regarding statistical methods or results in a prompt manner. He has gone above and beyond to make sure the work was done correctly.",
         "rating": 5.0, "sort_order": 2},
        {"client_name": "Client", "job_title": "Statistical Analysis for Biology Experiment",
         "review_text": "I highly recommend James. He is the perfect example of delivering more than promised. Not only that, he is able to effectively communicate the meaning of the data and why the results matter.",
         "rating": 5.0, "sort_order": 3},
        {"client_name": "Client", "job_title": "Neural Network: TensorFlow to PyTorch",
         "review_text": "Delivered excellent work on this machine learning project. His communication was top-notch, he met all deadlines, and his skills were very strong.",
         "rating": 5.0, "sort_order": 4},
        {"client_name": "Client", "job_title": "Implement Statistical Tests in Python",
         "review_text": "James performed well and delivered the results according to specs. Hope to work with him again!",
         "rating": 5.0, "sort_order": 5},
        {"client_name": "Client", "job_title": "Network Data Analysis",
         "review_text": "James is very responsive, productive, responsible and friendly. He can complete the tasks efficiently. I can say that this is definitely the best Upwork service I have received.",
         "rating": 5.0, "sort_order": 6},
        {"client_name": "Client", "job_title": "Financial Engineering Project",
         "review_text": "I had a great experience working with James. He is very cooperative and receptive to feedback. I will be happy to work with him again.",
         "rating": 5.0, "sort_order": 7},
        {"client_name": "Client", "job_title": "AI and Python Algorithms",
         "review_text": "Very kind, upfront and always available. Easy and efficient communication, recommend 100%.",
         "rating": 5.0, "sort_order": 8},
        {"client_name": "Client", "job_title": "Serial Correlation Analysis",
         "review_text": "Great Work! Very Diligent. Committed to Quality and Detail Oriented.",
         "rating": 5.0, "sort_order": 9},
    ]

    for t in testimonials:
        db.session.add(Testimonial(**t))
    db.session.commit()
    print(f"  {len(testimonials)} testimonials seeded.")


def seed_pm_data():
    """Seed Project Management data from spreadsheet."""
    if PMClient.query.first():
        print("  PM data already exists, skipping.")
        return

    # Clients from spreadsheet
    c1 = PMClient(client_id_code='001', name='Younnan Lamine')
    c2 = PMClient(client_id_code='002', name='Ariana Mondiri')
    c3 = PMClient(client_id_code='003', name='Joel Khalil')
    db.session.add_all([c1, c2, c3])
    db.session.flush()

    # Projects
    p1 = PMProject(client_id=c1.id, name="Bachelor's thesis: Effect of HCWs Vaccine Coverage on Healthcare costs of a UMC",
                   status='ongoing', budget=515, amount_paid=215)
    p2 = PMProject(client_id=c2.id, name="TDA for ML/DL: Epileptic Seizure Classification",
                   status='ongoing', budget=300, amount_paid=300,
                   notes="Client added a research task for $50. Paid in full")
    p3 = PMProject(client_id=c3.id, name="Bachelor's thesis: Bayesian Analysis of Instrument Variables via Gibbs Sampling",
                   status='ongoing', budget=100, amount_paid=70,
                   notes="Client wants to change data and have us write the thesis")
    db.session.add_all([p1, p2, p3])
    db.session.flush()

    # Tasks for p1
    tasks = [
        PMTask(project_id=p1.id, task_id_code='001-001', description='Chapter 1 of thesis (Introduction)',
               estimated_hours=4, status='completed', priority='2/5'),
        PMTask(project_id=p1.id, task_id_code='001-002', description='Chapter 3 of thesis (Methodology)',
               estimated_hours=10, status='not_started', priority='4/5'),
        PMTask(project_id=p1.id, task_id_code='001-003', description='Chapter 2 of thesis (Literature Review)',
               estimated_hours=8, status='not_started', priority='4/5'),
        PMTask(project_id=p1.id, task_id_code='001-004', description='Chapter 4 of thesis (Results)',
               estimated_hours=4, status='not_started', priority='4/5'),
    ]
    db.session.add_all(tasks)
    db.session.commit()
    print("  PM clients, projects, and tasks seeded.")


def seed_pinescript_projects():
    if Project.query.filter_by(category='pinescript').first():
        print("  PineScript projects already exist, skipping.")
        return

    tv_url = 'https://www.tradingview.com/u/lagobrian23/#published-scripts'

    projects = [
        {"title": "Risk Range", "category": "pinescript", "source": "tradingview",
         "short_description": "Creates risk ranges using implied volatility (VIX) or historical volatility, skewness (CBOE SKEW or estimate) and kurtosis.",
         "tools_used": "PineScript, TradingView, VIX, volatility", "is_featured": True,
         "substack_url": tv_url, "sort_order": 60,
         "full_description": "Creates risk ranges using implied volatility (VIX) or historical volatility, skewness (Cboe SKEW or estimate) and kurtosis. Top liked script with 123 likes."},

        {"title": "Bollinger Bands and RSI Mix with DCA", "category": "pinescript", "source": "tradingview",
         "short_description": "Uses a mix of Bollinger Bands and RSI to enter long positions with Dollar Cost Averaging (DCA).",
         "tools_used": "PineScript, TradingView, Bollinger Bands, RSI, DCA", "is_featured": True,
         "substack_url": tv_url, "sort_order": 61,
         "full_description": "Uses a mix of Bollinger Bands and RSI to enter long positions. Implements DCA (Dollar Cost Averaging). 115 likes."},

        {"title": "RSI Multiple Auto-Trendlines", "category": "pinescript", "source": "tradingview",
         "short_description": "Draws up to 4 trendlines on the RSI autonomously. User can remove lines and pick colours.",
         "tools_used": "PineScript, TradingView, RSI, trendlines", "is_featured": True,
         "substack_url": tv_url, "sort_order": 62,
         "full_description": "Draws as many as 4 trendlines autonomously. User can remove lines and pick colours. Most popular indicator with 107 likes."},

        {"title": "Daily Risk Ranges", "category": "pinescript", "source": "tradingview",
         "short_description": "Creates daily risk ranges using historical volatility, volatility skew and vol-of-vol.",
         "tools_used": "PineScript, TradingView, volatility, skew",
         "substack_url": tv_url, "sort_order": 63,
         "full_description": "Creates daily Risk Ranges using historical volatility, volatility skew and vol-of-vol. 58 likes — companion to Risk Range."},

        {"title": "RSI Auto-Trendlines", "category": "pinescript", "source": "tradingview",
         "short_description": "Draws trendlines on the RSI that update autonomously.",
         "tools_used": "PineScript, TradingView, RSI, trendlines",
         "substack_url": tv_url, "sort_order": 64},

        {"title": "RSI Highest Lowest", "category": "pinescript", "source": "tradingview",
         "short_description": "Draws trendlines on the RSI using pivot highs and pivot lows. Configurable lookback and pivot count.",
         "tools_used": "PineScript, TradingView, RSI, pivot points",
         "substack_url": tv_url, "sort_order": 65},

        {"title": "Marco's Indicator Panel", "category": "pinescript", "source": "tradingview",
         "short_description": "Shows MA, Momentum and Super-trend of the current symbol and a user-specified symbol across multiple timeframes.",
         "tools_used": "PineScript, TradingView, MA, momentum, Super Trend",
         "substack_url": tv_url, "sort_order": 66},

        {"title": "Aroon, Super Trend, Volume Oscillator & Kaufman AMA Strategy", "category": "pinescript", "source": "tradingview",
         "short_description": "Enters longs and shorts based on conditions from Aroon, Super Trend, Volume Oscillator and Kaufman Adaptive Moving Average.",
         "tools_used": "PineScript, TradingView, Aroon, Kaufman AMA, Volume Oscillator",
         "substack_url": tv_url, "sort_order": 67},

        {"title": "Buy on Pullback", "category": "pinescript", "source": "tradingview",
         "short_description": "Goes long when price retraces to the 38.2 Fibonacci level at a certain speed or slower, then retests the level.",
         "tools_used": "PineScript, TradingView, Fibonacci, retracement",
         "substack_url": tv_url, "sort_order": 68},

        {"title": "Simple DCA with MA", "category": "pinescript", "source": "tradingview",
         "short_description": "Simple dollar cost averaging strategy with moving average filter condition.",
         "tools_used": "PineScript, TradingView, DCA, moving average",
         "substack_url": tv_url, "sort_order": 69},

        {"title": "Planet Finder", "category": "pinescript", "source": "tradingview",
         "short_description": "Finds planetary cycles based on user-defined inputs. Configurable colours, line height, focal point, and visibility.",
         "tools_used": "PineScript, TradingView, astro, cycles",
         "substack_url": tv_url, "sort_order": 70},

        {"title": "Bar Counter", "category": "pinescript", "source": "tradingview",
         "short_description": "Uses timestamps to find corresponding bars and shows the number of bars in a time interval. Configurable colours.",
         "tools_used": "PineScript, TradingView, utility, timestamps",
         "substack_url": tv_url, "sort_order": 71},

        {"title": "Bar Finder", "category": "pinescript", "source": "tradingview",
         "short_description": "Identifies specific bars using date and time variables. Configurable line distance and colours.",
         "tools_used": "PineScript, TradingView, utility, date/time",
         "substack_url": tv_url, "sort_order": 72},
    ]

    for p in projects:
        p['slug'] = slugify(p['title'])
        existing = Project.query.filter_by(slug=p['slug']).first()
        if not existing:
            db.session.add(Project(**p))
    try:
        db.session.commit()
        print(f"  PineScript projects seeded.")
    except Exception as e:
        db.session.rollback()
        print(f"  ERROR seeding PineScript projects: {e}")


def seed_ghostwriting_projects():
    if Project.query.filter_by(category='ghostwriting').first():
        print("  Ghostwriting projects already exist, skipping.")
        return

    projects = [
        {"title": "Comparing ARCH and GARCH Models",
         "category": "ghostwriting", "source": "upwork",
         "short_description": "Comparative analysis of ARCH and GARCH volatility modelling approaches.",
         "full_description": "A comprehensive academic paper comparing ARCH and GARCH volatility modelling approaches in econometrics. Covers theoretical foundations, estimation methods, and empirical applications.",
         "tools_used": "R, EViews, LaTeX, econometrics", "is_featured": False,
         "substack_url": "comparing-arch-garch-models.docx", "sort_order": 80},

        {"title": "Interrelations Among Global Capital Markets",
         "category": "ghostwriting", "source": "upwork",
         "short_description": "Investigation of co-movement and interdependence across major world capital markets.",
         "full_description": "Academic paper investigating co-movement and interdependence across major global capital markets. Employs cointegration analysis and VAR modelling to assess long-run relationships.",
         "tools_used": "R, Python, cointegration, VAR", "is_featured": False,
         "substack_url": "interrelations-global-capital-markets.docx", "sort_order": 81},

        {"title": "Capital Transition & Bank Systemic Risk",
         "category": "ghostwriting", "source": "upwork",
         "short_description": "Analysis of capital transitional arrangements and their effect on bank systemic risk.",
         "full_description": "Research paper analysing how capital transitional arrangements under Basel III/IV affect bank systemic risk. Includes panel data regression and stress-testing frameworks.",
         "tools_used": "Stata, panel data, Basel III", "is_featured": False,
         "substack_url": "capital-transition-bank-systemic-risk.docx", "sort_order": 82},

        {"title": "Determinants of Economic Growth",
         "category": "ghostwriting", "source": "upwork",
         "short_description": "Econometric study of factors driving economic growth.",
         "full_description": "Econometric study examining the key determinants of economic growth across a panel of developing and developed economies. Employs GMM estimation to control for endogeneity.",
         "tools_used": "Stata, GMM, panel data, macroeconomics", "is_featured": False,
         "substack_url": "determinants-economic-growth.docx", "sort_order": 83},

        {"title": "Statistical Analysis for Business",
         "category": "ghostwriting", "source": "upwork",
         "short_description": "Applied statistical methods for business decision-making.",
         "full_description": "Applied statistics report covering hypothesis testing, regression analysis, and forecasting for business contexts. Practical interpretation of results for non-technical stakeholders.",
         "tools_used": "SPSS, Excel, regression, hypothesis testing", "is_featured": False,
         "substack_url": "statistical-analysis-business.docx", "sort_order": 84},
    ]

    for p in projects:
        p['slug'] = slugify(p['title'])
        existing = Project.query.filter_by(slug=p['slug']).first()
        if not existing:
            db.session.add(Project(**p))
    try:
        db.session.commit()
        print("  Ghostwriting projects seeded.")
    except Exception as e:
        db.session.rollback()
        print(f"  ERROR seeding ghostwriting projects: {e}")


def run_seed():
    with app.app_context():
        print("Seeding database...")
        seed_admin()
        seed_settings()
        seed_skills()
        seed_projects()
        seed_pinescript_projects()
        seed_ghostwriting_projects()
        seed_testimonials()
        seed_pm_data()
        print("\nDone! All data seeded successfully.")
        print(f"  Projects: {Project.query.count()}")
        print(f"  Testimonials: {Testimonial.query.count()}")
        print(f"  Skills: {Skill.query.count()}")
        print(f"  Settings: {Setting.query.count()}")
        print(f"  PM Clients: {PMClient.query.count()}")
        print(f"  PM Projects: {PMProject.query.count()}")


if __name__ == '__main__':
    run_seed()
