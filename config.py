"""Central configuration. Credentials are read only from environment variables."""
from __future__ import annotations
import os
from dotenv import load_dotenv
from dataclasses import dataclass, field

load_dotenv()

MODE = os.getenv("SCREENER_MODE", "fyers").lower()
FYERS_APP_ID = os.getenv("FYERS_APP_ID", "")
FYERS_ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN", "")
FYERS_SECRET = os.getenv("FYERS_SECRET", "")
FYERS_REDIRECT_URI = os.getenv("FYERS_REDIRECT_URI", "https://trade.fyers.in/api-login/redirect-uri/index.html")
FYERS_SYMBOL_MASTER_URL = os.getenv("FYERS_SYMBOL_MASTER_URL", "https://public.fyers.in/sym_details/NSE_CM.csv")

LTP_MIN = float(os.getenv("LTP_MIN", "30"))
LTP_MAX = float(os.getenv("LTP_MAX", "500"))
MIN_BID_QTY = int(os.getenv("MIN_BID_QTY", "1000000"))
MIN_ASK_QTY = int(os.getenv("MIN_ASK_QTY", "1000000"))
SMMA_FAST = int(os.getenv("SMMA_FAST", "20"))
SMMA_SLOW = int(os.getenv("SMMA_SLOW", "120"))
WINDOWS_MIN = [5, 20, 60]
REFRESH_INTERVAL = float(os.getenv("REFRESH_INTERVAL", "2"))
SCREEN_INTERVAL = float(os.getenv("SCREEN_INTERVAL", "300"))
MAX_SYMBOLS = int(os.getenv("MAX_SYMBOLS", "5000"))
ML_THRESHOLD = float(os.getenv("ML_THRESHOLD", "0.60"))
MIN_TRAIN_ROWS = int(os.getenv("MIN_TRAIN_ROWS", "40"))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data_store"))
MODEL_DIR = os.getenv("MODEL_DIR", os.path.join(os.path.dirname(__file__), "models"))

MOCK_SYMBOLS = [
    "NSE:SBIN-EQ", "NSE:TATASTEEL-EQ", "NSE:ONGC-EQ", "NSE:NTPC-EQ",
    "NSE:POWERGRID-EQ", "NSE:COALINDIA-EQ", "NSE:ITC-EQ", "NSE:IOC-EQ",
    "NSE:BPCL-EQ", "NSE:HINDALCO-EQ", "NSE:JSWSTEEL-EQ", "NSE:VEDL-EQ",
    "NSE:GAIL-EQ", "NSE:SAIL-EQ", "NSE:NMDC-EQ", "NSE:NATIONALUM-EQ",
    "NSE:BANKBARODA-EQ", "NSE:PNB-EQ", "NSE:CANBK-EQ", "NSE:UNIONBANK-EQ",
]

@dataclass
class RuntimeConfig:
    mode: str = MODE
    ltp_min: float = LTP_MIN
    ltp_max: float = LTP_MAX
    min_bid: int = MIN_BID_QTY
    min_ask: int = MIN_ASK_QTY
    smma_fast: int = SMMA_FAST
    smma_slow: int = SMMA_SLOW
    windows: list = field(default_factory=lambda: WINDOWS_MIN.copy())
    refresh: float = REFRESH_INTERVAL
    screen_interval: float = SCREEN_INTERVAL
    max_symbols: int = MAX_SYMBOLS
    ml_threshold: float = ML_THRESHOLD
    min_train_rows: int = MIN_TRAIN_ROWS

cfg = RuntimeConfig()
cfg.model_dir = MODEL_DIR
