"""Hold-aware labels for retraining the veto model (i = 0 taker under the measured hold).

Rows = every predict-table instant where the leaders' trigger fires and the arm's gates pass
(the rows the veto decides on), oriented to the trigger side with v1's features. Label = what a
60 sh FAK at limit = seen ask (i = 0) earns per intended share: matched at t + h against the
venue-clock book, 10 s mid markout after the taker fee, 0 when nothing survives."""
from .. import OUT

LAB = OUT / "label"
