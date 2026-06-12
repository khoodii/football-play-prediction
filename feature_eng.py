import json, pandas as pd, numpy as np

rows = json.load(open("/home/claude/parsed_v2.json"))

# --- clean plays only, with a family label ---
clean = [r for r in rows if not r['review']]
df = pd.DataFrame(clean)

# --- target ---
def target(r):
    f = r.get('play_family')
    if f in ('qb_run','qb_pass'): return 'qb_run'
    if f in ('run','pass'): return f
    return None

df['target'] = df.apply(target, axis=1)
before = len(df)
df = df[df['target'].notna()].copy()
print(f"Rows with target: {len(df)} / {before} clean plays ({before-len(df)} dropped, no family label)")
print("Target distribution:\n", df['target'].value_counts())

# --- features ---

# 1. down: 1-4, fill missing with median
df['down'] = pd.to_numeric(df['down'], errors='coerce')
df['down'] = df['down'].fillna(df['down'].median()).astype(int)

# 2. distance bucket: ordinal encode s=1 m=2 l=3 none=0
dist_map = {None: 0, 'none': 0, 's': 1, 'm': 2, 'l': 3}
df['dist_ord'] = df['dist_bucket'].map(lambda x: dist_map.get(x, 0))

# 3. box count: integer 5-8, fill with 7 (mode)
df['box'] = pd.to_numeric(df['box_count'], errors='coerce').fillna(7).astype(int)

# 4. coverage known: binary flag (1 if any coverage recorded)
df['coverage_known'] = df['coverage_postsnap'].apply(lambda x: 0 if (x is None or str(x).strip()=='') else 1)

# 5. coverage type: man=1 zone/cover3/cover2/cover4=2 cover1=3 unknown=0
def cov_type(x):
    if not x: return 0
    x = str(x).lower()
    if 'man' in x: return 1
    if any(z in x for z in ['zone','cover 3','cover 4','cover 2','cover3','cover4','cover2','solid']): return 2
    if 'cover 1' in x or 'cover1' in x: return 3
    return 0
df['cov_type'] = df['coverage_postsnap'].apply(cov_type)

# 6. blitz flag
df['blitz_flag'] = df['blitz'].apply(lambda x: 0 if (x is None or str(x).strip()=='') else 1)

# 7. opponent: one-hot (drop Kearsley since not a 2026 opponent - kept for training pool only)
df['opponent'] = df['game']
opp_dummies = pd.get_dummies(df['opponent'], prefix='opp')
df = pd.concat([df, opp_dummies], axis=1)

# 8. game id for cross-validation grouping
game_list = sorted(df['game'].unique())
df['game_id'] = df['game'].map({g: i for i, g in enumerate(game_list)})

# --- feature set ---
BASE_FEATS = ['down', 'dist_ord', 'box', 'blitz_flag']
COV_FEATS  = ['cov_type', 'coverage_known']
OPP_FEATS  = [c for c in df.columns if c.startswith('opp_')]
ALL_FEATS  = BASE_FEATS + COV_FEATS + OPP_FEATS

print("\nFeature sets:")
print(f"  BASE (down+dist+box+blitz): {BASE_FEATS}")
print(f"  +COVERAGE:                  {BASE_FEATS+COV_FEATS}")
print(f"  +OPPONENT (all feats):      {len(ALL_FEATS)} features")

# --- label encode target ---
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
df['y'] = le.fit_transform(df['target'])
print(f"\nTarget classes: {dict(zip(le.classes_, le.transform(le.classes_)))}")

# save
df.to_pickle("/home/claude/features.pkl")
import pickle
pickle.dump({'le': le, 'BASE': BASE_FEATS, 'COV': COV_FEATS, 'OPP': OPP_FEATS, 'ALL': ALL_FEATS}, 
            open("/home/claude/meta.pkl","wb"))
print(f"\nSaved {len(df)} rows x {len(ALL_FEATS)} features to features.pkl")
