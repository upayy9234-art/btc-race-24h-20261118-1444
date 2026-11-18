# btc-race-24h-20261118-1444

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/upayy9234-art/btc-race-24h-20261118-1444/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/upayy9234-art/btc-race-24h-20261118-1444/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

Long-only cbBTC dip bot for make.fun's [Race a BTC trading bot live for 24 hours](https://make.fun/bounty/btc-race-24h-20261118-1444) bounty ($250 in USDC). It trades Coinbase Wrapped BTC (CBBTC) against USDC on 1-minute bars, starting from $1,000 USDC.

## Strategy

- **Reference:** the highest close of the last 240 one-minute bars (including the current bar).
- **Entry (while flat):** buy with the entire cash balance when the close falls at least 160 bps below that reference. Entries need 240 bars seen before the current bar, at least 30 bars since the last exit, and only before seq 1380.
- **Entry price:** when a position first appears, its entry price is the open of the bar on which the fill landed (orders fill at the next bar's open).
- **Exit (while holding):** sell the whole position when the gain from the entry price reaches +150 bps, falls to −70 bps, or 480 bars have passed since the entry bar.
- **Safety:** no orders during warm-up, one reply per batch, at most one open position, max slippage 500 bps on every order.

All arithmetic is integer arithmetic on the protocol's scaled units, with no wall clock, environment reads, or unseeded randomness, so two runs on the same data produce byte-identical replies.

## Dev-window result

On the published 1,440-bar dev window, replayed offline with the kit's fill model (4 bps fee, 2 bps slippage, constant-product impact against each bar's open depth): **net PnL +$14.84 USDC, 4 trades, max drawdown 0.70%**. Fills: BUY bar 241 @ open $63,681.76, SELL bar 472 @ open $64,673.22, BUY bar 679 @ open $64,104.19, SELL bar 1160 @ open $64,528.46.

## Run it

```sh
python3 -P -s main.py
```

Python 3.13, standard library only. The bot speaks `agent-fun/bars-replay/v1` (newline-delimited JSON on stdin/stdout) via the vendored shim in `vendor/makefun_bars.py`, a byte-for-byte copy of the kit's SDK shim.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>
