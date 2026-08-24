"""SQLite persistence for real crossover observations and next-day evaluation."""
from __future__ import annotations
import os, sqlite3
from config import DATA_DIR

DB = os.path.join(DATA_DIR, "market_learning.db")

class LearningStore:
    def __init__(self, path=DB):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        self._init()

    def conn(self):
        c = sqlite3.connect(self.path, check_same_thread=False)
        c.row_factory = sqlite3.Row
        return c

    def _init(self):
        with self.conn() as c:
            c.execute('''CREATE TABLE IF NOT EXISTS crossovers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,timestamp REAL,symbol TEXT,signal TEXT,ltp REAL,ltq INTEGER,
            ltq_avg_2m REAL,ltq_avg_5m REAL,ltq_ratio_2_5 REAL,ltq_spike_ratio REAL,
            etq_5 REAL,etq_20 REAL,etq_60 REAL,bid_qty REAL,ask_qty REAL,bid REAL,ask REAL,
            bid_ask_imbalance REAL,directional_imbalance REAL,spread_pct REAL,smma_20 REAL,smma_120 REAL,
            smma_sep_pct REAL,avg_ltp_20 REAL,avg_ltp_60 REAL,price_vs_avg20_pct REAL,price_vs_avg60_pct REAL,
            direction INTEGER,ml_probability REAL,ml_accepted INTEGER,exit_time REAL,exit_ltp REAL,pnl REAL,
            profitable INTEGER,day TEXT,closed INTEGER DEFAULT 0)''')

    def add_signal(self, row, signal, pred):
        f = pred.features if pred else {}
        ts = float(row.get("timestamp") or row["_tick"].ts)
        day = __import__("datetime").datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
        # None means ML was unavailable. False/0 must mean the trained model explicitly rejected it.
        ml_accepted = None if pred is None or not pred.available else int(pred.accept)
        ml_probability = None if pred is None or not pred.available else pred.probability
        vals = (
            ts,row["symbol"],signal,row["ltp"],row.get("ltq",0),f.get("ltq_avg_2m",0),f.get("ltq_avg_5m",0),
            f.get("ltq_ratio_2_5",1),f.get("ltq_spike_ratio",1),row.get("etq_5",0),row.get("etq_20",0),row.get("etq_60",0),
            row.get("bid_qty",0),row.get("ask_qty",0),row.get("bid",0),row.get("ask",0),f.get("bid_ask_imbalance",0),
            f.get("directional_imbalance",0),f.get("spread_pct",0),row.get("smma_20",0),row.get("smma_120",0),f.get("smma_sep_pct",0),
            row.get("avg_ltp_20",0),row.get("avg_ltp_60",0),f.get("price_vs_avg20_pct",0),f.get("price_vs_avg60_pct",0),
            f.get("direction",1),ml_probability,ml_accepted,day
        )
        with self.conn() as c:
            cur = c.execute('''INSERT INTO crossovers(
                timestamp,symbol,signal,ltp,ltq,ltq_avg_2m,ltq_avg_5m,ltq_ratio_2_5,ltq_spike_ratio,
                etq_5,etq_20,etq_60,bid_qty,ask_qty,bid,ask,bid_ask_imbalance,directional_imbalance,
                spread_pct,smma_20,smma_120,smma_sep_pct,avg_ltp_20,avg_ltp_60,price_vs_avg20_pct,
                price_vs_avg60_pct,direction,ml_probability,ml_accepted,day)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', vals)
            return cur.lastrowid

    def close_previous(self, symbol, exit_time, exit_ltp):
        with self.conn() as c:
            # Close the most recent still-open hypothetical crossover for this symbol.
            r = c.execute('SELECT * FROM crossovers WHERE symbol=? AND closed=0 ORDER BY timestamp DESC LIMIT 1', (symbol,)).fetchone()
            if not r:
                return None
            pnl = (exit_ltp-r["ltp"]) if r["signal"] == "BUY" else (r["ltp"]-exit_ltp)
            prof = int(pnl > 0)
            c.execute('UPDATE crossovers SET exit_time=?,exit_ltp=?,pnl=?,profitable=?,closed=1 WHERE id=?',
                      (exit_time, exit_ltp, pnl, prof, r["id"]))
            return dict(r) | {"exit_time": exit_time, "exit_ltp": exit_ltp, "pnl": pnl, "profitable": prof}

    def history(self, closed_only=True):
        q = "SELECT * FROM crossovers"
        if closed_only:
            q += " WHERE closed=1 AND profitable IS NOT NULL"
        q += " ORDER BY timestamp"
        with self.conn() as c:
            return [dict(r) for r in c.execute(q).fetchall()]

    def recent(self, limit=100):
        with self.conn() as c:
            return [dict(r) for r in c.execute("SELECT * FROM crossovers ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()]

    def evaluation(self, day=None):
        q = "SELECT * FROM crossovers WHERE closed=1"
        args = []
        if day:
            q += " AND day=?"; args.append(day)
        with self.conn() as c:
            rows = [dict(r) for r in c.execute(q, args).fetchall()]
        total = len(rows)
        wins = sum(r["profitable"] == 1 for r in rows)
        losses = sum(r["profitable"] == 0 for r in rows)
        evaluated = [r for r in rows if r["ml_accepted"] is not None]
        accepted = [r for r in evaluated if r["ml_accepted"] == 1]
        avoided = [r for r in evaluated if r["ml_accepted"] == 0]
        accepted_wins = sum(r["profitable"] == 1 for r in accepted)
        accepted_losses = sum(r["profitable"] == 0 for r in accepted)
        avoided_losses = sum(r["profitable"] == 0 for r in avoided)
        avoided_wins = sum(r["profitable"] == 1 for r in avoided)
        pnl_all = sum(float(r["pnl"] or 0) for r in rows)
        pnl_accepted = sum(float(r["pnl"] or 0) for r in accepted)
        pnl_baseline = pnl_all
        return {
            "total": total, "wins": wins, "losses": losses, "overall_win_rate": wins/total if total else 0,
            "evaluated": len(evaluated), "accepted": len(accepted), "avoided": len(avoided),
            "avoidance_rate": len(avoided)/len(evaluated) if evaluated else 0,
            "accepted_win_rate": accepted_wins/len(accepted) if accepted else 0,
            "accepted_loss_rate": accepted_losses/len(accepted) if accepted else 0,
            "accepted_wins": accepted_wins, "accepted_losses": accepted_losses,
            "avoided_losses": avoided_losses, "avoided_wins": avoided_wins,
            "avoided_loss_capture": avoided_losses/losses if losses else 0,
            "avoided_correct_rate": avoided_losses/len(avoided) if avoided else 0,
            "overall_loss_rate": losses/total if total else 0,
            "pnl_baseline": pnl_baseline, "pnl_accepted": pnl_accepted,
        }

    def day_stats(self, day=None):
        e = self.evaluation(day)
        return {"total":e["total"],"evaluated":e["evaluated"],"avoided":e["avoided"],"accepted":e["accepted"],
                "avoidance_rate":e["avoidance_rate"],"avoided_loss_capture":e["avoided_loss_capture"],
                "wins":e["wins"],"losses":e["losses"],"win_rate":e["overall_win_rate"],
                "accepted_win_rate":e["accepted_win_rate"],"accepted_loss_rate":e["accepted_loss_rate"],
                "pnl":e["pnl_baseline"]}
