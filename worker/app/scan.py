"""
Core scan logic for the sector rotation income scanner.

This is a direct port of sector_rotation_bull_put_finder.py's technical
scoring and option-screen functions. The math is UNCHANGED -- only the
output shape changed, from print()/DataFrame/CSV to plain dicts that
main.py inserts into Supabase.
"""

import math
import datetime as dt
import pandas as pd
import numpy as np
from scipy.stats import norm

from . import config as cfg

# Yahoo Finance increasingly blocks requests that don't look like a real
# browser -- this is especially common from cloud/datacenter IPs (Railway,
# AWS, etc.), even when the exact same code works fine locally or in
# Colab. curl_cffi's impersonate mode makes the underlying TLS/HTTP
# fingerprint match a real Chrome install, which is yfinance's own
# currently-recommended workaround. This is NOT a guaranteed fix --
# Yahoo can still tighten blocking further -- but it's the best available
# option short of a paid market-data API.
_session = None


def _get_session():
    global _session
    if _session is None:
        from curl_cffi import requests as cffi_requests
        _session = cffi_requests.Session(impersonate="chrome")
    return _session


def compute_rsi(closes, period=cfg.RSI_PERIOD):
    delta = closes.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_macd_hist(closes):
    ema12 = closes.ewm(span=12, adjust=False).mean()
    ema26 = closes.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line - signal


def fetch_price_history(ticker, period="1y"):
    import yfinance as yf
    df = yf.download(
        ticker, period=period, progress=False, auto_adjust=True,
        session=_get_session(),
    )
    if df.empty or len(df) < cfg.SMA_TREND + cfg.SMA_SLOPE_LOOKBACK:
        return None
    df = df[["Close"]].rename(columns={"Close": "close"})
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["close"]
    return df


def momentum_score(closes, spy_closes):
    sma200 = closes.rolling(cfg.SMA_TREND).mean()
    if pd.isna(sma200.iloc[-1]) or pd.isna(sma200.iloc[-1 - cfg.SMA_SLOPE_LOOKBACK]):
        return None, None

    price = float(closes.iloc[-1])
    sma200_now = float(sma200.iloc[-1])
    sma200_then = float(sma200.iloc[-1 - cfg.SMA_SLOPE_LOOKBACK])

    if not (price > sma200_now and sma200_now > sma200_then):
        return None, None

    rsi = float(compute_rsi(closes).iloc[-1])
    high_52w = float(closes.rolling(min(len(closes), 252)).max().iloc[-1])
    pct_off_high = (high_52w - price) / high_52w * 100

    macd_hist = compute_macd_hist(closes)
    macd_rising = float(macd_hist.iloc[-1]) > float(macd_hist.iloc[-1 - cfg.MACD_LOOKBACK])

    if len(closes) > cfg.REL_STRENGTH_LOOKBACK and len(spy_closes) > cfg.REL_STRENGTH_LOOKBACK:
        stock_ret = price / float(closes.iloc[-1 - cfg.REL_STRENGTH_LOOKBACK]) - 1
        spy_ret = float(spy_closes.iloc[-1]) / float(spy_closes.iloc[-1 - cfg.REL_STRENGTH_LOOKBACK]) - 1
        rel_strength = stock_ret - spy_ret
    else:
        rel_strength = 0.0

    if cfg.RSI_SWEET_MIN <= rsi <= cfg.RSI_SWEET_MAX:
        rsi_score = 1.0
    else:
        rsi_score = max(0.0, 1.0 - abs(rsi - (cfg.RSI_SWEET_MIN + cfg.RSI_SWEET_MAX) / 2) / 30.0)

    if cfg.PCT_OFF_HIGH_MIN <= pct_off_high <= cfg.PCT_OFF_HIGH_MAX:
        off_high_score = 1.0
    else:
        mid = (cfg.PCT_OFF_HIGH_MIN + cfg.PCT_OFF_HIGH_MAX) / 2
        off_high_score = max(0.0, 1.0 - abs(pct_off_high - mid) / 25.0)

    macd_score = 1.0 if macd_rising else 0.2
    relstr_score = 1.0 if rel_strength > 0 else max(0.0, 0.5 + rel_strength * 5)

    score = 0.30 * rsi_score + 0.25 * off_high_score + 0.20 * macd_score + 0.25 * relstr_score

    detail = {
        "rsi": round(rsi, 1),
        "pct_off_52w_high": round(pct_off_high, 1),
        "macd_rising": macd_rising,
        "rel_strength_3m_pct": round(rel_strength * 100, 1),
        "score": round(score, 3),
    }
    return score, detail


