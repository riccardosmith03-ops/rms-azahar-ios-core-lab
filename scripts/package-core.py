#!/usr/bin/env python3
"""Package a newly built, unsigned iPhoneOS libretro framework. No installation."""
import argparse,hashlib,json,pathlib,plistlib,shutil,struct,subprocess,zipfile
MINIMUM=(17,4,0)
INSTALL_NAME='@rpath/azahar.libretro.framework/azahar.libretro'
class Rejected(ValueError):pass
def require(ok,message):
    if not ok:raise Rejected(message)
def version(value):return (value>>16,(value>>8)&255,value&255)
def macho(data,expected_min=MINIMUM):
    require(len(data)>=32,'Truncated Mach-O header')
    magic,cpu,subtype,kind,ncmds,sizecmds,flags,reserved=struct.unpack_from('<8I',data)
    require(magic==0xfeedfacf,'Expected a thin little-endian 64-bit Mach-O')
    require(cpu==0x0100000c and (subtype&0xffffff)==0,'Expected arm64 (not arm64e or simulator architecture)')
    require(kind==6,'Expected MH_DYLIB')
    require(0<ncmds<=4096 and 8*ncmds<=sizecmds<=len(data)-32,'Invalid load command area')
    offset=32;end=32+sizecmds;build=[];deps=[];ids=[];rpaths=[];signature=False
    def string_at(start,size,field,minimum=12):
        rel=struct.unpack_from('<I',data,start+field)[0]
        require(minimum<=rel<size,'Invalid load-command string offset')
        value=data[start+rel:start+size];require(b'\0'in value,'Unterminated load-command string')
        try:return value.split(b'\0',1)[0].decode('utf-8')
        except UnicodeDecodeError as e:raise Rejected('Invalid UTF-8 load-command string')from e
    for _ in range(ncmds):
        require(offset+8<=end,'Truncated load command')
        cmd,size=struct.unpack_from('<II',data,offset)
        require(size>=8 and size%4==0 and offset+size<=end,'Invalid load command bounds')
        if cmd==0x32:
            require(size>=24,'Truncated LC_BUILD_VERSION');platform,minimum,sdk,ntools=struct.unpack_from('<4I',data,offset+8)
            require(24+8*ntools<=size,'Invalid build tools array');build.append((platform,version(minimum),version(sdk)))
        elif cmd in (0xc,0xd,0x80000018,0x8000001f,0x20,0x80000023):
            require(size>=24,'Truncated dylib command');name=string_at(offset,size,8,24)
            (ids if cmd==0xd else deps).append(name)
        elif cmd==0x8000001c:
            require(size>=12,'Truncated LC_RPATH');rpaths.append(string_at(offset,size,8))
        elif cmd==0x1d:
            require(size>=16,'Truncated LC_CODE_SIGNATURE');start,count=struct.unpack_from('<II',data,offset+8)
            require(start<=len(data) and count<=len(data)-start,'Code signature outside binary');signature=True
        elif cmd==0x27:raise Rejected('Unexpected dyld environment command')
        offset+=size
    require(offset==end,'Load command size mismatch')
    require(len(build)==1 and build[0][0]==2,'Expected one native iOS platform build command')
    require(build[0][1]==expected_min,'Unexpected minimum iOS version')
    require(len(ids)==1,'Expected one LC_ID_DYLIB')
    require(all(x.startswith(('/System/Library/','/usr/lib/')) for x in deps),'Non-system dynamic dependency: framework is not self-contained')
    require(all(x in ('@loader_path','@loader_path/..','@executable_path/Frameworks') for x in rpaths),'Unexpected runtime search path')
    return {'architecture':'arm64','filetype':'MH_DYLIB','platform':'iOS','minimum_ios':'.'.join(map(str,build[0][1])),'sdk':'.'.join(map(str,build[0][2])),'install_name':ids[0],'dependencies':deps,'rpaths':rpaths,'has_code_signature':signature}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(*args):return subprocess.check_output(list(args),text=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('--binary',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    carrier=pathlib.Path(__file__).resolve().parents[1];lock=json.loads((carrier/'source-lock.json').read_text());binary=pathlib.Path(a.binary)
    require(binary.is_file() and not binary.is_symlink(),'Input must be a real built file');binary=binary.resolve(strict=True)
    out=pathlib.Path(a.out).resolve();require(not out.exists(),'Output directory must be new; refusing overwrite')
    before=macho(binary.read_bytes());out.mkdir(parents=True);fw=out/'azahar.libretro.framework';fw.mkdir();target=fw/'azahar.libretro';shutil.copy2(binary,target)
    run('xcrun','install_name_tool','-id',INSTALL_NAME,str(target))
    if before['has_code_signature']:run('/usr/bin/codesign','--remove-signature',str(target))
    run('xcrun','strip','-x',str(target));info=macho(target.read_bytes())
    require(info['install_name']==INSTALL_NAME and not info['has_code_signature'],'Final framework must have the expected ID and be unsigned')
    symbols=set(run('xcrun','nm','-gU','-j',str(target)).splitlines());require(set(lock['required_exports'])<=symbols,'Missing standard libretro ABI export')
    plist={'CFBundleIdentifier':'azahar.libretro','CFBundleExecutable':'azahar.libretro','CFBundleName':'azahar.libretro','CFBundlePackageType':'FMWK','CFBundleVersion':'2127.3','CFBundleShortVersionString':'2127.0','MinimumOSVersion':'17.4','CFBundleSupportedPlatforms':['iPhoneOS'],'RMSUpstreamCommit':lock['upstream_commit'],'RMSRuntimeLayoutPatchSHA256':lock['patch_sha256']}
    (fw/'Info.plist').write_bytes(plistlib.dumps(plist,fmt=plistlib.FMT_XML,sort_keys=True));target.chmod(0o755)
    source=out/'corresponding-source';source.mkdir()
    for name in ('LICENSE.txt','README.txt','source-lock.json'):shutil.copy2(carrier/name,source/name)
    portable=('patches/0001-rms-runtime-layout.patch','scripts/verify-source.py',
              'scripts/build-core.sh','scripts/package-core.py',
              'tests/runtime_layout_policy_test.cpp','tests/test-package-core.py')
    for name in portable:
        dest=source/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(carrier/name,dest)
    # Only the explicitly staged framework and portable source recipe enter the ZIP.
    records=[]
    for path in sorted(out.rglob('*')):
        if path.is_file():records.append({'path':path.relative_to(out).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
    inspection={'status':'STATIC_INSPECTION_PASS_RUNTIME_UNTESTED','source_commit':lock['upstream_commit'],'patch_sha256':lock['patch_sha256'],'minimum_ios':'17.4','unsigned':True,'abi_exports_verified':len(lock['required_exports']),'binary':info,'files':records,'jit_enabled_by_patch':False,'fps40_implemented':False}
    (out/'inspection.json').write_text(json.dumps(inspection,indent=2)+'\n',encoding='utf-8')
    archive=out/'rms-azahar-runtime-layout-UNSIGNED.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for f in records:z.write(out/f['path'],f['path'])
        z.write(out/'inspection.json','inspection.json')
    with zipfile.ZipFile(archive) as z:require(z.testzip()is None,'ZIP CRC failure')
    print(json.dumps({'package':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'status':inspection['status']}))
if __name__=='__main__':main()
