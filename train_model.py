import pandas as pd, numpy as np, pickle
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from collections import Counter

df   = pd.read_pickle("/home/claude/features.pkl")
meta = pickle.load(open("/home/claude/meta.pkl","rb"))
base = pickle.load(open("/home/claude/baselines.pkl","rb"))
le   = meta['le']

groups = df['game_id'].values
y      = df['y'].values

FEAT_SETS = {
    'BASE':         meta['BASE'],
    'BASE+COV':     meta['BASE'] + meta['COV'],
    'ALL':          meta['ALL'],
}

MODELS = {
    'RandomForest': RandomForestClassifier(n_estimators=200, max_depth=4, 
                                           min_samples_leaf=5, random_state=42),
    'GradientBoost': GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                                learning_rate=0.1, min_samples_leaf=5,
                                                random_state=42),
}

logo = LeaveOneGroupOut()
results = {}

print("=== STEP 6: MODEL TRAINING (leave-one-game-out, 9 folds) ===\n")
print(f"  Majority-class baseline:      {base['majority']:.3f} ({base['majority']*100:.1f}%)")
print(f"  Beat this to be useful:       {base['majority']:.3f}\n")

for mname, model in MODELS.items():
    for fname, feats in FEAT_SETS.items():
        X = df[feats].values
        all_preds, all_true, all_proba = [], [], []
        fold_accs = []
        
        for train_idx, test_idx in logo.split(X, y, groups):
            Xtr, Xte = X[train_idx], X[test_idx]
            ytr, yte = y[train_idx], y[test_idx]
            m = pickle.loads(pickle.dumps(model))  # fresh clone
            m.fit(Xtr, ytr)
            preds = m.predict(Xte)
            all_preds.extend(preds)
            all_true.extend(yte)
            fold_accs.append(accuracy_score(yte, preds))
        
        acc   = accuracy_score(all_true, all_preds)
        std   = np.std(fold_accs)
        key   = f"{mname}_{fname}"
        results[key] = {'acc': acc, 'std': std, 'preds': all_preds, 'true': all_true,
                        'model_name': mname, 'feat_name': fname, 'feats': feats}
        lift  = acc - base['majority']
        print(f"  {mname:<16} {fname:<10}  acc={acc:.3f} ({acc*100:.1f}%)  std={std:.3f}  lift={lift:+.3f}")

# --- best model ---
best_key = max(results, key=lambda k: results[k]['acc'])
best     = results[best_key]
print(f"\n  Best: {best_key}  acc={best['acc']:.3f}")
print()

# --- per-class report on best ---
print("=== Classification report (best model) ===")
print(classification_report(best['true'], best['preds'], 
                             target_names=le.classes_, digits=3))

# --- confusion matrix ---
print("=== Confusion matrix (best model) ===")
cm = confusion_matrix(best['true'], best['preds'])
print(f"         {'  '.join(le.classes_)}")
for i, row in enumerate(cm):
    print(f"  {le.classes_[i]:<8}  {row}")

# --- per-game fold accuracy ---
print("\n=== Per-game fold accuracy (best model) ===")
games = sorted(df['game'].unique())
feats = best['feats']
X = df[feats].values
model = MODELS[best['model_name']]
for train_idx, test_idx in logo.split(X, y, groups):
    game = df.iloc[test_idx[0]]['game']
    m = pickle.loads(pickle.dumps(model))
    m.fit(X[train_idx], y[train_idx])
    acc_fold = accuracy_score(y[test_idx], m.predict(X[test_idx]))
    n = len(test_idx)
    print(f"  {game:<14}  n={n:<3}  acc={acc_fold:.3f}")

# save best model (retrained on all data) for step 7
model_final = pickle.loads(pickle.dumps(model))
model_final.fit(df[feats].values, y)
pickle.dump({'model': model_final, 'feats': feats, 'le': le, 
             'results': results, 'best_key': best_key,
             'baselines': base},
            open("/home/claude/best_model.pkl","wb"))
print("\nSaved best model.")
