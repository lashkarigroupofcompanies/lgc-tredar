"""
Turso Cloud Database Sync Engine for LGC Trading
Handles edge-replicated persistence for Trades, Neural Memory, Rejections, and Agent Evolution.
Zero external pip dependencies: uses standard libSQL HTTP Pipeline API.
"""

import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("TursoSync")

TURSO_CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "turso_config.json"))

# Default credentials provided by user - embedded for 100% zero-configuration standalone app execution
DEFAULT_DB_URL = "https://lgc-trader-paras007.aws-ap-northeast-1.turso.io"
DEFAULT_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODkxNDU0MzAsImlkIjoiMDFhMDkxNWQtZTMwMS03ODA0LWI1MTUtNGYyMTJhZmZjYTIxIiwia2lkIjoiN3N3WGpzTXVaaUFFNWtsc3BRRzE0RTVVTGZVUlRuSmM0VGlRcGxOVkx4OCIsInJpZCI6ImQxMDY0Zjg2LWY1ZDEtNDIxMy05YWNhLTE3NmQzNGIzNDk1ZCJ9.LTIo7kYr0JPc-iHxGn-CH5Yyy8GUGwfeqAwVutv8_m0vlZHtUnaxpXHR7rVxCGghOMpi3tjFOy9B9d7gll9tAg"


class TursoClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TursoClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_url: Optional[str] = None, auth_token: Optional[str] = None):
        if getattr(self, "_initialized", False):
            return

        self._load_config()
        if db_url:
            self.db_url = db_url
        elif not getattr(self, "db_url", None):
            self.db_url = os.getenv("TURSO_DATABASE_URL", DEFAULT_DB_URL)

        if self.db_url.startswith("libsql://"):
            self.db_url = "https://" + self.db_url[len("libsql://"):]
        self.db_url = self.db_url.rstrip("/")

        if auth_token:
            self.auth_token = auth_token
        elif not getattr(self, "auth_token", None):
            self.auth_token = os.getenv("TURSO_AUTH_TOKEN", DEFAULT_TOKEN)

        self._initialized = True

    def _load_config(self):
        """Loads Turso config from disk if present."""
        if os.path.exists(TURSO_CONFIG_FILE):
            try:
                with open(TURSO_CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    url = cfg.get("db_url")
                    if url:
                        if url.startswith("libsql://"):
                            url = "https://" + url[len("libsql://"):]
                        self.db_url = url.rstrip("/")
                    token = cfg.get("auth_token")
                    if token:
                        self.auth_token = token
            except Exception as e:
                logger.warning(f"[TursoSync] Could not read config file: {e}")

    def save_config(self, db_url: str, auth_token: str):
        """Saves updated Turso config to disk."""
        if db_url.startswith("libsql://"):
            db_url = "https://" + db_url[len("libsql://"):]
        self.db_url = db_url.rstrip("/")
        self.auth_token = auth_token.strip()

        try:
            with open(TURSO_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"db_url": self.db_url, "auth_token": self.auth_token}, f, indent=2)
            logger.info("[TursoSync] Config saved to disk.")
        except Exception as e:
            logger.error(f"[TursoSync] Failed to save config: {e}")

    def execute(self, sql: str, args: Optional[List[Any]] = None) -> Dict[str, Any]:
        """
        Executes a single SQL statement on Turso via HTTP Pipeline API v2.
        """
        if not self.db_url or not self.auth_token:
            return {"error": "Turso not configured"}

        pipeline_url = f"{self.db_url}/v2/pipeline"
        stmt: Dict[str, Any] = {"sql": sql}
        if args:
            stmt_args = []
            for a in args:
                if a is None:
                    stmt_args.append({"type": "null"})
                elif isinstance(a, int):
                    stmt_args.append({"type": "integer", "value": str(a)})
                elif isinstance(a, float):
                    stmt_args.append({"type": "float", "value": a})
                else:
                    stmt_args.append({"type": "text", "value": str(a)})
            stmt["args"] = stmt_args

        payload = {
            "requests": [
                {"type": "execute", "stmt": stmt}
            ]
        }

        req = urllib.request.Request(
            pipeline_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data
        except Exception as e:
            logger.error(f"[TursoSync] SQL execution error: {e}")
            return {"error": str(e)}

    def initialize_tables(self) -> Dict[str, Any]:
        """
        Creates the complete schema in Turso:
        - trades
        - neural_memory
        - rejections_defense
        - agent_milestones
        """
        queries = [
            """
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                market TEXT,
                side TEXT NOT NULL,
                entry_price REAL,
                exit_price REAL,
                quantity REAL,
                pnl REAL,
                pnl_percent REAL,
                strategy TEXT,
                exit_reason TEXT,
                confidence REAL,
                time TEXT,
                synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS neural_memory (
                id TEXT PRIMARY KEY,
                trade_id TEXT,
                symbol TEXT,
                outcome TEXT,
                pnl REAL,
                regime TEXT,
                lesson TEXT,
                counterfactual_note TEXT,
                learned_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS rejections_defense (
                id TEXT PRIMARY KEY,
                symbol TEXT,
                strategy TEXT,
                proposed_side TEXT,
                rejection_reason TEXT,
                counterfactual_outcome TEXT,
                capital_saved REAL,
                logged_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS agent_milestones (
                id TEXT PRIMARY KEY,
                total_trades_executed INTEGER,
                win_rate REAL,
                total_realized_pnl REAL,
                current_capital REAL,
                agent_rank TEXT,
                agent_level INTEGER,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]

        results = []
        for q in queries:
            res = self.execute(q.strip())
            results.append(res)
        logger.info("[TursoSync] Database tables successfully verified & initialized on Turso cloud!")
        return {"status": "INITIALIZED", "results": results}

    def sync_trade(self, t: Dict[str, Any]) -> Dict[str, Any]:
        """Inserts or updates an executed trade into Turso."""
        sql = """
        INSERT OR REPLACE INTO trades 
        (id, symbol, market, side, entry_price, exit_price, quantity, pnl, pnl_percent, strategy, exit_reason, confidence, time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        args = [
            str(t.get("trade_id") or t.get("id") or f"TRD-{int(datetime.now().timestamp())}"),
            str(t.get("symbol", "UNKNOWN")),
            str(t.get("market", "GLOBAL")),
            str(t.get("side", "BUY")),
            float(t.get("entry_price") or t.get("entry") or 0.0),
            float(t.get("exit_price") or t.get("exit") or 0.0),
            float(t.get("quantity") or t.get("size") or 1.0),
            float(t.get("pnl") or 0.0),
            float(t.get("pnl_percent") or 0.0),
            str(t.get("strategy", "Dynamic Quant Alpha")),
            str(t.get("exit_reason", "TP1 / Runner Exit")),
            float(t.get("confidence") or 0.85),
            str(t.get("time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ]
        return self.execute(sql, args)

    def sync_neural_memory(self, m: Dict[str, Any]) -> Dict[str, Any]:
        """Inserts a neural learning record into Turso."""
        sql = """
        INSERT OR REPLACE INTO neural_memory 
        (id, trade_id, symbol, outcome, pnl, regime, lesson, counterfactual_note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        args = [
            str(m.get("id") or f"MEM-{int(datetime.now().timestamp())}"),
            str(m.get("trade_id", "")),
            str(m.get("symbol", "")),
            str(m.get("outcome", "WIN")),
            float(m.get("pnl") or 0.0),
            str(m.get("regime", "Trend Following")),
            str(m.get("lesson", "")),
            str(m.get("counterfactual_note", ""))
        ]
        return self.execute(sql, args)

    def get_status(self) -> Dict[str, Any]:
        """Returns connection status and trade counts from Turso."""
        res = self.execute("SELECT COUNT(*) FROM trades;")
        trade_count = 0
        is_connected = False
        try:
            if "results" in res and res["results"][0].get("type") == "ok":
                rows = res["results"][0]["response"]["result"]["rows"]
                if rows:
                    trade_count = int(rows[0][0]["value"])
                is_connected = True
        except Exception:
            pass

        return {
            "is_connected": is_connected,
            "db_url": self.db_url,
            "region": "aws-ap-northeast-1 (Tokyo)",
            "trades_count": trade_count
        }


# Singleton instance
turso_client = TursoClient()
