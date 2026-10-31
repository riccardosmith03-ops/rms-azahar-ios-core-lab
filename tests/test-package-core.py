#!/usr/bin/env python3
import importlib.util,pathlib,struct,unittest,sys
sys.dont_write_bytecode=True
root=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('package_core',root/'scripts/package-core.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def textcmd(cmd,text):
 b=text.encode()+b'\0';size=(24+len(b)+7)//8*8
 return struct.pack('<6I',cmd,size,24,0,0,0)+b+b'\0'*(size-24-len(b))
def fixture(cpu=0x100000c,sub=0,kind=6,platform=2,minimum=0x110400,deps=('/usr/lib/libc++.1.dylib',),ids=1):
 cmds=[struct.pack('<6I',0x32,24,platform,minimum,0x1a0500,0)]
 cmds += [textcmd(0xd,m.INSTALL_NAME)]*ids
 cmds += [textcmd(0xc,x)for x in deps]
 b=b''.join(cmds);return struct.pack('<8I',0xfeedfacf,cpu,sub,kind,len(cmds),len(b),0,0)+b
class GateTests(unittest.TestCase):
 def test_native_dylib(self):self.assertEqual(m.macho(fixture())['minimum_ios'],'17.4.0')
 def test_reject_x86(self):self.assertRaises(m.Rejected,m.macho,fixture(cpu=0x1000007))
 def test_reject_arm64e(self):self.assertRaises(m.Rejected,m.macho,fixture(sub=2))
 def test_reject_app(self):self.assertRaises(m.Rejected,m.macho,fixture(kind=2))
 def test_reject_simulator(self):self.assertRaises(m.Rejected,m.macho,fixture(platform=7))
 def test_reject_future_minimum(self):self.assertRaises(m.Rejected,m.macho,fixture(minimum=0x120000))
 def test_reject_other_minimum(self):self.assertRaises(m.Rejected,m.macho,fixture(minimum=0xe0000))
 def test_reject_missing_id(self):self.assertRaises(m.Rejected,m.macho,fixture(ids=0))
 def test_reject_duplicate_id(self):self.assertRaises(m.Rejected,m.macho,fixture(ids=2))
 def test_reject_host_dependency(self):self.assertRaises(m.Rejected,m.macho,fixture(deps=('/opt/homebrew/lib/libfoo.dylib',)))
 def test_reject_missing_embedded_dependency(self):self.assertRaises(m.Rejected,m.macho,fixture(deps=('@rpath/libfoo.dylib',)))
 def test_reject_truncated_header(self):self.assertRaises(m.Rejected,m.macho,b'\0'*16)
 def test_reject_truncated_command(self):self.assertRaises(m.Rejected,m.macho,fixture()[:-1])
 def test_reject_command_overflow(self):
  b=bytearray(fixture());struct.pack_into('<I',b,36,0x10000);self.assertRaises(m.Rejected,m.macho,bytes(b))
 def test_reject_dylib_string_inside_header(self):
  b=bytearray(fixture());struct.pack_into('<I',b,64,12);self.assertRaises(m.Rejected,m.macho,bytes(b))
 def test_reject_string_outside_command(self):
  b=bytearray(fixture());struct.pack_into('<I',b,64,0xffff);self.assertRaises(m.Rejected,m.macho,bytes(b))
if __name__=='__main__':unittest.main(verbosity=2)
