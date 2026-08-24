"""Diagnostic: verifies FYERS Market Depth permission/response without printing credentials."""
from config import FYERS_APP_ID, FYERS_ACCESS_TOKEN
from data.fyers_provider import FyersProvider

if __name__ == "__main__":
    p = FyersProvider()
    symbols = p.load_universe(refresh=False)
    print("NSE symbols:", len(symbols))
    # Pick the first symbol that has a valid quote and LTP.
    selected = None
    for i in range(0, min(len(symbols), 250), 50):
        batch = symbols[i:i+50]
        resp = p.fyers.quotes(data={"symbols": ",".join(batch)})
        for item in resp.get("d", []) if isinstance(resp, dict) else []:
            v = item.get("v", item) if isinstance(item, dict) else {}
            sym = item.get("n") or item.get("symbol") or v.get("symbol")
            if sym and p.num(v, "lp", "ltp") > 0:
                selected = sym
                break
        if selected:
            break
    if not selected:
        raise SystemExit("No valid quote found. Run this during market hours.")
    print("Testing depth for:", selected)
    response = p.fyers.depth(data={"symbol": selected, "ohlcv_flag": "1"})
    if isinstance(response, dict) and response.get("s") == "error":
        print("FYERS depth error:", response.get("code"), response.get("message"))
    else:
        d = p._depth_fields(response)
        print("Depth status: OK")
        print("LTP:", d.get("ltp"))
        print("Bid price:", d.get("bid"))
        print("Bid quantity (total buy):", d.get("bid_qty"))
        print("Ask price:", d.get("ask"))
        print("Ask quantity (total sell):", d.get("ask_qty"))
