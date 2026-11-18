"""Long-only cbBTC dip bot for make.fun's btc-race-24h-20261118-1444.

Strategy, in one paragraph: track the close of every 1-minute CBBTC bar.
The reference is the highest close of the last 240 bars (including the
current one). While flat, buy the whole cash balance when the close has
fallen at least 160 bps below that reference. Once a position appears,
its entry price is the open of the bar on which the fill landed. While
holding, sell the whole position when the gain from that entry price
reaches +150 bps, when it falls to -70 bps, or when 480 bars have passed
since the entry bar. After an exit, wait at least 30 bars before the
next entry, and never enter on or after seq 1380.

Everything is integer arithmetic on the protocol's scaled units (prices
are USDC x 1e5, quantities are satoshis, cash is micro-USDC), so two runs
on the same data produce byte-identical replies. No wall clock, no
environment, no randomness.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"

# Lookback for the reference high, in bars.
LOOKBACK_BARS = 240
# Entry: close at least this many bps below the 240-bar high.
ENTRY_DIP_BPS = 160
# Exit: take profit / stop loss, in bps from the entry price.
TAKE_PROFIT_BPS = 150
STOP_LOSS_BPS = -70
# Exit: maximum holding time, in bars.
MAX_HOLD_BARS = 480
# Cooldown after an exit before the next entry, in bars.
COOLDOWN_BARS = 30
# Never enter on or after this batch seq (orders on the last batch are
# rejected anyway, and a late entry has no time to exit cleanly).
LAST_ENTRY_SEQ = 1380
# Slippage guard on every order, in bps from the latest close.
MAX_SLIPPAGE_BPS = 500


class Bot:
    """Per-run strategy state. All of it is derived from the batches."""

    def __init__(self):
        # Closes seen so far, oldest first, as ints.
        self.closes = []
        # Entry price (int, scaled) and entry bar seq of the open position.
        self.entry_price = None
        self.entry_bar = None
        # Seq of the batch on which the last exit fill landed, or None.
        self.last_exit = None
        # Whether the previous batch reported a position.
        self.was_holding = False

    def on_batch(self, state, batch):
        if state.warming_up:
            return []

        bar = state.latest.get(SYMBOL)
        if bar is None:
            return []
        close = int(bar["c"])
        self.closes.append(close)

        holding = state.positions.get(SYMBOL)
        qty = holding.qty if holding is not None else 0

        # A position that just appeared: its fill landed at this bar's
        # open, so that open is the entry price.
        if qty > 0 and not self.was_holding:
            self.entry_price = int(bar["o"])
            self.entry_bar = state.seq
        # A position that just disappeared: the exit fill landed here.
        if qty == 0 and self.was_holding:
            self.last_exit = state.seq
            self.entry_price = None
            self.entry_bar = None
        self.was_holding = qty > 0

        if qty > 0:
            return self._maybe_exit(state, close, qty)
        return self._maybe_enter(state, close)

    def _maybe_enter(self, state, close):
        if state.seq >= LAST_ENTRY_SEQ:
            return []
        # At least 240 bars must have been seen *before* the current
        # bar, so the first possible entry decision is on seq 240
        # (the 241st close, with a full 240-bar reference behind it).
        if len(self.closes) <= LOOKBACK_BARS:
            return []
        if self.last_exit is not None and state.seq - self.last_exit < COOLDOWN_BARS:
            return []
        reference = max(self.closes[-LOOKBACK_BARS:])
        # close <= reference * (1 - 160/10000), in integers.
        if close * 10000 > reference * (10000 - ENTRY_DIP_BPS):
            return []
        if state.cash <= 0:
            return []
        return [
            {
                "side": "buy",
                "symbol": SYMBOL,
                "notional_quote_units": state.cash,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }
        ]

    def _maybe_exit(self, state, close, qty):
        if self.entry_price is None or self.entry_bar is None:
            return []
        # gain_bps = (close - entry_price) * 10000 / entry_price,
        # truncated toward zero (not floored) so a small negative move
        # is not overstated by a whole basis point.
        diff = (close - self.entry_price) * 10000
        if diff >= 0:
            gain_bps = diff // self.entry_price
        else:
            gain_bps = -((-diff) // self.entry_price)
        if (
            gain_bps >= TAKE_PROFIT_BPS
            or gain_bps <= STOP_LOSS_BPS
            or state.seq - self.entry_bar >= MAX_HOLD_BARS
        ):
            return [
                {
                    "side": "sell",
                    "symbol": SYMBOL,
                    "qty": qty,
                    "max_slippage_bps": MAX_SLIPPAGE_BPS,
                }
            ]
        return []


def main():
    makefun_bars.run(Bot().on_batch)


if __name__ == "__main__":
    main()
