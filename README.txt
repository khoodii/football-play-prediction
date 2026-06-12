FOOTBALL PLAY-PREDICTION PIPELINE
Run order:

1. parse_plays.py     - Content-pattern parser: raw hand-logs -> parsed.json
2. apply_edits.py     - Applies manual row corrections -> parsed_v2.json
                        (also fill play-family labels; see inline notes)
3. build_xlsx.py      - Builds the formatted spreadsheet (Plays/Schema/Summary)
4. feature_eng.py     - Encodes features, locks target -> features.pkl
5. baseline.py        - Majority-class + down-conditional baselines
6. train_model.py     - RandomForest & GradientBoosting, leave-one-game-out CV

Requires: python3, pandas, scikit-learn, openpyxl, striprtf
Input: raw play logs (.rtf / .txt) in an uploads folder (edit paths at top of parse_plays.py)

NOTE: This is v1, built on ~374 clean plays from 9 games. The models did not beat
the majority-class baseline (see writeup) due to small sample size. Re-run the full
pipeline when a larger, cleaner dataset is collected to revisit the modeling question.
