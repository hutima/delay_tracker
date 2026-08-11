# Model card — v0.1.0-prior-only

## Intended use
Leakage-controlled checkpoint persistence and transparent dashboard fallback for
the B6 317 → SQ23 pairing. This version is **not decision-grade**.

## Model
Models A–C and the direct pair layer use fixed logistic intercepts with a tiny
horizon term. They are a software-validation prior, not a fitted empirical model.
Intervals are deliberately broad (±10 percentage points). No coefficient is
presented as learned evidence.

## Leakage controls
The schedule-relative grid contains 6-hour checkpoints from T−120h through T−48h
and 2-hour checkpoints from T−46h through T−4h. Assertions require checkpoints
to precede the flight-specific T−3h embargo. Outcome fields are blank during
prediction generation.

## Limitations
The user-provided approximate schedule has not been independently verified by
service date. Source acquisition returned HTTP 401, so weather vintages, flight
operations, rotations, FAA state, outcomes, fitting, backtests, and calibration
are unavailable rather than fabricated. Historical replay labels in the UI mean
the date has elapsed; they do not claim its evidence reconstruction is complete.
