import os, re, json
from striprtf.striprtf import rtf_to_text

UP = "/mnt/user-data/uploads"
FILES = {
    "Bedford": "Bedford.rtf", "Dexter": "Dexter.rtf", "Kearsley": "Keasrley_Play_Log.rtf",
    "Monroe": "Monroe.rtf", "Pioneer": "Pioneer.txt", "Saline": "Saline.rtf",
    "Skyline": "Skyline_Play_Log.rtf", "Stoney Creek": "Stoney_Creek_Plalog.rtf",
    "Woodhaven": "woodhaven_play_traking.rtf",
}

def load(path):
    raw = open(path, "rb").read().decode("utf-8", "ignore")
    txt = rtf_to_text(raw) if path.endswith(".rtf") else raw
    return [l.strip() for l in txt.splitlines() if l.strip()]

# ---------- vocabularies ----------
PLAY_NAMES = {  # offensive play names / concepts
    "power","dragon","switch","fade","jet","hitch","screen","toss","boot","sweep","bubble",
    "swing","slant","curl","snag","spot","stop","flat","iso","panther","orca","read","counter",
    "trap","rhino","bear","twist","smoke","hook","out","over","post","wheel","sluggo","slam",
    "comeback","special","rich","larry","punch","spike","bend","shark","quad","pop","dig","sneak",
    "scramble","carry","flow","under","wing","option","reverse","keeper","outtie","sumo","bull"
}
FORMATIONS = {"rip","louie","deuce","strong","weak","boundary","field","plus","minus","pro",
              "jumbo","tight","empty","trip","wing","right","left"}  # context-dependent
COVERAGE_MAP = {  # post-snap scheme
    "solid":"cover 3","cover 1":"cover 1","cover 2":"cover 2","cover 3":"cover 3","cover 4":"cover 4",
    "cover four":"cover 4","cover0":"cover 0","cover 0":"cover 0","four deep":"cover 4",
    "man":"man","zone":"zone","in man":"man","cover three":"cover 3","cover two":"cover 2",
}
SHELL_PATTERNS = [  # pre-snap safety picture
    (r"\bdeuce\b","2-high (deuce)"), (r"2\s*(?:hi|high)\b","2-high"),
    (r"2\s*saf(?:e?ties|tey|ty)\s*high","2-high"), (r"\b1\s*(?:hi|high)\b","1-high"),
    (r"\b3\s*high\b","3-high"), (r"four\s*deep","4-deep"),
]
BLITZ_PATTERNS = [
    r"double\s*a\s*(?:gap)?\s*blitz", r"\ba\s*gap\b.*blitz", r"a\s*gap\s*blitz",
    r"\bblitz\b", r"sim\s*pressure", r"mike\s*blitz", r"delayed\s*a\s*gap", r"\bdouble\s*a\b",
]
FLAGS = {
    "false start":"penalty:false_start","offsid":"penalty:offside","offisd":"penalty:offside",
    "holding":"penalty:holding","hold":"penalty:holding","delay of game":"penalty:delay",
    "illegal procedure":"penalty:illegal_procedure","roughing":"penalty:roughing",
    "pass interference":"penalty:PI","intentional grounding":"penalty:grounding",
    "dead call":"dead_call","penalty":"penalty","missed the play":"play_missed",
    "didn't see":"play_missed","didnt see":"play_missed","couldn't see":"play_missed",
    "come back to this":"review","note this":"review","need to doc":"review",
}
OUTCOMES = [
    (r"touchdown|\btd\b","TD"), (r"interception|\bint\b|intercept","INT"),
    (r"sack","sack"), (r"fumble","fumble"),
    (r"incompl|\binc\b|incompet","incomplete"), (r"no gain|no yards|0 yards|nothing","no_gain"),
    (r"first down|1st down|\bfirst\b","first_down"),
    (r"completion|complete|caught|catch|reception","complete"),
]

def find_box(line):
    m = re.search(r"(\d)\s*(?:in\s+)?(?:the\s+)?(?:box|nox)", line)
    if m and m.group(1) in "5678": return int(m.group(1))
    m = re.search(r"(?:box|nox)\D{0,4}(\d)", line)
    if m and m.group(1) in "5678": return int(m.group(1))
    return None

def find_shell(line):
    for pat,val in SHELL_PATTERNS:
        if re.search(pat, line): return val
    return None

def find_coverage(line):
    for k in ["cover four","cover 0","cover0","cover 1","cover 2","cover 3","cover 4",
              "four deep","solid"," man ","zone"]:
        if k in line: return COVERAGE_MAP.get(k.strip(), COVERAGE_MAP.get(k))
    if re.search(r"\bin man\b", line): return "man"
    if re.search(r"\b1\s*(?:hi|high)\b", line): return "cover 3"  # user rule: 1 high = cover 3
    return None

