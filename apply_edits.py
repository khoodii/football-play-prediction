import json
rows=json.load(open("/home/claude/parsed.json"))
for r in rows: r["user_note"]=""

def S(sr): return rows[sr-2]  # sheet row -> data row

# field name shortcuts -> row keys
KEY={"shell":"shell_presnap","coverage":"coverage_postsnap","family":"play_family",
     "broken":"broken_play","goal":"goal_to_go","name":"play_name","num":"play_number"}

EDITS={
 # --- clear, applied ---
 13:{"review":"presnap_or_note","user_note":"safeties to boundary; LBs/DBs ~5yd depth (pre-snap)"},
 22:{"review":"presnap_or_note","box_count":5,"user_note":"5 box, 1 mike middle (pre-snap)"},
 27:{"review":"observation_only","user_note":"'the backside play' = reference note"},
 28:{"down":1,"name":"post","family":"pass","review":None,"user_note":"double-A blitz, man weak/zone strong; backside post"},
 29:{"down":2,"name":"slant","family":"pass","review":None,"user_note":"slant from trips"},
 48:{"user_note":"guard got blown up (sack)"},
 58:{"down":1,"box_count":5,"shell":"2-high","outcome":"first_down","user_note":"1 on fringe, playing to field"},
 62:{"down":2,"yards":8,"shell":"boundary","review":"needs_user","user_note":"CONFIRM box: you said 2, entry says 7. 'boundary' moved to pre-snap (D set)"},
 68:{"outcome":"first_down","user_note":"prior play was a penalty"},
 82:{"down":4,"dist_bucket":"s"},
 92:{"down":2,"box_count":5,"shell":"1-high","review":"presnap_or_note","user_note":"2nd, 1 high, 5 box (pre-snap)"},
 105:{"down":4},
 110:{"down":4,"name":"wheel","family":"pass","yards":40,"outcome":"complete","user_note":"3rd time running wheel; 40yd completion"},
 113:{"down":1,"name":"panther","family":"qb_run","yards":7,"user_note":"same play as prior (panther)"},
 117:{"down":1,"box_count":7,"shell":"1-high","coverage":"cover 3","flag":"penalty:false_start","user_note":"1 high = cover 3; result false start"},
 134:{"down":1,"dist_explicit":10,"shell":"2-high","box_count":7,"broken":"Y","yards":25,"user_note":"1st&10, broken play 25yd"},
 139:{"review":"observation_only","user_note":"placeholder: add first-half notes from email"},
 160:{"down":2,"dist_bucket":"l","yards":2},
 179:{"down":3,"dist_explicit":5},
 189:{"down":3,"dist_explicit":27,"flag":"penalty"},
 199:{"down":1,"goal":"","user_note":"'goal line' = spot on field, not goal-to-go"},
 227:{"down":3,"broken":"Y","review":"observation_only","user_note":"broken play (observation)"},
 234:{"down":3,"dist_explicit":18,"outcome":"fumble","user_note":"got first down then fumbled"},
 265:{"down":1,"yards":-10,"user_note":"crazy snap, 10yd loss"},
 279:{"down":1,"yards":3},
 313:{"down":3,"box_count":8,"review":"presnap_or_note","user_note":"8 box all drive; d-line note"},
 321:{"down":3,"dist_bucket":"l","outcome":"sack","user_note":"qb smashed"},
 323:{"review":"observation_only","user_note":"qb suspended first half (note)"},
 345:{"review":"observation_only","user_note":"busted play (note)"},
 386:{"down":2,"dist_bucket":"l","blitz":"delayed a gap blitz","box_count":7,"review":"presnap_or_note","user_note":"delayed A-gap blitz, 7 box (pre-snap D)"},
 395:{"down":4,"broken":"Y","outcome":"first_down","user_note":"broken play -> first down (note)"},
 399:{"down":1,"box_count":8,"coverage":"cover 3","review":"presnap_or_note","user_note":"8 box, solid=cover3 (pre-snap)"},
 403:{"down":4,"dist_bucket":"l"},
 # --- conflicts: your note disagrees with the recorded entry; held for your 2nd pass ---
 45:{"review":"needs_user","user_note":"You said 'first down' but entry is a coverage note ('went cover 3 whole drive') — looks like an observation. Confirm."},
 69:{"review":"needs_user","user_note":"You said 'first down' but entry says '90 over / fumble sack'. Confirm result."},
 77:{"review":"needs_user","user_note":"You said 'first down' but entry shows a penalty + 'fade bracketed' observation. Confirm."},
 124:{"review":"observation_only","user_note":"Reads as a coach observation (#4 lazy/footwork), not a down. Tell me if it was a real play."},
 125:{"review":"observation_only","user_note":"Reads as an observation (interior getting beat), not a down. Confirm if real play."},
 126:{"review":"observation_only","user_note":"Reads as an observation (new safety in game), not a down. Confirm if real play."},
 274:{"review":"needs_user","user_note":"Entry is '3/ field goal' — field goal on 3rd is unclear. Confirm."},
}

applied=0; flagged=[]
for sr,ed in EDITS.items():
    r=S(sr)
    for k,v in ed.items():
        if k=="review": r["review"]=v
        elif k=="user_note": r["user_note"]=v
        else: r[KEY.get(k,k)]=v
    if ed.get("review")=="needs_user" or sr in (45,69,77,124,125,126,274): flagged.append(sr)
    applied+=1

json.dump(rows, open("/home/claude/parsed_v2.json","w"), indent=0)
print("rows edited:",applied)
print("held for your 2nd pass (conflicts):",sorted(set(flagged)))
from collections import Counter
print("new review tags:",dict(Counter(r['review'] for r in rows)))
print("clean plays now:",sum(1 for r in rows if not r['review']))
