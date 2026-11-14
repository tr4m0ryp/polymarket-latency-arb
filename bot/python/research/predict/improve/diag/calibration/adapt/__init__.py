"""Adaptive-gain and delta-structural refits of the 1 s value model (post-freeze, diagnostic).

The calibration diagnostic found the busy-hour inflation comes from the spot-book inputs
(depletion, short microprice changes, touch size, time-to-depletion) firing at twice their
train base rate, and the loss anatomy found the model flat across the settlement delta while
the realised value is not. Two inversions of the fixed-scale default, both fitted on run 2
train only (the frozen v1's rows and sample):

- adaptive gain (`agc*`): every Binance book signal divided by its own trailing 60 s scale
  (price changes by realised volatility -> z-scores; flow, depletion and tick counts by the
  message or tick rate; log intensities and log times relative to the trailing rate), the
  divisive normalisation of sensory adaptation (Brenner, Bialek & de Ruyter van Steveninck
  2000; Carandini & Heeger 2012) applied to the model inputs.
- delta-structural (`ds*`): the target split into the part that scales with the settlement
  delta and the known costs, value = delta * g(x) - half spread - fee, g fitted on
  (y + half spread + fee) / delta with weights delta^2 (the same squared loss in cents).

Variants: v1r (control, v1 refit through this code), ctx (v1 + activity scales as inputs),
agc, agc_add, ds, ds_agc, dsc / dsc_agc (delta capped at 30 c/bp), q25 / q25_agc (25%
quantile, a lower-bound prediction). Models are written under CACHE/models/ (not the frozen directory)."""
from .. import CACHE

MODELS = CACHE / "models"
VARIANTS = ("v1r", "ctx", "agc", "agc_add", "ds", "ds_agc", "dsc", "dsc_agc", "q25", "q25_agc")
