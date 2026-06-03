"""
Mahayukti Finance — personal finance, investing & wealth building for India.
@mahayuktifinance | 2 Shorts/day + 3 Long-form/week (Mon/Wed/Fri)
"""

CHANNEL_ID     = "finance"
CHANNEL_NAME   = "Mahayukti Finance"
CHANNEL_HANDLE = "@mahayuktifinance"
TOKEN_ENV_VAR  = "YOUTUBE_FINANCE_TOKEN_JSON"

NICHE = (
    "Personal finance, stock market, mutual funds, tax planning, and wealth "
    "building specifically for Indian millennials and first-time investors."
)

VIDEO_STYLE = (
    "Dark cinematic with deep green and gold tones, stock market charts, "
    "Indian rupee symbols, clean professional aesthetic, dramatic lighting"
)

VOICE = "af_heart"   # warm, clear — works well for finance content

PRIMARY_HEX = "#00C864"   # green for finance/wealth

# ── Short topics ──────────────────────────────────────────────────────────────

SHORT_TOPICS = [
    {"name": "Why SIP beats lump sum every time — the math", "category": "Mutual Funds"},
    {"name": "Stop putting money in FD — here's what to do instead", "category": "Fixed Income"},
    {"name": "Tax hack most salaried Indians miss in 80C", "category": "Tax Planning"},
    {"name": "Why your LIC policy is destroying your wealth", "category": "Insurance"},
    {"name": "Index funds vs active funds — who actually wins?", "category": "Mutual Funds"},
    {"name": "Where to keep your emergency fund in India", "category": "Personal Finance"},
    {"name": "How to get 0% tax on ₹7 lakh income — legally", "category": "Tax Planning"},
    {"name": "Crypto tax in India — 3 things you must know", "category": "Crypto"},
    {"name": "How much term insurance do you actually need?", "category": "Insurance"},
    {"name": "SIP in 3 simple steps for beginners", "category": "Mutual Funds"},
    {"name": "PPF trick to maximise your tax-free returns", "category": "Fixed Income"},
    {"name": "Why your salary account is killing your money", "category": "Personal Finance"},
    {"name": "Gold ETF vs Sovereign Gold Bond — which is better?", "category": "General"},
    {"name": "The 50/30/20 rule explained in 60 seconds", "category": "Personal Finance"},
    {"name": "Step-up SIP: the smartest wealth-building hack", "category": "Mutual Funds"},
    {"name": "CIBIL score basics every Indian must know", "category": "Credit"},
    {"name": "Direct mutual funds vs regular — the difference explained", "category": "Mutual Funds"},
    {"name": "NPS vs EPF: which is better for retirement?", "category": "Retirement"},
    {"name": "Health insurance sub-limits: what the fine print hides", "category": "Insurance"},
    {"name": "How to invest your bonus — priority order", "category": "Personal Finance"},
]

# ── Long-form topics ──────────────────────────────────────────────────────────

