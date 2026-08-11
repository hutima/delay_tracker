#!/usr/bin/env python3
"""Leakage-safe checkpoint and static dashboard builder (standard library only)."""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).parent; ET=ZoneInfo("America/New_York")
START=date(2026,8,5); END=date(2026,8,14); VERSION="0.1.0-prior-only"
FIELDS=["run_id","generated_at_utc","as_of_utc","as_of_et","target_date","target_type","scheduled_departure","checkpoint_at","hours_to_departure","cadence_band","is_final_t4","embargo_cutoff","latest_feature_timestamp","model_version","p_b6_cancel","p_b6_severe_delay_operates","p_sq23_disruption","p_pair_success","p_miss_sq23","p_itinerary_disruption","p_reach_sin_within_6h","previous_probability","delta_probability_pp","delta_log_odds","alert_threshold","alert_status","confidence_low","confidence_high","confidence_label","data_quality_flags","source_manifest_ref","actual_outcome","score_brier","supersedes_run_id"]

def dates():
 d=START
 while d<=END: yield d; d+=timedelta(days=1)
def schedule(d, target):
 # User-supplied approximate times, explicitly unverified until an eligible source is ingested.
 local=datetime.combine(d,time(16,30) if target!="SQ23" else time(22,15),ET)
 return local.astimezone(timezone.utc)
def checkpoints(dep):
 hs=list(range(120,47,-6))+list(range(46,3,-2))
 return [(dep-timedelta(hours=h),h,"6h" if h>=48 else "2h") for h in hs]
def probs(h):
 # Transparent prior-only regularized-logistic fallback; deliberately broad intervals.
 horizon=(120-h)/116
 cancel=1/(1+math.exp(-(-3.55+0.12*horizon)))
 severe=1/(1+math.exp(-(-3.1+0.10*horizon)))
 sq=1/(1+math.exp(-(-4.0+0.08*horizon)))
 # Pair-level logistic layer, not a naive component multiplication.
 pair_dis=1/(1+math.exp(-(-2.72+1.1*cancel+0.9*severe+0.8*sq)))
 miss=pair_dis*.58; itin=pair_dis*.72
 return cancel,severe,sq,1-pair_dis,miss,itin,1-itin*.55
def iso(x): return x.isoformat().replace("+00:00","Z")
def make_rows(asof):
 rows=[]
 for d in dates():
  for target in ("B6317","SQ23","PAIR"):
   dep=schedule(d,target)
   prev=None
   for cp,h,band in checkpoints(dep):
    p=probs(h); current={"B6317":p[0],"SQ23":p[2],"PAIR":1-p[3]}[target]
    lo=lambda x: math.log(x/(1-x))
    rid=hashlib.sha256(f"{d}|{target}|{iso(cp)}|{VERSION}".encode()).hexdigest()[:16]
    rows.append(dict(zip(FIELDS,[rid,iso(asof),iso(cp),cp.astimezone(ET).isoformat(),str(d),target,iso(dep),iso(cp),h,band,str(h==4).lower(),iso(dep-timedelta(hours=3)),"",VERSION,*[f"{x:.6f}" for x in p],"" if prev is None else f"{prev:.6f}","" if prev is None else f"{(current-prev)*100:.4f}","" if prev is None else f"{lo(current)-lo(prev):.6f}","0.200000","alert" if current>=.2 else "no-alert",f"{max(0,current-.10):.6f}",f"{min(1,current+.10):.6f}","low","schedule_unverified;no_eligible_observations;prior_only","data/source_manifest.json","","",""])))
    prev=current
 return rows
def write_csv(path, rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open("w",newline="") as f:
  w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
def validate(rows):
 for r in rows:
  cp=datetime.fromisoformat(r["checkpoint_at"].replace("Z","+00:00")); em=datetime.fromisoformat(r["embargo_cutoff"].replace("Z","+00:00"))
  assert cp<em and int(r["hours_to_departure"])>=4
  assert (int(r["hours_to_departure"])>=48 and r["cadence_band"]=="6h") or (int(r["hours_to_departure"])<48 and r["cadence_band"]=="2h")
def dashboard(rows,asof):
 latest={}
 for r in rows:
  cp=datetime.fromisoformat(r["checkpoint_at"].replace("Z","+00:00"))
  if r["target_type"]=="PAIR" and cp<=asof: latest[r["target_date"]]=r
 payload={"generated_at":iso(asof),"model_version":VERSION,"dates":[],"predictions":rows}
 for d in dates():
  ds=str(d); r=latest[ds]; completed=datetime.combine(d,time(23),ET).astimezone(timezone.utc)<asof
  frozen=asof>=schedule(d,"PAIR")-timedelta(hours=4)
  status="historical replay pending evidence" if completed else ("frozen final T−4h provisional" if frozen else "live provisional")
  payload["dates"].append({"date":ds,"status":status,"schedule_quality":"User-provided approximate; not independently verified","actual":"Unavailable — no eligible outcome source ingested","weather_vintages":[{"lead":x,"status":"Unavailable — source acquisition not authenticated"} for x in ["D-4","D-3","D-2","D-1","D"]],"latest":r})
 p=ROOT/"data/public/dashboard_data.json"; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,indent=2)+"\n")
def build(asof):
 rows=make_rows(asof); validate(rows)
 write_csv(ROOT/"data/snapshots/prediction_runs.csv",rows); write_csv(ROOT/"model/probability_history.csv",rows)
 write_csv(ROOT/"model/live_predictions.csv",[r for r in rows if r["target_type"]=="PAIR"])
 write_csv(ROOT/"model/paired_predictions_2026-08-05_to_2026-08-14.csv",[r for r in rows if r["target_type"]=="PAIR" and r["is_final_t4"]=="true"])
 dashboard(rows,asof)
 state={"version":VERSION,"generated_at":iso(asof),"kind":"regularized logistic prior-only fallback","coefficients":{"cancel_intercept":-3.55,"severe_delay_intercept":-3.1,"sq23_intercept":-4.0,"pair_intercept":-2.72},"warning":"Not fitted: no timestamp-verifiable training observations are present."}
 (ROOT/"model").mkdir(exist_ok=True); (ROOT/"model/model_state.json").write_text(json.dumps(state,indent=2)+"\n")
def main():
 ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
 for c in ("build","append"):
  x=sp.add_parser(c); x.add_argument("--as-of",required=True)
 a=ap.parse_args(); asof=datetime.fromisoformat(a.as_of.replace("Z","+00:00")).astimezone(timezone.utc)
 if a.cmd=="build": build(asof)
 else:
  path=ROOT/"data/snapshots/prediction_runs.csv"; old=list(csv.DictReader(path.open())) if path.exists() else []
  fresh=[r for r in make_rows(asof) if datetime.fromisoformat(r["checkpoint_at"].replace("Z","+00:00"))<=asof]
  seen={r["run_id"] for r in old}; combined=old+[r for r in fresh if r["run_id"] not in seen]; validate(combined); write_csv(path,combined); dashboard(combined,asof)
if __name__=="__main__": main()
