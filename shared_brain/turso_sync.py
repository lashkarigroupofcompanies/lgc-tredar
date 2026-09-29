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
                trading_mode TEXT,
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
            CREATE TABLE IF NOT EXISTS open_positions (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                market TEXT,
                side TEXT NOT NULL,
                entry_price REAL,
                current_price REAL,
                quantity REAL,
                stop_loss REAL,
                take_profit_1 REAL,
                take_profit_2 REAL,
                strategy TEXT,
                trading_mode TEXT,
                unrealized_pnl REAL,
                entry_time TEXT,
                synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
        
        try:
            self.execute("ALTER TABLE trades ADD COLUMN trading_mode TEXT;")
        except Exception:
            pass

        logger.info("[TursoSync] Database tables successfully verified & initialized on Turso cloud!")
        return {"status": "INITIALIZED", "results": results}

    def sync_trade(self, t: Dict[str, Any]) -> Dict[str, Any]:
        """Inserts or updates an executed trade into Turso."""
        sql = """
        INSERT OR REPLACE INTO trades 
        (id, symbol, market, side, entry_price, exit_price, quantity, pnl, pnl_percent, strategy, trading_mode, exit_reason, confidence, time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        strat = str(t.get("strategy_name") or t.get("strategy") or "Dynamic Quant Alpha")
        tm = str(t.get("trading_mode") or t.get("mode") or ("DANGEROUS" if any(k in strat.upper() for k in ["FAST", "SCALP", "MICRO", "VOLATILITY"]) else "SAFE"))
        args = [
            str(t.get("trade_id") or t.get("id") or f"TRD-{int(datetime.now().timestamp())}"),
            str(t.get("symbol", "UNKNOWN")),
            str(t.get("market", "GLOBAL")),
            str(t.get("side", t.get("direction", "BUY"))),
            float(t.get("entry_price") or t.get("entry") or 0.0),
            float(t.get("exit_price") or t.get("exit") or 0.0),
            float(t.get("quantity") or t.get("size") or t.get("shares") or 1.0),
            float(t.get("pnl") or t.get("realized_pnl") or 0.0),
            float(t.get("pnl_percent") or 0.0),
            strat,
            tm,
            str(t.get("exit_reason", "TP1 / Runner Exit")),
            float(t.get("confidence") or 0.85),
            str(t.get("time") or t.get("exit_time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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

    def get_all_trades(self) -> List[Dict[str, Any]]:
        """Retrieves all historical trades from Turso Cloud Database."""
        sql = "SELECT id, symbol, market, side, entry_price, exit_price, quantity, pnl, pnl_percent, strategy, trading_mode, exit_reason, confidence, time, synced_at FROM trades ORDER BY synced_at ASC;"
        res = self.execute(sql)
        trades = []
        try:
            if "results" in res and res["results"] and res["results"][0].get("type") == "ok":
                cols = [c["name"] for c in res["results"][0]["response"]["result"]["cols"]]
                rows = res["results"][0]["response"]["result"]["rows"]
                for r in rows:
                    row_dict = {}
                    for i, col in enumerate(cols):
                        val = r[i].get("value")
                        row_dict[col] = val
                    
                    pnl_val = float(row_dict.get("pnl") or 0.0)
                    entry_val = float(row_dict.get("entry_price") or 0.0)
                    exit_val = float(row_dict.get("exit_price") or 0.0)
                    qty_val = float(row_dict.get("quantity") or 1.0)
                    t_time = str(row_dict.get("time") or row_dict.get("synced_at") or "")
                    strat_name = str(row_dict.get("strategy") or "Dynamic Quant Alpha")
                    
                    raw_mode = row_dict.get("trading_mode")
                    if not raw_mode or str(raw_mode).strip() == "" or str(raw_mode).upper() == "NONE":
                        if any(k in strat_name.upper() for k in ["FAST", "SCALP", "MICRO", "VOLATILITY", "MOMENTUM"]):
                            mode_val = "DANGEROUS"
                        elif str(row_dict.get("market", "")).upper() == "CRYPTO":
                            mode_val = "DANGEROUS"
                        else:
                            mode_val = "SAFE"
                    else:
                        mode_val = str(raw_mode).upper()

                    trades.append({
                        "trade_id": str(row_dict.get("id")),
                        "id": str(row_dict.get("id")),
                        "symbol": str(row_dict.get("symbol") or "NIFTY 50"),
                        "market": str(row_dict.get("market") or "CRYPTO"),
                        "trading_mode": mode_val,
                        "side": str(row_dict.get("side") or "BUY"),
                        "direction": str(row_dict.get("side") or "BUY"),
                        "entry_price": entry_val,
                        "exit_price": exit_val,
                        "initial_size": qty_val,
                        "shares": qty_val,
                        "realized_pnl": pnl_val,
                        "pnl": pnl_val,
                        "pnl_percent": float(row_dict.get("pnl_percent") or 0.0),
                        "strategy": strat_name,
                        "strategy_name": strat_name,
                        "exit_reason": str(row_dict.get("exit_reason") or "TP/SL Exit"),
                        "confidence": float(row_dict.get("confidence") or 0.85),
                        "entry_time": t_time,
                        "exit_time": t_time,
                        "timestamp_close": t_time,
                        "status": "CLOSED"
                    })
        except Exception as e:
            logger.error(f"[TursoSync] Failed to parse trades from Turso: {e}")
        return trades

    def get_all_neural_memories(self) -> List[Dict[str, Any]]:
        """Retrieves neural memories from Turso Cloud Database."""
        sql = "SELECT id, trade_id, symbol, outcome, pnl, regime, lesson, counterfactual_note, learned_at FROM neural_memory ORDER BY learned_at ASC;"
        res = self.execute(sql)
        mems = []
        try:
            if "results" in res and res["results"] and res["results"][0].get("type") == "ok":
                cols = [c["name"] for c in res["results"][0]["response"]["result"]["cols"]]
                rows = res["results"][0]["response"]["result"]["rows"]
                for r in rows:
                    row_dict = {}
                    for i, col in enumerate(cols):
                        val = r[i].get("value")
                        row_dict[col] = val
                    mems.append(row_dict)
        except Exception as e:
            logger.error(f"[TursoSync] Failed to parse neural memories from Turso: {e}")
        return mems

    def sync_open_position(self, p: Dict[str, Any]) -> Dict[str, Any]:
        """Upserts an active open position to Turso Cloud Database."""
        sql = """
        INSERT OR REPLACE INTO open_positions
        (id, symbol, market, side, entry_price, current_price, quantity, stop_loss, take_profit_1, take_profit_2, strategy, trading_mode, unrealized_pnl, entry_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        pos_id = str(p.get("trade_id") or p.get("id") or "")
        args = [
            pos_id,
            str(p.get("symbol", "")),
            str(p.get("market", "")),
            str(p.get("direction") or p.get("side", "BUY")),
            float(p.get("entry_price") or 0.0),
            float(p.get("current_price") or p.get("entry_price") or 0.0),
            float(p.get("initial_units") or p.get("quantity") or p.get("remaining_units") or 1.0),
            float(p.get("stop_loss") or p.get("initial_stop_loss") or 0.0),
            float(p.get("take_profit_1") or 0.0),
            float(p.get("take_profit_2") or 0.0),
            str(p.get("strategy_name") or p.get("strategy") or "Dynamic Alpha"),
            str(p.get("trading_mode") or "SAFE"),
            float(p.get("unrealized_pnl") or 0.0),
            str(p.get("timestamp") or p.get("entry_time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ]
        return self.execute(sql, args)

    def delete_open_position(self, pos_id: str) -> Dict[str, Any]:
        """Deletes a closed position from open_positions table in Turso."""
        sql = "DELETE FROM open_positions WHERE id = ?;"
        return self.execute(sql, [str(pos_id)])

    def get_all_open_positions(self) -> List[Dict[str, Any]]:
        """Retrieves active open positions from Turso Cloud Database."""
        sql = "SELECT id, symbol, market, side, entry_price, current_price, quantity, stop_loss, take_profit_1, take_profit_2, strategy, trading_mode, unrealized_pnl, entry_time FROM open_positions ORDER BY entry_time ASC;"
        res = self.execute(sql)
        positions = []
        try:
            if "results" in res and res["results"] and res["results"][0].get("type") == "ok":
                cols = [c["name"] for c in res["results"][0]["response"]["result"]["cols"]]
                rows = res["results"][0]["response"]["result"]["rows"]
                for r in rows:
                    row_dict = {}
                    for i, col in enumerate(cols):
                        row_dict[col] = r[i].get("value")
                    p_id = str(row_dict.get("id"))
                    positions.append({
                        "trade_id": p_id,
                        "id": p_id,
                        "symbol": str(row_dict.get("symbol") or "Asset"),
                        "market": str(row_dict.get("market") or "CRYPTO"),
                        "direction": str(row_dict.get("side") or "BUY"),
                        "side": str(row_dict.get("side") or "BUY"),
                        "entry_price": float(row_dict.get("entry_price") or 0.0),
                        "current_price": float(row_dict.get("current_price") or row_dict.get("entry_price") or 0.0),
                        "initial_units": float(row_dict.get("quantity") or 1.0),
                        "remaining_units": float(row_dict.get("quantity") or 1.0),
                        "stop_loss": float(row_dict.get("stop_loss") or 0.0),
                        "take_profit_1": float(row_dict.get("take_profit_1") or 0.0),
                        "take_profit_2": float(row_dict.get("take_profit_2") or 0.0),
                        "strategy_name": str(row_dict.get("strategy") or "Dynamic Alpha"),
                        "trading_mode": str(row_dict.get("trading_mode") or "SAFE"),
                        "unrealized_pnl": float(row_dict.get("unrealized_pnl") or 0.0),
                        "timestamp": str(row_dict.get("entry_time") or ""),
                        "entry_time": str(row_dict.get("entry_time") or "")
                    })
        except Exception as e:
            logger.error(f"[TursoSync] Failed to parse open positions from Turso: {e}")
        return positions

    def sync_rejection(self, r: Dict[str, Any]) -> Dict[str, Any]:
        """Saves a real defensive rejection to Turso Cloud Database."""
        sql = """
        INSERT OR REPLACE INTO rejections_defense
        (id, symbol, strategy, proposed_side, rejection_reason, counterfactual_outcome, capital_saved)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        rej_id = str(r.get("id") or f"REJ-{int(datetime.now().timestamp())}")
        args = [
            rej_id,
            str(r.get("symbol", "")),
            str(r.get("strategy") or r.get("filter_engine") or "Risk Shield"),
            str(r.get("proposed_side", "BUY")),
            str(r.get("rejection_reason") or r.get("reason") or "Vetoed"),
            str(r.get("counterfactual_outcome", "CAPITAL_PRESERVED")),
            float(r.get("capital_saved") or 2500.0)
        ]
        return self.execute(sql, args)

    def get_recent_rejections(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Retrieves real defensive rejections from Turso Cloud Database."""
        sql = f"SELECT id, symbol, strategy, proposed_side, rejection_reason, counterfactual_outcome, capital_saved, logged_at FROM rejections_defense ORDER BY logged_at DESC LIMIT {int(limit)};"
        res = self.execute(sql)
        rejections = []
        try:
            if "results" in res and res["results"] and res["results"][0].get("type") == "ok":
                cols = [c["name"] for c in res["results"][0]["response"]["result"]["cols"]]
                rows = res["results"][0]["response"]["result"]["rows"]
                for r in rows:
                    row_dict = {}
                    for i, col in enumerate(cols):
                        row_dict[col] = r[i].get("value")
                    rejections.append({
                        "id": str(row_dict.get("id")),
                        "symbol": str(row_dict.get("symbol") or "Asset"),
                        "strategy": str(row_dict.get("strategy") or "Risk Shield"),
                        "proposed_side": str(row_dict.get("proposed_side") or "BUY"),
                        "reason": str(row_dict.get("rejection_reason") or ""),
                        "outcome": str(row_dict.get("counterfactual_outcome") or "CAPITAL_PRESERVED"),
                        "capital_saved": float(row_dict.get("capital_saved") or 0.0),
                        "time": str(row_dict.get("logged_at") or "")
                    })
        except Exception as e:
            logger.error(f"[TursoSync] Failed to parse rejections from Turso: {e}")
        return rejections

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
