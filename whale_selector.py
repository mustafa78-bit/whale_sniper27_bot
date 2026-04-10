from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
import requests

LAST_N_TRADES = 6

ELITE_MIN_WINS = 5
ELITE_MIN_TOTAL_PNL = 8.0
ELITE_MIN_AVG_PNL = 1.2
ELITE_MAX_BIG_LOSSES = 1
ELITE_MIN_STABILITY = 65.0

WATCH_MIN_WINS = 3
WATCH_MIN_TOTAL_PNL = 1.0
WATCH_MIN_AVG_PNL = 0.2
WATCH_MIN_STABILITY = 45.0

BIG_LOSS_THRESHOLD = -3.0

OUTPUT_FILE = "whale_groups.json"

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")


@dataclass
class WhalePerformance:
    wallet: str
    group: str
    stars: str
    wins: int
    losses: int
    win_rate: float
    total_pnl_percent: float
    avg_pnl_percent: float
    big_losses: int
    stability_score: float
    note: str


def sort_trades_desc(trades):
    return sorted(trades, key=lambda x: x["closed_at"], reverse=True)


def take_last_n_closed_trades(trades, n=LAST_N_TRADES):
    return sort_trades_desc(trades)[:n]


def calc_stability_score(pnls):
    if not pnls:
        return 0.0

    avg = sum(pnls) / len(pnls)
    variance = sum((x - avg) ** 2 for x in pnls) / len(pnls)
    std_dev = variance ** 0.5

    score = 100 - (std_dev * 8)

    if any(x <= BIG_LOSS_THRESHOLD for x in pnls):
        score -= 10

    return max(0, min(100, round(score, 2)))


def classify_last_6(trades):
    if len(trades) < LAST_N_TRADES:
        return None

    wallet = trades[0]["wallet"]
    last6 = take_last_n_closed_trades(trades)
    pnls = [float(t["pnl_percent"]) for t in last6]

    wins = sum(1 for x in pnls if x > 0)
    losses = sum(1 for x in pnls if x <= 0)
    total_pnl = round(sum(pnls), 2)
    avg_pnl = round(total_pnl / LAST_N_TRADES, 2)
    big_losses = sum(1 for x in pnls if x <= BIG_LOSS_THRESHOLD)
    win_rate = round((wins / LAST_N_TRADES) * 100, 2)
    stability = calc_stability_score(pnls)

    if (
        wins >= ELITE_MIN_WINS
        and total_pnl >= ELITE_MIN_TOTAL_PNL
        and avg_pnl >= ELITE_MIN_AVG_PNL
        and big_losses <= ELITE_MAX_BIG_LOSSES
        and stability >= ELITE_MIN_STABILITY
    ):
        return WhalePerformance(
            wallet=wallet,
            group="ELITE",
            stars="⭐⭐⭐⭐⭐⭐",
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            total_pnl_percent=total_pnl,
            avg_pnl_percent=avg_pnl,
            big_losses=big_losses,
            stability_score=stability,
            note="Elite balina",
        )

    if (
        wins >= WATCH_MIN_WINS
        and total_pnl >= WATCH_MIN_TOTAL_PNL
        and avg_pnl >= WATCH_MIN_AVG_PNL
        and stability >= WATCH_MIN_STABILITY
    ):
        return WhalePerformance(
            wallet=wallet,
            group="WATCH",
            stars="👀",
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            total_pnl_percent=total_pnl,
            avg_pnl_percent=avg_pnl,
            big_losses=big_losses,
            stability_score=stability,
            note="Takip balinası",
        )

    return None


def split_whales(trades):
    grouped = {}

    for t in trades:
        wallet = str(t["wallet"]).strip()
        grouped.setdefault(wallet, []).append(t)

    elite = []
    watch = []

    for wallet, tlist in grouped.items():
        result = classify_last_6(tlist)
        if not result:
            continue

        if result.group == "ELITE":
            elite.append(result)
        else:
            watch.append(result)

    elite.sort(
        key=lambda x: (x.win_rate, x.total_pnl_percent, x.stability_score),
        reverse=True,
    )
    watch.sort(
        key=lambda x: (x.win_rate, x.total_pnl_percent, x.stability_score),
        reverse=True,
    )

    return {
        "elite": [asdict(x) for x in elite],
        "watch": [asdict(x) for x in watch],
    }


def load_trades(path="closed_whale_trades.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_output(data):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print(msg)
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": msg,
            "disable_web_page_preview": True,
        },
        timeout=20,
    )


def build_msg(data):
    lines = []
    lines.append("🐋 WHALE SON 6")

    lines.append("")
    lines.append("🏆 ELITE")
    if data["elite"]:
        for w in data["elite"][:5]:
            lines.append(
                f"{w['wallet']} | WR %{w['win_rate']} | PnL %{w['total_pnl_percent']}"
            )
    else:
        lines.append("Elite yok")

    lines.append("")
    lines.append("👀 TAKİP")
    if data["watch"]:
        for w in data["watch"][:5]:
            lines.append(
                f"{w['wallet']} | WR %{w['win_rate']} | PnL %{w['total_pnl_percent']}"
            )
    else:
        lines.append("Takip yok")

    return "\n".join(lines)


if __name__ == "__main__":
    trades = load_trades()
    result = split_whales(trades)
    save_output(result)

    msg = build_msg(result)
    print(msg)
    send_telegram(msg)
