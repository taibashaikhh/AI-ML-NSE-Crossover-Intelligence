from __future__ import annotations
import os, time
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from config import cfg
from data.provider_factory import create_provider
from learning import LearningManager
from trade_engine import PaperTradeEngine

st.set_page_config(page_title="AI/ML NSE Crossover Intelligence", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
.block-container{padding-top:1rem}.hero{padding:24px 28px;border-radius:20px;background:linear-gradient(135deg,#101828,#1d2939);color:white;margin-bottom:18px}.hero h1{margin:0;font-size:2.05rem}.hero p{margin:.45rem 0 0;color:#d0d5dd}.pill{display:inline-block;padding:5px 10px;border-radius:999px;background:#344054;color:#fff;font-size:.8rem;margin:4px 6px 0 0}.good{color:#12b76a}.bad{color:#f04438}.muted{color:#98a2b3}.small{font-size:.85rem}.section{margin-top:12px}
</style>""", unsafe_allow_html=True)

@st.cache_resource
def services():
    return create_provider(), LearningManager(), PaperTradeEngine()

provider, learn, engine = services()

with st.sidebar:
    st.header("⚙ Controls")
    threshold = st.slider("ML acceptance threshold", 0.50, 0.90, float(cfg.ml_threshold), 0.01)
    auto = st.toggle("Auto refresh", True)
    if st.button("🧠 Train from previous trading days"):
        result = learn.train_previous_days()
        st.success(str(result)) if result.get("status") == "trained" else st.warning(str(result))
    st.caption("Paper trading only. No broker orders are sent.")
    st.caption(f"Live source: **{cfg.mode.upper()}**")
    st.divider(); st.markdown("**Assignment filters**")
    st.write(f"LTP: ₹{cfg.ltp_min:.0f}–₹{cfg.ltp_max:.0f}")
    st.write(f"Bid Qty > {cfg.min_bid:,}")
    st.write(f"Ask Qty > {cfg.min_ask:,}")
    st.write(f"SMMA: {cfg.smma_fast}/{cfg.smma_slow}")

try:
    rows = provider.snapshot()
except Exception as e:
    st.error(f"Provider could not start: {e}"); st.stop()

for r in rows:
    if r.get("signal"):
        pred = learn.model.predict(r, r["signal"], threshold)
        learn.process(r, pred)
        engine.process_crossover(r["symbol"], r["signal"], r["ltp"], r["timestamp"], pred.probability if pred.available else None, pred.accept if pred.available else False)

status = provider.status() if hasattr(provider, "status") else {}
eval_all = learn.stats()
model = learn.model
price_candidates = status.get("price_candidates", 0)
liquidity_qualified = status.get("liquidity_qualified", 0)
depth_checked = status.get("depth_checked", 0)
depth_pending = status.get("depth_pending", 0)
depth_complete = status.get("depth_scan_complete", False)
ws_label = "CONNECTED" if status.get("websocket_connected") else "WAITING"
scan_label = "COMPLETE" if depth_complete else f"IN PROGRESS ({depth_checked} checked, {depth_pending} pending)"

st.markdown(f'''<div class="hero"><h1>📈 AI/ML NSE Crossover Intelligence</h1><p>FYERS live exchange data → LTP & liquidity screening → LTQ/ETQ → SMMA crossover → next-day neural-network decision → outcome validation</p><div style="margin-top:10px"><span class="pill">{cfg.mode.upper()} DATA</span><span class="pill">PAPER TRADING</span><span class="pill">NO BROKER ORDERS</span><span class="pill">DEPTH {scan_label}</span></div></div>''', unsafe_allow_html=True)

c = st.columns(6)
c[0].metric("Live rows", len(rows))
c[1].metric("LTP-qualified", price_candidates)
c[2].metric("Liquidity-qualified", liquidity_qualified)
c[3].metric("Closed crossovers", eval_all["total"])
c[4].metric("ML avoided", eval_all["avoided"])
c[5].metric("Accepted win rate", f"{eval_all['accepted_win_rate']:.1%}" if eval_all["accepted"] else "—")
st.caption(f"FYERS universe: {status.get('universe',0)} · LTP-qualified: {price_candidates} · Liquidity-qualified: {liquidity_qualified} · Depth scan: {scan_label} · WebSocket: {ws_label}")

st.subheader("🔎 Live Stock Screening")
if rows:
    data=[]
    for r in rows:
        pred=model.predict(r, r.get("signal"), threshold) if r.get("signal") else None
        data.append({
            "Symbol":r["symbol"],"LTP":r["ltp"],"Bid":r["bid"],"Bid Qty":r["bid_qty"],"Ask":r["ask"],"Ask Qty":r["ask_qty"],
            "SMMA 20":r["smma_20"],"SMMA 120":r["smma_120"],"ETQ 5m":r["etq_5"],"ETQ 20m":r["etq_20"],"ETQ 60m":r["etq_60"],
            "Avg LTP 20m":r["avg_ltp_20"],"Avg LTP 60m":r["avg_ltp_60"],"LTQ":r["ltq"],"LTQ 2m/5m":r["ltq_ratio_2_5"],
            "Signal":r.get("signal") or "—","AI":("ACCEPT" if pred and pred.available and pred.accept else "AVOID" if pred and pred.available else "WAIT"),
            "P(profit)":pred.probability if pred and pred.available else None,"Explanation":pred.reason if pred else "No crossover at this moment"
        })
    df=pd.DataFrame(data)
    st.dataframe(df,use_container_width=True,height=520,column_config={
        "LTP":st.column_config.NumberColumn(format="₹%.2f"),"Bid":st.column_config.NumberColumn(format="₹%.2f"),"Ask":st.column_config.NumberColumn(format="₹%.2f"),
        "P(profit)":st.column_config.ProgressColumn("P(profit)",min_value=0,max_value=1,format="%.0f%%"),"Explanation":st.column_config.TextColumn(width="large")})
else:
    st.info("No live rows currently pass all filters. If the depth scan is still in progress, this is not a final zero result.")

st.subheader("🧠 Deep Learning / Next-Day Validation")
if not model.available:
    st.warning(f"Model status: NOT READY. No synthetic data is used. Collect and close real crossover outcomes from a previous trading day; then train before the next session. Minimum labeled outcomes: {cfg.min_train_rows}.")
else:
    m=st.columns(6)
    m[0].metric("Model", "READY")
    m[1].metric("Training rows", model.training_rows)
    m[2].metric("Training day", model.training_day or "—")
    m[3].metric("Validation accuracy", f"{model.metrics.get('accuracy',0):.1%}")
    m[4].metric("Precision", f"{model.metrics.get('precision',0):.1%}")
    roc_auc = model.metrics.get("roc_auc")

if roc_auc is None:
    roc_auc_display = "N/A"
else:
    roc_auc_display = f"{float(roc_auc):.2f}"

    m[5].metric("ROC-AUC", roc_auc_display)
    st.success(f"Deployment model trained only from closed real outcomes dated up to {model.training_day}. Current session is the validation/application day.")

st.subheader("📊 Analysis Result — Does AI + LTQ Improve the Crossover Strategy?")
if eval_all["evaluated"]:
    a=st.columns(8)
    a[0].metric("All crossovers", eval_all["total"])
    a[1].metric("ML evaluated", eval_all["evaluated"])
    a[2].metric("ML avoided", eval_all["avoided"])
    a[3].metric("Avoidance rate", f"{eval_all['avoidance_rate']:.1%}")
    a[4].metric("Avoided losses", eval_all["avoided_losses"])
    a[5].metric("Losses avoided %", f"{eval_all['avoided_loss_capture']:.1%}")
    a[6].metric("Accepted win rate", f"{eval_all['accepted_win_rate']:.1%}")
    a[7].metric("Accepted loss rate", f"{eval_all['accepted_loss_rate']:.1%}")

    comparison=pd.DataFrame([
        ["Signals",eval_all["total"],eval_all["accepted"]],
        ["Profitable",eval_all["wins"],eval_all["accepted_wins"]],
        ["Losses",eval_all["losses"],eval_all["accepted_losses"]],
        ["Win rate",eval_all["overall_win_rate"],eval_all["accepted_win_rate"]],
        ["Loss rate",eval_all["overall_loss_rate"],eval_all["accepted_loss_rate"]],
        ["P/L",eval_all["pnl_baseline"],eval_all["pnl_accepted"]],
    ],columns=["Metric","SMMA baseline","AI + LTQ accepted"])
    st.dataframe(comparison,use_container_width=True,hide_index=True,column_config={
        "Win rate":st.column_config.NumberColumn(format="%.1%"),"Loss rate":st.column_config.NumberColumn(format="%.1%"),"P/L":st.column_config.NumberColumn(format="₹%.2f")})
    st.caption("Baseline = every closed crossover treated as a hypothetical trade. AI + LTQ = only model-accepted signals. 'Losses avoided %' = losing baseline crossovers that the trained model rejected ÷ all baseline losses.")
else:
    st.info("Analysis results will populate after real crossover signals have been closed at their opposite SMMA crossover. No fabricated performance numbers are shown.")

hist=pd.DataFrame(learn.store.recent(250))
if not hist.empty:
    st.subheader("📌 Crossover Outcome Audit Trail")
    show=hist[[c for c in ['timestamp','symbol','signal','ltp','ltq','ltq_avg_2m','ltq_avg_5m','etq_5','etq_20','etq_60','bid_qty','ask_qty','ml_probability','ml_accepted','exit_ltp','pnl','profitable','closed'] if c in hist.columns]].copy()
    if "timestamp" in show: show["timestamp"]=pd.to_datetime(show.timestamp,unit="s").dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(show,use_container_width=True,height=380)

if model.available:
    st.subheader("🔬 What the Neural Network Learns From")
    hist2=pd.DataFrame(learn.store.history(True))
    try:
        imp=model.permutation_importance(hist2)
        if not imp.empty:
            impdf=imp.reset_index(); impdf.columns=["Feature","Importance"]
            st.plotly_chart(px.bar(impdf,x="Importance",y="Feature",orientation="h",title="Feature importance on real validation history"),use_container_width=True)
    except Exception as e:
        st.caption(f"Feature importance will become available after enough real validation rows: {e}")

st.subheader("⚠️ Example of an ML Avoidance")
if not hist.empty and "ml_accepted" in hist.columns:
    examples=hist[(hist.closed==1)&hist.ml_accepted.notna()]
    if not examples.empty:
        ex=examples.sort_values("timestamp",ascending=False).iloc[0]
        outcome="LOSS — correct avoidance" if ex.profitable==0 and ex.ml_accepted==0 else "PROFIT — avoided a winning signal" if ex.profitable==1 and ex.ml_accepted==0 else "Accepted trade"
        st.info(f"{ex.symbol} {ex.signal} at ₹{ex.ltp:.2f} · ML P(profit)={ex.ml_probability:.1%} · Decision={'ACCEPT' if ex.ml_accepted else 'AVOID'} · Actual outcome={outcome} · P/L=₹{ex.pnl:.2f}")
    else:
        st.caption("A concrete ML avoidance example will appear after the first trained model evaluates and closes a real crossover.")

with st.expander("ℹ Technical / audit status"):
    st.write({"provider":cfg.mode,"websocket":status,"database":learn.store.path,"model_file":os.path.join(cfg.model_dir,"next_day_mlp.joblib"),"data_policy":"real FYERS data; no synthetic training data"})

st.caption(f"Last refresh {datetime.now().strftime('%H:%M:%S')} · Refresh interval {cfg.refresh}s")
if auto:
    time.sleep(cfg.refresh)
    st.rerun()
