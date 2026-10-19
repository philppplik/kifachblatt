#!/usr/bin/env python3
"""Immutable, content-addressed editorial snapshots. Network refresh is explicit."""
from pathlib import Path
import json,hashlib,datetime,urllib.request,argparse
ROOT=Path(__file__).resolve().parents[1]
REPOS={'openai':'openai/openai-python','anthropics':'anthropics/anthropic-sdk-python','googleapis':'googleapis/python-genai','mistralai':'mistralai/client-python','nvidia':'NVIDIA-NeMo/Speech','meta-llama':'meta-llama/llama-api-python'}
def store(kind,data):
 blob=(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();digest=hashlib.sha256(blob).hexdigest();folder=ROOT/'content/portrait-snapshots'/kind;folder.mkdir(parents=True,exist_ok=True);p=folder/(datetime.date.today().isoformat()+'-'+digest[:16]+'.json')
 if not p.exists():
  with p.open('xb') as f:f.write(blob)
 return p

def archive(data):
 return store('editorial',data)
def refresh():
 for key,repo in REPOS.items():
  req=urllib.request.Request('https://api.github.com/repos/'+repo,headers={'User-Agent':'KI-Portraits/1.0','Accept':'application/vnd.github+json'})
  # No credentials, bounded to six public repositories. Stop on throttling/errors.
  with urllib.request.urlopen(req,timeout=20) as response:
   raw=json.load(response)
  fields={k:raw[k] for k in ['full_name','html_url','stargazers_count','forks_count','pushed_at','archived','language','license']}
  store('github-'+key,{'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'https://api.github.com/repos/'+repo,'data':fields})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--refresh-github',action='store_true');args=a.parse_args()
 if args.refresh_github:refresh()
 else:archive(json.loads((ROOT/'content/portraits.json').read_text()))
