from flask import Flask, render_template, request, jsonify
import time
import sys
import copy
import random

app = Flask(__name__)

COLORS = ("R", "G", "B", "Y")
KINDS = ("NUM", "SKIP", "REV", "D2", "WILD")

def _rand_card(rng: random.Random):
    r = rng.randint(0, 9)
    if r <= 5:
        return {"kind": "NUM", "color": rng.choice(COLORS), "num": rng.randint(0, 9)}
    if r == 6:
        return {"kind": "SKIP", "color": rng.choice(COLORS), "num": -1}
    if r == 7:
        return {"kind": "REV", "color": rng.choice(COLORS), "num": -1}
    if r == 8:
        return {"kind": "D2", "color": rng.choice(COLORS), "num": -1}
    return {"kind": "WILD", "color": "W", "num": -1}

def _is_playable(card, top, current_color: str) -> bool:
    if card["kind"] == "WILD":
        return True
    if card["color"] == current_color:
        return True
    if card["kind"] != "NUM" and card["kind"] == top["kind"]:
        return True
    if card["kind"] == "NUM" and top["kind"] == "NUM" and card["num"] == top["num"]:
        return True
    return False

def _init_game(players: int, hand: int, rng: random.Random):
    hands = [[_rand_card(rng) for _ in range(hand)] for _ in range(players)]
    top = _rand_card(rng)
    current_color = rng.choice(COLORS) if top["kind"] == "WILD" else top["color"]
    return {
        "players": players,
        "hands": hands,
        "top": top,
        "color": current_color,
        "turn": 0,
        "dir": 1,
        "pending_draw": 0,
        "finished": False,
        "winner": -1,
        "steps": 0,
    }

def _next_idx(state, idx: int) -> int:
    n = state["players"]
    return (idx + state["dir"]) % n

def _step_once(state, rng: random.Random):
    """Proses 1 giliran (1 langkah)."""
    if state["finished"]:
        return

    p = state["turn"]
    hand = state["hands"][p]

    # Terapkan pending draw akibat D2
    if state["pending_draw"] > 0:
        for _ in range(state["pending_draw"]):
            hand.append(_rand_card(rng))
        state["pending_draw"] = 0

    # Cari kartu playable (scan sederhana)
    playable_idx = -1
    for i, c in enumerate(hand):
        if _is_playable(c, state["top"], state["color"]):
            playable_idx = i
            break

    if playable_idx == -1:
        # Tidak ada kartu cocok -> draw 1
        hand.append(_rand_card(rng))
    else:
        played = hand.pop(playable_idx)
        state["top"] = played
        if played["kind"] != "WILD":
            state["color"] = played["color"]
        else:
            state["color"] = rng.choice(COLORS)

        # Efek aksi
        if played["kind"] == "SKIP":
            # loncat 1 pemain
            state["turn"] = _next_idx(state, state["turn"])
        elif played["kind"] == "REV":
            state["dir"] *= -1
        elif played["kind"] == "D2":
            state["pending_draw"] += 2

        # Cek menang
        if len(hand) == 0:
            state["finished"] = True
            state["winner"] = p
            return

    # Next player
    state["turn"] = _next_idx(state, state["turn"])
    state["steps"] += 1

def simulate_iter(players: int, hand: int, max_turns: int, seed: int = 1) -> int:
    rng = random.Random(seed)
    state = _init_game(players, hand, rng)
    while (not state["finished"]) and state["steps"] < max_turns:
        _step_once(state, rng)
    return state["steps"]

def _simulate_rec(state, rng: random.Random, max_turns: int) -> int:
    if state["finished"] or state["steps"] >= max_turns:
        return state["steps"]
    _step_once(state, rng)
    return _simulate_rec(state, rng, max_turns)

def simulate_rec(players: int, hand: int, max_turns: int, seed: int = 1) -> int:
    rng = random.Random(seed)
    state = _init_game(players, hand, rng)
    return _simulate_rec(state, rng, max_turns)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run():
    data = request.json

    players = int(data.get("players", 4))
    hand = int(data.get("hand", 7))
    turns_req = int(data.get("turns", 500))
    seed = int(data.get("seed", 1))

    players = max(2, min(players, 10))
    hand = max(1, min(hand, 20))
    turns_req = max(1, min(turns_req, 200000))

    sys.setrecursionlimit(max(2000, turns_req + 200))

    start = time.perf_counter()

    if data["type"] == "iterative":
        turns = simulate_iter(players, hand, turns_req, seed=seed)
    else:
        # Rekursif: sama persis param-nya, hanya beda cara loop-nya
        turns = simulate_rec(players, hand, turns_req, seed=seed)

    end = time.perf_counter()
    return jsonify({
        "turns": turns,
        "time": round((end - start) * 1000, 3)
    })

@app.route("/compare", methods=["POST"])
def compare():
    data = request.json
    players = int(data.get("players", 4))
    hand = int(data.get("hand", 7))
    turns_req = int(data.get("turns", 500))
    repeat = int(data.get("repeat", 30))
    seed = int(data.get("seed", 1))

    players = max(2, min(players, 10))
    hand = max(1, min(hand, 20))
    turns_req = max(1, min(turns_req, 200000))
    repeat = max(1, min(repeat, 1000))

    sys.setrecursionlimit(max(2000, turns_req + 200))
    
    t0 = time.perf_counter()
    for _ in range(repeat):
        simulate_iter(players, hand, turns_req, seed=seed)
    t1 = time.perf_counter()

    t2 = time.perf_counter()
    for _ in range(repeat):
        simulate_rec(players, hand, turns_req, seed=seed)
    t3 = time.perf_counter()

    iter_total_ms = (t1 - t0) * 1000
    rec_total_ms = (t3 - t2) * 1000

    return jsonify({
        "repeat": repeat,
        "iter_total_ms": round(iter_total_ms, 3),
        "iter_avg_ms": round((t1 - t0) * 1000 / repeat, 3),
        "rec_total_ms": round(rec_total_ms, 3),
        "rec_avg_ms": round((t3 - t2) * 1000 / repeat, 3)
    })

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)