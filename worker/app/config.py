"""Config for the sector rotation scan worker.

This is the same set of tunables from sector_rotation_bull_put_finder.py,
unchanged -- only the delivery mechanism (Supabase rows instead of
print()/CSV) is different. Keeping the numbers identical means the app's
first runs are directly comparable to the ones already reviewed in Colab.
"""

SECTOR_ETFS = {
    "Technology": "XLK",
    "Financials": "XLF",
    "Energy": "XLE",
    "Health Care": "XLV",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Consumer Staples": "XLP",
    "Consumer Discretionary": "XLY",
    "Utilities": "XLU",
    "Communication Services": "XLC",
    "Real Estate": "XLRE",
}

SECTOR_CANDIDATES = {
    "Technology": ["AAPL","MSFT","NVDA","AVGO","CRM","ORCL","ADBE","AMD","CSCO","ACN",
                   "IBM","QCOM","TXN","INTU","AMAT","MU","LRCX","KLAC","NOW","PANW"],
    "Financials": ["JPM","BAC","WFC","GS","MS","C","SCHW","BLK","SPGI","AXP",
                   "PNC","USB","TFC","COF","MET","AIG","PGR","TRV","CB","ICE"],
    "Energy": ["XOM","CVX","COP","EOG","SLB","MPC","PSX","VLO","OXY","WMB",
               "KMI","HAL","BKR","DVN","FANG"],
    "Health Care": ["UNH","JNJ","LLY","ABBV","MRK","PFE","TMO","ABT","DHR","BMY",
                     "AMGN","CVS","MDT","ISRG","GILD","VRTX","ZTS","CI","HCA","ELV"],
    "Industrials": ["CAT","RTX","HON","UNP","BA","GE","DE","LMT","UPS","ETN",
                     "ADP","ITW","NOC","GD","EMR","WM","CSX","FDX","NSC","PH"],
    "Materials": ["LIN","APD","SHW","ECL","FCX","NUE","DOW","DD","PPG","VMC",
                  "MLM","ALB","CTVA","IFF","LYB"],
    "Consumer Staples": ["PG","KO","PEP","COST","WMT","PM","MO","MDLZ","CL","KMB",
                          "GIS","STZ","KDP","SYY","HSY"],
    "Consumer Discretionary": ["AMZN","TSLA","HD","MCD","NKE","LOW","SBUX","TJX","BKNG","CMG",
                                "ORLY","MAR","GM","F","ROST"],
    "Utilities": ["NEE","DUK","SO","D","AEP","EXC","SRE","XEL","PEG","ED",
                  "WEC","ES","AWK","DTE","PPL"],
    "Communication Services": ["GOOGL","META","NFLX","DIS","CMCSA","VZ","T","TMUS","CHTR","EA",
                                "TTWO","WBD","OMC"],
    "Real Estate": ["PLD","AMT","EQIX","CCI","PSA","O","WELL","SPG","DLR","AVB",
                     "EQR","VTR","INVH","EXR","SBAC"],
}

TOP_N_SECTORS = 3
TOP_N_SYMBOLS_PER_SECTOR = 10

RSI_PERIOD = 14
SMA_TREND = 200
SMA_SLOPE_LOOKBACK = 10
PCT_OFF_HIGH_MIN = 3.0
PCT_OFF_HIGH_MAX = 20.0
RSI_SWEET_MIN = 45.0
RSI_SWEET_MAX = 65.0
MACD_LOOKBACK = 5
REL_STRENGTH_LOOKBACK = 63

DTE_MIN = 21
DTE_MAX = 49

TARGET_ROR_PCT_MIN = 12.0
TARGET_ROR_PCT_SWEET = 18.0

TARGET_POP_PCT_MIN = 65.0
TARGET_POP_PCT_MAX = 85.0

MIN_WIDTH = 1.0
MAX_WIDTH = 15.0

SHORT_DELTA_MIN = -0.35
SHORT_DELTA_MAX = -0.06

MIN_OPEN_INTEREST = 50
MIN_BID = 0.05

RISK_FREE_RATE = 0.045


def config_snapshot() -> dict:
    """Everything worth freezing into scan_runs.config_snapshot so a
    historical run stays interpretable even if these constants change later."""
    return {
        "top_n_sectors": TOP_N_SECTORS,
        "top_n_symbols_per_sector": TOP_N_SYMBOLS_PER_SECTOR,
        "rsi_sweet_min": RSI_SWEET_MIN,
        "rsi_sweet_max": RSI_SWEET_MAX,
        "pct_off_high_min": PCT_OFF_HIGH_MIN,
        "pct_off_high_max": PCT_OFF_HIGH_MAX,
        "dte_min": DTE_MIN,
        "dte_max": DTE_MAX,
        "target_ror_pct_min": TARGET_ROR_PCT_MIN,
        "target_ror_pct_sweet": TARGET_ROR_PCT_SWEET,
        "target_pop_pct_min": TARGET_POP_PCT_MIN,
        "target_pop_pct_max": TARGET_POP_PCT_MAX,
        "short_delta_min": SHORT_DELTA_MIN,
        "short_delta_max": SHORT_DELTA_MAX,
        "min_open_interest": MIN_OPEN_INTEREST,
    }