def find_blitz(line):
    for pat in BLITZ_PATTERNS:
        if re.search(pat, line): return re.search(pat, line).group(0).strip()
    return None

def find_outcome(line):
    for pat,val in OUTCOMES:
        if re.search(pat, line): return val
    return None

def find_yards(line):
    m = re.search(r"(-?\d{1,2})\s*yard", line)
    if m: return int(m.group(1))
    return None

ALIASES={"buble":"bubble","rhyino":"rhino","switchpick":"switch","siwtch":"switch",
         "incompolete":None,"compelte":None}
PASS_KW={"fade","hitch","slant","post","curl","snag","out","wheel","boot","swing","flat",
         "spike","bend","shark","quad","pop","dig","sluggo","over","under","spot","stop","hook","comeback"}
RUN_KW={"power","counter","trap","toss","sweep","slam","iso","bear","sumo","larry","rich",
        "punch","rhino","dragon","bull","special","read","jet"}

def _named(token):
    if token in ALIASES: return ALIASES[token]
    if token in PLAY_NAMES: return token
    for nm in PLAY_NAMES:
        if len(nm)>=4 and nm in token: return nm   # substring catch (switchpick->switch)
    return None

def find_play(line):
    num=None; name=None; family=None; broken="Y" if "broken play" in line else ""
    # number + concept  e.g. "47 power", "23 dragon", "61 switchpick"
    m=re.search(r"\b([2-9]\d)\s+([a-z]+)", line)
    if m:
        nm=_named(m.group(2))
        if nm: num=int(m.group(1)); name=nm
    # standalone known concept
    if name is None:
        for w in re.findall(r"[a-z]+", line):
            nm=_named(w)
            if nm: name=nm; break
        if name:
            m2=re.search(r"\b([2-9]\d)\b", line)
            if m2: num=int(m2.group(1))
    # QB-run family (overrides/augments)
    qb=re.search(r"qb\s*(run|carry|keeper|kept|sneak|scramble|sweep|power|flow|read|pass)", line)
    if qb:
        family="qb_pass" if qb.group(1)=="pass" else "qb_run"
        if name is None: name="qb "+qb.group(1)
    # generic fallbacks when no named concept
    if name is None and "qb" in line and broken:
        name="qb run"; family="qb_run"
    if name is None:
        if re.search(r"\bscreen\b", line): name="screen"; family=family or "pass"
        elif re.search(r"throw\s*(?:it\s*)?away|threw.*away|thrown away", line): name="throwaway"; family="pass"
        elif re.search(r"\b(run|running|rush)\b|run up (?:the )?middle", line): name="run"; family=family or "run"
        elif re.search(r"\b(pass|throw|threw|deep pass)\b", line): name="pass"; family=family or "pass"
    # family from explicit keyword vocab (only when confident; named numbers left blank)
    if family is None and name:
        if name in RUN_KW: family="run"
        elif name in PASS_KW: family="pass"
    return num,name,family,broken

def find_direction(line):
    for d in ["right","left","middle"]:
        if re.search(rf"\b{d}\b", line): return d
    return None

def find_formation(line):
    found=[]
    for f in ["rip pro","rip strong","rip plus","rip","louie","left strong","right strong",
              "left weak","right weak","left minus","left plus","right right","boundary","field",
              "jumbo","tight","empty","trip","wing","deuce tight"]:
        if f in line and f not in ("right","left"): found.append(f)
    return ", ".join(dict.fromkeys(found)) if found else None

def find_flags(line):
    out=[]
    for k,v in FLAGS.items():
        if k in line: out.append(v)
    return ", ".join(dict.fromkeys(out)) if out else None

DOWN_RE = re.compile(r"^\s*([1-4])(?:st|nd|rd|th)?\b")
def parse_down_dist(line):
    down=None; dist_bucket=None; dist_explicit=None; goal=False
    if re.search(r"goal", line): goal=True
    m = re.search(r"\b([1-4])(?:st|nd|rd|th)?\s+and\s+(\d{1,2})", line)
    if m:
        down=int(m.group(1)); dist_explicit=int(m.group(2)); return down,dist_bucket,dist_explicit,goal
    dm = DOWN_RE.match(line)
    if dm: down=int(dm.group(1))
    # s/m/l bucket: second slash-token
    parts=[p.strip() for p in line.split("/")]
    if len(parts)>1 and parts[1] in ("s","m","l"): dist_bucket=parts[1]
    # explicit small distance like "4/1/" (4th and 1)
    if len(parts)>1 and re.fullmatch(r"\d{1,2}", parts[1]) and down in (3,4):
        dist_explicit=int(parts[1])
    return down,dist_bucket,dist_explicit,goal