def rank_sectors():
    spy_df = fetch_price_history("SPY", period="1y")
    if spy_df is None:
        raise RuntimeError("Could not fetch SPY history for relative strength baseline.")
    spy_closes = spy_df["close"]

    rows = []
    for sector, etf in cfg.SECTOR_ETFS.items():
        df = fetch_price_history(etf, period="1y")
        base = {"sector": sector, "etf": etf}
        if df is None:
            rows.append({**base, "passed_gate": False})
            continue
        score, detail = momentum_score(df["close"], spy_closes)
        if score is None:
            rows.append({**base, "passed_gate": False})
            continue
        rows.append({**base, "passed_gate": True, **detail})

    passed = [r for r in rows if r["passed_gate"]]
    passed.sort(key=lambda r: r["score"], reverse=True)
    for i, r in enumerate(passed):
        r["rank"] = i + 1
        r["is_top_3"] = i < cfg.TOP_N_SECTORS

    gated = [r for r in rows if not r["passed_gate"]]
    for r in gated:
        r["rank"] = None
        r["is_top_3"] = False

    return passed + gated, spy_closes


def rank_symbols_in_sector(sector, spy_closes, top_n=cfg.TOP_N_SYMBOLS_PER_SECTOR):
    candidates = cfg.SECTOR_CANDIDATES.get(sector, [])
    rows = []
    for sym in candidates:
        df = fetch_price_history(sym, period="1y")
        if df is None:
            continue
        score, detail = momentum_score(df["close"], spy_closes)
        if score is None:
            continue
        rows.append({"symbol": sym, "sector": sector, **detail})
    rows.sort(key=lambda r: r["score"], reverse=True)
    ranked = rows[:top_n]
    for i, r in enumerate(ranked):
        r["rank"] = i + 1
    return ranked


