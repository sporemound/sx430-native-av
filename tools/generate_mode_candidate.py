"""Build the experimental Lua candidate from a locally supplied, verified ROM."""
from pathlib import Path
import argparse, hashlib, re, struct
import sx430
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_HANDLER_SHA256='d0d209d83797cc649e3002ecea0344ef39c155ed2528194c0f0ea8d0737da4ee'
def generate(rom):
    if not sx430.verify_firmware(rom)['matches_sx430_100b']:
        raise ValueError('ROM does not match SX430 IS 1.00B')
    start,stop=0xff05f154,0xff05f748
    region=rom[start-sx430.ROM_BASE:stop-sx430.ROM_BASE]
    if hashlib.sha256(region).hexdigest()!=EXPECTED_HANDLER_SHA256:
        raise ValueError('Mode handler differs from reviewed code')
    words=[(addr,struct.unpack_from('<I',rom,addr-sx430.ROM_BASE)[0]) for addr in range(start,stop,4)]
    assert len(words)==381
    template=(ROOT/'camera/experimental/native-mode.lua.in').read_text()
    body='local firmware_words={\n'+''.join('    {0x%08x,0x%08x},\n'%w for w in words)+'}\nassert(#firmware_words==381,"Incomplete firmware fingerprint")\n'
    begin='-- FIRMWARE_WORDS_BEGIN\n';end='-- FIRMWARE_WORDS_END'
    return template.split(begin)[0]+begin+body+end+template.split(end)[1]
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--out',type=Path,default=ROOT/'private/generated-candidate.lua')
    a=p.parse_args()
    text=generate(a.rom.read_bytes())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x',encoding='utf-8') as out: out.write(text)
    print('Generated experimental candidate. Keep it and its firmware source private.')
if __name__=='__main__':main()