def is_drive_header(line):
    return bool(re.match(r"^\s*(drive|1st drive|2nd drive|\d+(?:st|nd|rd|th)?\s+drive)\b", line, re.I)) \
        or bool(re.match(r"^\s*drive\s*\d", line, re.I))

def is_structural(line):
    l=line.lower()
    if is_drive_header(l): return "drive"
    if re.search(r"second half|2nd half|second quarter|quarter 2|end of (?:first )?half|"
                 r"4th quarter|fourth quarter|end of quarter|second half", l): return "section"
    if l in ("play log","final report","summary"): return "skip"
    if re.search(r"punt|field ?goal|fieldgoal|2 ?(?:pt|point) conversion|victory|2 pt conversion", l) \
       and not re.match(r"^[1-4]", l): return "special_teams"
    return None

def sticky_directive(line):
    """Detect drive-level defaults like '7 in box unless noted', 'in cover 4 unless noted'."""
    l=line.lower(); box=None; cov=None; shell=None
    if re.search(r"unless\s*(?:otherwise\s*)?noted|until\s*(?:said\s*)?(?:otherwise|noted)|"
                 r"all\s*plays|every\s*play|everyplay|this drive", l):
        box=find_box(l); cov=find_coverage(l); shell=find_shell(l)
    return box,cov,shell

# ---------- main ----------
rows=[]; idx=0
for game,fname in FILES.items():
    path=os.path.join(UP,fname)
    if not os.path.exists(path) or os.path.getsize(path)==0: continue
    lines=load(path)
    drive=0; cur_box=None; sticky_cov=None; sticky_shell=None; pidx=0
    for line in lines:
        low=line.lower()
        if re.search(r"final report|^summary$|final notes", low):
            break  # rest of file is prose narrative, not plays
        st=is_structural(low)
        if st=="drive":
            drive+=1
            b,c,s=sticky_directive(low)
            if b: cur_box=b
            sticky_cov=c; sticky_shell=s
            continue
        if st in ("section","skip","special_teams"):
            # section markers may carry sticky coverage ("in cover 4 unless noted")
            b,c,s=sticky_directive(low)
            if b: cur_box=b
            if c: sticky_cov=c
            if s: sticky_shell=s
            continue
        # drive-internal sticky directive line w/o a down
        if DOWN_RE.match(line) is None and re.search(r"unless|every play|all plays|until", low):
            b,c,s=sticky_directive(low)
            if b: cur_box=b
            if c: sticky_cov=c
            if s: sticky_shell=s
            # may still contain a play; fall through only if it has a down — it doesn't, so skip
            continue

        down,db,de,goal=parse_down_dist(line)
        # pure penalty / dead-call lines with no down
        flags=find_flags(low)
        box=find_box(low)
        if box is not None: cur_box=box
        shell=find_shell(low) or sticky_shell
        cov=find_coverage(low) or sticky_cov
        blitz=find_blitz(low)
        outcome=find_outcome(low)
        yards=find_yards(low)
        num,name,family,broken=find_play(low)
        direction=find_direction(low)
        formation=find_formation(low)

        # confidence / review taxonomy
        has_play = name is not None or num is not None
        if not has_play and not flags and outcome is None and down is None \
           and box is None and cov is None:
            review="empty"
        elif down is None and has_play:
            review="no_down"
        elif down is None and not has_play and flags:
            review=None
        elif down is None and not has_play:
            review="observation_only"
        elif has_play:
            review=None
        elif flags:
            review=None            # legit penalty / dead-call row
        elif outcome:
            review="result_only"   # real play, only the result was logged
        else:
            review="presnap_or_note"

        pidx+=1; idx+=1
        rows.append({
            "game":game,"drive":drive,"play_idx":pidx,
            "down":down,"dist_bucket":db,"dist_explicit":de,"goal_to_go":"Y" if goal else "",
            "formation":formation,"play_number":num,"play_name":name,"play_family":family,
            "broken_play":broken,"direction":direction,
            "box_count":cur_box,"shell_presnap":shell,"coverage_postsnap":cov,"blitz":blitz,
            "outcome":outcome,"yards":yards,"flag":flags,"review":review,"raw":line,
        })

json.dump(rows, open("/home/claude/parsed.json","w"), indent=0)
print(f"games={len(set(r['game'] for r in rows))}  rows={len(rows)}")
from collections import Counter
print("play rows w/ a name:", sum(1 for r in rows if r['play_name']))
print("play family set:", sum(1 for r in rows if r['play_family']))
print("review tags:", dict(Counter(r['review'] for r in rows)))
print("box filled:", sum(1 for r in rows if r['box_count'] is not None),"/",len(rows))
print("coverage present:", sum(1 for r in rows if r['coverage_postsnap']))
print("shell present:", sum(1 for r in rows if r['shell_presnap']))
