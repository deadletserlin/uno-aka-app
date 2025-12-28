from flask import Flask, render_template, request, jsonify
import time

app = Flask(__name__)

def simulate_iter(players, hand, max_turns):
    turn = 0
    while turn < max_turns:
        turn += 1
    return turn

def simulate_rec(turn, max_turns):
    if turn >= max_turns:
        return turn
    return simulate_rec(turn + 1, max_turns)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run():
    data = request.json
    start = time.perf_counter()

    if data["type"] == "iterative":
        turns = simulate_iter(data["players"], data["hand"], data["turns"])
    else:
        turns = simulate_rec(0, data["turns"])

    end = time.perf_counter()
    return jsonify({
        "turns": turns,
        "time": round((end - start) * 1000, 3)
    })

@app.route("/compare", methods=["POST"])
def compare():
    data = request.json
    repeat = int(data.get("repeat", 30))

    t0 = time.perf_counter()
    for _ in range(repeat):
        simulate_iter(data["players"], data["hand"], data["turns"])
    t1 = time.perf_counter()

    t2 = time.perf_counter()
    for _ in range(repeat):
        simulate_rec(0, data["turns"])
    t3 = time.perf_counter()

    return jsonify({
        "iter_avg_ms": round((t1 - t0) * 1000 / repeat, 3),
        "rec_avg_ms": round((t3 - t2) * 1000 / repeat, 3)
    })

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)