# Predicting Offensive Play Calls from Hand-Logged Football Data

A machine learning and data analysis project built on a full season of high school football play-by-play data, recorded by hand in a custom shorthand notation.

## Overview

I set out to answer a single question: can a machine learning model predict our offense's play calls (run, pass, or QB run) from the game situation — down, distance, defensive box count, and coverage?

I built the full pipeline end to end: parsing raw hand-written logs into structured data, cleaning and validating a schema, exploratory analysis, and model training with proper cross-validation. The honest result is that the model could not beat a simple baseline — and the most valuable part of the project was recognizing why, and pivoting the deliverable to something that actually works: situational tendency analysis.

## The Data

- **Source:** 9 games of offensive play-by-play, logged by hand during film review.
- **Format:** A custom slash-delimited shorthand (down / distance / play call / defensive box / result / coverage), recorded inconsistently — field order varied between and even within games, and many fields were missing.
- **Volume:** ~450 raw entries, cleaned down to 374 usable plays.

The inconsistency was the core challenge. The same piece of information (box count, for example) could appear at the start, middle, or end of a line depending on how it was jotted down mid-game.

## Pipeline

1. **Parsing.** Rather than parse by field position (which fails the moment the order shifts), I built a **content-pattern parser**: it identifies each field by what the token *is*, not where it sits. A bare number 5–8 is a box count; 0–3 in the coverage slot is a coverage scheme; named tokens map to plays, formations, or defensive shells. The non-overlapping number ranges let the parser recover fields regardless of position.
2. **Schema validation and cleaning.** Defined a fixed schema up front, then ran a manual correction pass against flagged rows. Missing data was kept as genuine blanks — never imputed with placeholder values that could be mistaken for real data.
3. **Exploratory analysis.** Run/pass/QB-run rates broken down by down, distance, box count, and opponent.
4. **Feature engineering and target selection.** Chose a coarse 3-class target (run / pass / QB run) after finding that the data contained 59 distinct play calls, 33 of which appeared fewer than three times — far too sparse for call-level prediction.
5. **Baseline.** Benchmarked against a majority-class predictor (always guess the most common outcome).
6. **Modeling.** Random forest and gradient boosting classifiers across three feature sets.

## Methodology

The methodological decisions are the heart of this project:

- **Leave-one-game-out cross-validation (9 folds).** Plays from the same game are correlated — same opponent, same game script, same conditions. A random train/test split would leak that correlation across the split and inflate accuracy. Holding out whole games is the honest test of whether the model generalizes to a game it has never seen.
- **Baseline benchmarking.** A model is only useful if it beats the naive guess. The majority-class baseline (always predict "pass") scored 49.9%. That became the number to beat.

## Results

| Model | Features | Accuracy (LOGO CV) | vs. baseline |
|-------|----------|-------------------|--------------|
| Majority class | — | 49.9% | baseline |
| Random forest | down + distance + box + blitz | 45.2% | −4.7 |
| Random forest | + coverage | 46.6% | −3.3 |
| Random forest | + opponent (all features) | 45.8% | −4.1 |
| Gradient boosting | all features | 42.6% | −7.3 |

Collapsing to a simpler two-class problem (run vs. pass) raised the best score to 56.3% — a 6-point lift over a coin flip, but still modest.

Two diagnostic signals stood out:

- The QB-run class (36 of 343 plays) was **never predicted** — too few examples for the model to ever choose it confidently.
- The full feature set scored **worse** than the simpler one. That inversion is a classic sign of overfitting: with limited data, the extra features let the model memorize noise rather than learn signal.

Feature importance confirmed what the exploratory analysis suggested: **down** was the only feature carrying real weight; box count, coverage, and blitz contributed almost nothing.

## Interpretation and Decision

The model didn't fail because of a bug — it failed because the dataset is too small and the features too low-variance to support play-level prediction beyond what down-and-distance tendency already reveals. With the tendencies themselves being clear, transparent, and more reliable than a model that can't beat a baseline, **I chose not to ship the classifier.**

Instead, the deliverable became:
- **Descriptive tendency tables** — run/pass rates by situation, which directly serve the scouting use case.
- **A reusable pipeline** — when a larger, cleaner dataset is collected next season (estimated 3x the volume), the entire pipeline re-runs and the modeling question reopens with a real chance.

## What I'd Do Differently / Next Steps

- **Collect more data with a consistent schema** — the single biggest lever. The model's failure is a sample-size problem, not a method problem.
- **Add features with more variance** — box count was 62% one value, which limits its predictive power.
- **Revisit the model at higher volume** with the same validation discipline.

## Tech Stack

Python · pandas · scikit-learn (RandomForest, GradientBoosting, LeaveOneGroupOut) · openpyxl

## Skills Demonstrated

- Parsing messy, real-world unstructured data into a clean schema
- Designing a content-pattern parser robust to inconsistent input
- Proper cross-validation for grouped data (avoiding leakage)
- Baseline benchmarking and honest model evaluation
- Diagnosing overfitting and small-sample limitations
- Knowing when *not* to ship a model — and pivoting to the deliverable that serves the real need