LONG_TOPICS = [
    {
        "name": "SIP vs Lump Sum: Which One Actually Makes You More Money?",
        "category": "Mutual Funds",
        "angle": "Rupee cost averaging math, market timing myth, real data from 2008 and 2020 crashes",
    },
    {
        "name": "How to Pay ZERO Tax on ₹12 Lakh Income — Legally",
        "category": "Tax Planning",
        "angle": "New vs old tax regime, 80C/80D/HRA/NPS deductions, Section 87A rebate walkthrough",
    },
    {
        "name": "Why Your LIC Policy Is Destroying Your Wealth",
        "category": "Insurance",
        "angle": "ULIP trap, real returns vs term insurance math, surrender value reality, what to do instead",
    },
    {
        "name": "The Complete Guide to Buying Your First Mutual Fund",
        "category": "Mutual Funds",
        "angle": "Direct vs regular, expense ratio impact, Nifty 50 index fund, starting with ₹500 on Zerodha/Groww",
    },
    {
        "name": "EPFO vs NPS vs PPF: Where Should Your Retirement Money Go?",
        "category": "Retirement",
        "angle": "Tax treatment, liquidity, return comparison, optimal split strategy by age group",
    },
    {
        "name": "Why 95% of Active Mutual Funds Can't Beat the Index",
        "category": "Mutual Funds",
        "angle": "SPIVA India data, expense ratio drag, survivorship bias, fund manager luck vs skill",
    },
    {
        "name": "Renting vs Buying a House — The Math Nobody Shows You",
        "category": "Real Estate",
        "angle": "Price-to-rent ratio, opportunity cost of down payment, EMI vs investing the difference",
    },
    {
        "name": "How to Build ₹1 Crore in 10 Years on a ₹50,000 Salary",
        "category": "Personal Finance",
        "angle": "50/30/20 rule, SIP calculator walkthrough, step-up SIP, realistic compounding timeline",
    },
    {
        "name": "The Complete Term Insurance Guide for Indian Families",
        "category": "Insurance",
        "angle": "How much cover, online vs offline, claim settlement ratios, critical riders explained",
    },
    {
        "name": "Smallcap vs Midcap vs Largecap: Where to Invest in 2024?",
        "category": "Stock Market",
        "angle": "Risk-return tradeoff, SEBI categorisation, historical data, portfolio allocation by age",
    },
    {
        "name": "Debt Mutual Funds vs FD: Which Is Actually Better After Tax?",
        "category": "Fixed Income",
        "angle": "Real returns after inflation, indexation changes post-2023, credit risk, duration guide",
    },
    {
        "name": "How to File ITR Yourself Without a CA",
        "category": "Tax Planning",
        "angle": "Step-by-step ITR-1 and ITR-2, Form 16, AIS reconciliation, capital gains, common mistakes",
    },
    {
        "name": "Health Insurance in India — What They Don't Tell You",
        "category": "Insurance",
        "angle": "Waiting periods, sub-limits, co-pay traps, top-up vs super top-up, best claim settlement ratios",
    },
    {
        "name": "How to Invest in US Stocks from India — Complete Guide",
        "category": "Stock Market",
        "angle": "LRS route, fractional shares, tax treatment in India, PFIC, best platforms",
    },
    {
        "name": "Gold vs Nifty 50: 20-Year Comparison — What Actually Won?",
        "category": "General",
        "angle": "Data since 2004, Sovereign Gold Bonds vs physical vs ETF, portfolio role of gold",
    },
    {
        "name": "The Dark Truth About Real Estate Returns in India",
        "category": "Real Estate",
        "angle": "Actual CAGR after costs, black money premium, maintenance, vacancy, REITs as alternative",
    },
    {
        "name": "ELSS vs PPF vs NPS: Best Tax-Saving Option in 2024",
        "category": "Tax Planning",
        "angle": "Lock-in periods, expected returns, liquidity, which to choose by age and risk appetite",
    },
    {
        "name": "How Inflation Is Quietly Eating Your FD and Savings Returns",
        "category": "Fixed Income",
        "angle": "Real returns after tax and inflation, savings alternatives, floating rate bonds",
    },
    {
        "name": "How to Retire at 45 in India — FIRE Explained",
        "category": "Personal Finance",
        "angle": "25x rule, safe withdrawal rate, India-specific healthcare/inflation challenges",
    },
    {
        "name": "How to Use Credit Cards Without Getting Into Debt",
        "category": "Credit",
        "angle": "Reward optimisation, CIBIL score management, full payment discipline, balance transfer trap",
    },
    {
        "name": "Step-Up SIP: The Smartest Way to Build Wealth in India",
        "category": "Mutual Funds",
        "angle": "10% annual step-up compounding math, calculator walkthrough, best platforms",
    },
    {
        "name": "Budget 2024 — What Changed for Your Investments and Taxes",
        "category": "Tax Planning",
        "angle": "LTCG changes, indexation removal, new tax slabs, NPS impact, debt fund changes",
    },
    {
        "name": "How India's Richest 1% Invest Their Money",
        "category": "Stock Market",
        "angle": "Asset allocation, PMS, AIFs, direct equity, family offices vs retail investors",
    },
    {
        "name": "PPF: The Only Investment That Gives Tax-Free Guaranteed Returns",
        "category": "Fixed Income",
        "angle": "EEE status, current rate, extension rules, partial withdrawal, loan facility",
    },
    {
        "name": "How to Read a Mutual Fund Factsheet Like a Pro",
        "category": "Mutual Funds",
        "angle": "Alpha, beta, Sharpe ratio, portfolio overlap, expense ratio, AUM size — what matters",
    },
    {
        "name": "Emergency Fund: The Step Most Indians Skip Before Investing",
        "category": "Personal Finance",
        "angle": "6-month expenses rule, where to keep it (liquid fund vs FD), common mistakes",
    },
    {
        "name": "How to Build Passive Income of ₹50,000/Month from Dividends",
        "category": "Stock Market",
        "angle": "Dividend yield stocks in India, dividend stripping rules, REIT distributions",
    },
    {
        "name": "The Truth About Crypto in India — Tax, Risk, and Reality",
        "category": "Crypto",
        "angle": "30% flat tax, TDS, no loss set-off, portfolio allocation, who should invest and how much",
    },
    {
        "name": "How to Invest Your Diwali Bonus — A Complete Financial Plan",
        "category": "Personal Finance",
        "angle": "Debt first vs invest first, tax-saving priority, lump sum strategy, asset allocation",
    },
    {
        "name": "Why Most Indians Get Insurance Wrong — And Stay Broke",
        "category": "Insurance",
        "angle": "Underinsurance reality, mixing investment and insurance, term vs endowment data",
    },
]
