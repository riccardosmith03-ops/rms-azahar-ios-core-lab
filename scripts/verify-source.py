#!/usr/bin/env python3
import argparse,hashlib,json,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('--upstream',required=True);p.add_argument('--phase',choices=['before','after'],required=True);a=p.parse_args()
carrier=pathlib.Path(__file__).resolve().parents[1];root=pathlib.Path(a.upstream).resolve(strict=True);lock=json.loads((carrier/'source-lock.json').read_text())
def git(*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert git('rev-parse','HEAD')==lock['upstream_commit'],'Wrong upstream commit'
assert sha(carrier/lock['patch'])==lock['patch_sha256'],'Patch hash mismatch'
assert all(line.startswith(' ') for line in subprocess.check_output(['git','-C',str(root),'submodule','status','--recursive'],text=True).splitlines()),'Uninitialized or mismatched submodule'
for name,digest in lock['protected_build_sources'].items():assert sha(root/name)==digest,'Build source changed: '+name
for dep in lock.get('dependency_files',[]):
 path=root/dep['path'];digest=dep['before_sha256'] if a.phase=='before' else dep['after_sha256']
 assert path.is_file() and not path.is_symlink() and sha(path)==digest,'Dependency source hash mismatch: '+dep['path']
 assert subprocess.check_output(['git','-C',str(root/dep['submodule']),'rev-parse','HEAD'],text=True).strip()==dep['submodule_commit'],'Wrong pinned dependency commit'
for f in lock['files']:
 path=root/f['path'];digest=f['before_sha256'] if a.phase=='before' else f['after_sha256']
 if digest is None:assert not path.exists(),'New header already exists'
 else:assert path.is_file() and not path.is_symlink() and sha(path)==digest,'Source hash mismatch: '+f['path']
if a.phase=='before':
 assert not git('status','--porcelain'),'Source was not clean'
 for dep in lock.get('dependency_files',[]):
  assert not subprocess.check_output(['git','-C',str(root/dep['submodule']),'status','--porcelain','--untracked-files=all'],text=True).strip(),'Dependency was not clean'
else:
 changed=set(git('diff','--ignore-submodules=none','--name-only').splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines())
 assert changed==({f['path']for f in lock['files']}|{d['submodule']for d in lock.get('dependency_files',[])}),'Unexpected changed source files'
 for dep in lock.get('dependency_files',[]):
  sub=root/dep['submodule']
  subchanges=set(subprocess.check_output(['git','-C',str(sub),'diff','--name-only'],text=True).splitlines())|set(subprocess.check_output(['git','-C',str(sub),'ls-files','--others','--exclude-standard'],text=True).splitlines())
  assert subchanges=={dep['relative_path']},'Unexpected dependency source changes'
print('Fixed source and '+a.phase+'-patch hashes verified.')