# ----------------------------------------------------------------------
# OPTION SCREEN (unchanged from the Colab version)
# ----------------------------------------------------------------------
def bs_put_delta_and_pop(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return None, None
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    put_delta = norm.cdf(d1) - 1
    pop = norm.cdf(d2)
    return put_delta, pop


def get_risk_free_rate():
    try:
        import yfinance as yf
        irx = yf.Ticker("^IRX", session=_get_session()).history(period="5d")["Close"].iloc[-1]
        return round(irx / 100.0, 4)
    except Exception:
        return cfg.RISK_FREE_RATE


def fetch_put_chains(ticker, dte_min, dte_max):
    import yfinance as yf
    tk = yf.Ticker(ticker, session=_get_session())
    try:
        spot = tk.fast_info["lastPrice"]
    except Exception:
        hist = tk.history(period="1d")
        if hist.empty:
            return []
        spot = float(hist["Close"].iloc[-1])

    today = dt.date.today()
    out = []
    for exp_str in tk.options:
        exp_date = dt.datetime.strptime(exp_str, "%Y-%m-%d").date()
        dte = (exp_date - today).days
        if dte < dte_min or dte > dte_max:
            continue
        try:
            chain = tk.option_chain(exp_str)
        except Exception:
            continue
        puts = chain.puts.copy()
        if puts.empty:
            continue
        out.append((exp_str, dte, puts, spot))
    return out


def screen_ticker(ticker, r, sector):
    results = []
    chains = fetch_put_chains(ticker, cfg.DTE_MIN, cfg.DTE_MAX)

    for exp_str, dte, puts, spot in chains:
        T = dte / 365.0
        puts = puts.copy()
        puts = puts[(puts["bid"] >= cfg.MIN_BID) & (puts["openInterest"] >= 0)]
        puts = puts.sort_values("strike").reset_index(drop=True)

        deltas, pops = [], []
        for _, row in puts.iterrows():
            iv = row.get("impliedVolatility", np.nan)
            if pd.isna(iv) or iv <= 0:
                deltas.append(None); pops.append(None); continue
            d, p = bs_put_delta_and_pop(spot, row["strike"], T, r, iv)
            deltas.append(d); pops.append(p)
        puts["delta"] = deltas
        puts["pop"] = pops

        shorts = puts[
            puts["delta"].notna()
            & (puts["delta"] >= cfg.SHORT_DELTA_MIN)
            & (puts["delta"] <= cfg.SHORT_DELTA_MAX)
            & (puts["openInterest"] >= cfg.MIN_OPEN_INTEREST)
        ]

        for _, short_row in shorts.iterrows():
            short_strike = short_row["strike"]
            longs = puts[
                (puts["strike"] < short_strike)
                & (puts["strike"] >= short_strike - cfg.MAX_WIDTH)
                & (puts["strike"] <= short_strike - cfg.MIN_WIDTH)
            ]
            for _, long_row in longs.iterrows():
                width = short_strike - long_row["strike"]
                credit = short_row["bid"] - long_row["ask"]
                if credit <= 0 or width <= 0:
                    continue
                max_loss = width - credit
                if max_loss <= 0:
                    continue
                ror = (credit / max_loss) * 100
                pop = short_row["pop"] * 100 if short_row["pop"] is not None else None
                if pop is None:
                    continue
                if ror < cfg.TARGET_ROR_PCT_MIN:
                    continue
                if not (cfg.TARGET_POP_PCT_MIN <= pop <= cfg.TARGET_POP_PCT_MAX):
                    continue

                results.append({
                    "sector": sector,
                    "symbol": ticker,
                    "expiration": exp_str,
                    "dte": dte,
                    "spot": round(float(spot), 2),
                    "short_strike": float(short_strike),
                    "long_strike": float(long_row["strike"]),
                    "width": round(float(width), 2),
                    "credit": round(float(credit), 2),
                    "max_loss": round(float(max_loss), 2),
                    "ror_pct": round(float(ror), 1),
                    "in_sweet_spot": ror >= cfg.TARGET_ROR_PCT_SWEET,
                    "pop_pct": round(float(pop), 1),
                    "short_delta": round(float(short_row["delta"]), 3),
                    "short_oi": int(short_row["openInterest"]),
                    "short_iv": round(float(short_row["impliedVolatility"]) * 100, 1),
                })
    return results


# ----------------------------------------------------------------------
# PIPELINE ENTRY POINT
# ----------------------------------------------------------------------
def run_full_scan(progress_cb=None):
    """Runs the full pipeline and returns (sector_rows, symbol_rows,
    trade_rows, risk_free_rate). progress_cb, if given, is called with a
    short status string after each major step -- main.py wires this to a
    scan_runs status update so the UI can poll something better than
    silence during a multi-minute run."""

    def note(msg):
        if progress_cb:
            progress_cb(msg)

    note("ranking sectors")
    sector_rows, spy_closes = rank_sectors()

    top_sectors = [r["sector"] for r in sector_rows if r.get("is_top_3")]

    symbol_rows = []
    for sector in top_sectors:
        note(f"ranking symbols in {sector}")
        symbol_rows.extend(rank_symbols_in_sector(sector, spy_closes))

    note("fetching risk-free rate")
    r = get_risk_free_rate()

    trade_rows = []
    for row in symbol_rows:
        note(f"screening {row['symbol']} ({row['sector']})")
        trade_rows.extend(screen_ticker(row["symbol"], r, row["sector"]))

    note("done")
    return sector_rows, symbol_rows, trade_rows, r
