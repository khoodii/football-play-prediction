import pandas as pd, numpy as np, pickle
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import accuracy_score
from collections import Counter

df = pd.read_pickle("/home/claude/features.pkl")
meta = pickle.load(open("/home/claude/meta.pkl","rb"))
le = meta['le']

groups = df['game_id'].values
y = df['y'].values

# --- Baseline 1: always predict majority class (pass) ---
majority = Counter(y).most_common(1)[0][0]
acc_majority = accuracy_score(y, [majority]*len(y))

# --- Baseline 2: down-conditional mode (per fold, honest LOGO) ---
logo = LeaveOneGroupOut()
preds_down = []
trues = []

for train_idx, test_idx in logo.split(df, y, groups):
    train = df.iloc[train_idx]
    test  = df.iloc[test_idx]
    # for each down, find the most common call in TRAIN
    down_mode = train.groupby('down')['y'].agg(lambda x: x.mode()[0]).to_dict()
    overall_mode = Counter(train['y']).most_common(1)[0][0]
    preds = test['down'].map(lambda d: down_mode.get(d, overall_mode))
    preds_down.extend(preds.tolist())
    trues.extend(y[test_idx].tolist())

acc_down = accuracy_score(trues, preds_down)

# --- Baseline 3: random stratified ---
from sklearn.dummy import DummyClassifier
logo2 = LeaveOneGroupOut()
dummy = DummyClassifier(strategy='stratified', random_state=42)
preds_rand = []
for train_idx, test_idx in logo2.split(df, y, groups):
    dummy.fit(df.iloc[train_idx][['down']], y[train_idx])
    preds_rand.extend(dummy.predict(df.iloc[test_idx][['down']]).tolist())
acc_rand = accuracy_score(y, preds_rand)

print("=== BASELINES (leave-one-game-out) ===")
print(f"  Always predict 'pass':        {acc_majority:.3f}  ({acc_majority*100:.1f}%)")
print(f"  Stratified random:            {acc_rand:.3f}  ({acc_rand*100:.1f}%)")
print(f"  Down-conditional mode:        {acc_down:.3f}  ({acc_down*100:.1f}%)")
print()
print("Down-conditional predictions (what the baseline actually predicts per down):")
for d in [1,2,3,4]:
    sub = df[df['down']==d]
    mode_label = le.inverse_transform([Counter(sub['y']).most_common(1)[0][0]])[0]
    dist = sub['target'].value_counts(normalize=True).to_dict()
    print(f"  Down {d}: predicts '{mode_label}' every time  | true dist: { {k:f'{v:.0%}' for k,v in dist.items()} }")
print()
print(f"  --> Beat this number to justify a model: {acc_down:.3f}")

# save for step 6
pickle.dump({'majority': acc_majority, 'down_conditional': acc_down, 'random': acc_rand},
            open("/home/claude/baselines.pkl","wb"))
