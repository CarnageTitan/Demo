"""
Quant Trading Model - Web App for Render
"""

import os
from flask import Flask, render_template, request, jsonify

from model_runner import run_model, DEFAULT_WATCHLIST

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", watchlist=",".join(DEFAULT_WATCHLIST))


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    tickers_raw = request.form.get("tickers") or request.args.get("tickers") or ""
    tickers = [t.strip() for t in tickers_raw.split(",") if t.strip()] if tickers_raw else None
    top = int(request.form.get("top") or request.args.get("top") or 25)
    min_score = float(request.form.get("min_score") or request.args.get("min_score") or 0)

    out = run_model(tickers=tickers, top=top, min_score=min_score)

    if request.headers.get("Accept") == "application/json" or request.args.get("json"):
        return jsonify(out)

    return render_template("index.html", results=out["results"], error=out["error"], watchlist=tickers_raw or ",".join(DEFAULT_WATCHLIST))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
