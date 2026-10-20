"""Export only the completed cohorts discussed in the paper; never run inference."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
DEST=Path(__file__).resolve().parents[1]/'data'
SOURCES=[
 ('main','Pretrained Qwen',6,'training_runs/head-goon-qwen-base-001-execution/results/games.json',{}),
 ('main','JEV',6,'data/jev-head-goon-baseline-001/results.json',{}),
 ('main','BC04',6,'training_runs/head-goon-bc04-greedy-001-execution/results/games.json',{}),
 ('main','PPO10',6,'training_runs/head-goon-greedy-004010-001-execution/results/games.json',{'checkpoint':'iteration-10'}),
 ('main','PPO10',6,'training_runs/head-goon-greedy-010015-001-execution/results/games.json',{'checkpoint':'iteration-10'}),
 ('main','PPO15',6,'training_runs/head-goon-ppo15-modes-001-execution/results/games.json',{'selection':'greedy'}),
 ('main','PPO15',6,'training_runs/head-goon-greedy-010015-001-execution/results/games.json',{'checkpoint':'iteration-15'}),
 ('randomized','BC04',6,'training_runs/head-goon-bc04-variation-001-execution/results/games.json',{}),
 ('randomized','PPO10',6,'training_runs/head-goon-variation-010015-001-execution/results/games.json',{'checkpoint':'iteration-10'}),
 ('randomized','PPO15',6,'training_runs/head-goon-variation-010015-001-execution/results/games.json',{'checkpoint':'iteration-15'}),
 ('randomized','JEV',6,'data/jev-head-goon-variation-001/results.json',{}),
 ('randomized','JEV delayed',6,'data/jev-head-goon-latency-001/results.json',{}),
]
for source in ['head-goon-ppo15-oneframe-001','head-goon-ppo15-oneframe-002-retry-01']:
 for env in ['main','randomized']:
  SOURCES.append((env,'PPO15',1,f'training_runs/{source}-execution/results/games.json',{'environment':env}))
FIELDS=['win','outcome','scenario','repeat','seed','entry_sha256','selection','frames','decisions','wall_seconds','boss_hits','direct_hits','damage_taken','reward_total','normalized_progress','spatial_cells_visited','stall_seconds','delay_median_ms']
def main():
 review=json.loads((ROOT/'training_runs/head-goon-bc04-variation-001-execution/review.json').read_text())
 if review['status']!='complete_reviewed' or review['games']!=50:raise ValueError('BC04 randomized audit not complete')
 base_review=json.loads((ROOT/'training_runs/head-goon-qwen-base-001-execution/review.json').read_text())
 if base_review['status']!='complete_reviewed' or base_review['games']!=50:raise ValueError('Pretrained Qwen audit not complete')
 DEST.mkdir(exist_ok=True);rows=[];sources={};seen=set()
 for environment,model,interval,name,filters in SOURCES:
  p=ROOT/name;data=p.read_bytes();sources[name]=hashlib.sha256(data).hexdigest()
  for index,g in enumerate(json.loads(data)):
   if not all(g.get(k)==v for k,v in filters.items()):continue
   run=g.get('artifact_run',g.get('provenance',{}).get('run',name))
   identity=(run,g.get('attempt',str(index)))
   if identity in seen:raise ValueError(f'Duplicate game: {identity}')
   seen.add(identity)
   rows.append({'environment':environment,'model':model,'post_action_frames':interval,'game_id':'/'.join(identity),'source':name,'source_index':index,**{k:g.get(k) for k in FIELDS}})
 (DEST/'games.json').write_text(json.dumps(rows,indent=2)+'\n')
 (DEST/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
 print(f'Exported {len(rows)} unique completed games from {len(sources)} sources.')
if __name__=='__main__':main()
