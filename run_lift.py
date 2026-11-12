#!/usr/bin/env python3
"""Periodic Table 2002 lift driver: work/functions.json -> src/recomp/gen/.

Periodic_Table_2002.exe 1.2.1 (Visual Basic 6, native code, base 0x00400000)
is the whole program; MSVBVM60.DLL runs natively. AmazingMIDI's driver (from
Bully's), with the VB6 header (pcrecomp tools/pe/vb6.py) deciding what is code
and where On Error resumes.

    py -3 run_lift.py
"""
import argparse
import json
import os
import re
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
# PCRECOMP picks the toolkit checkout, the same knob CMakeLists.txt has: the
# lifter and the runtime header must come from the same tree.
_TOOLS = os.path.join(os.environ.get('PCRECOMP', os.path.join(_HERE, '..', 'pcrecomp')), 'tools')
sys.path.insert(0, os.path.join(_TOOLS, 'lift'))
sys.path.insert(0, os.path.join(_TOOLS, 'pe'))

from capstone import Cs, CS_ARCH_X86, CS_MODE_32          # noqa: E402
from generate import (EXTENT_REACH, find_splits, true_extent,  # noqa: E402
                      linear_disassemble_function, lift_function_linear, write_chunk)
from lift32 import Lifter                                  # noqa: E402
from eh32 import resume_points                             # noqa: E402
from pe_analyze import analyze_pe, build_iat_map           # noqa: E402
from vb6 import VB6Image                                   # noqa: E402
import pefile                                              # noqa: E402

WORK = os.path.join(_HERE, 'work')
EXE = os.path.join(WORK, 'Periodic_Table_2002.exe')
OUT = os.path.join(_HERE, 'src', 'recomp', 'gen')
STAMP = 0x414900DF                                        # 2004-09-16, v1.2.1


def load_seeds(path):
    """Addresses from a seed file: a list of {'address': va} or of plain VAs."""
    if not os.path.exists(path):
        return set()
    return {e['address'] if isinstance(e, dict) else e for e in json.load(open(path))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--split', type=int, default=400, help='functions per .c file')
    args = ap.parse_args()
    catalog = os.path.join(WORK, 'functions.json')
    if not os.path.exists(EXE):
        sys.exit('no %s -- README, Getting started' % EXE)
    if pefile.PE(EXE, fast_load=True).FILE_HEADER.TimeDateStamp != STAMP:
        sys.exit('%s is not Periodic Table 2002 1.70 (PE stamp 0x%08X expected); the README says where to get it'
                 % (EXE, STAMP))
    if not os.path.exists(catalog):
        sys.exit('no catalog at %s -- run disasm32.py first (README, Step by step)' % catalog)
    t0 = time.time()

    info = analyze_pe(EXE)
    iat = build_iat_map(info)
    cs, ce = info.code_start, info.code_end
    print('[*] base=0x%08X code=0x%08X-0x%08X IAT=%d' % (info.image_base, cs, ce, len(iat)))
    # A VB6 .text is mostly data (the VB header, object tables, strings, form
    # data): only the native code range, the event stubs and the import
    # thunks are code (pcrecomp tools/pe/vb6.py). The catalog's linear sweep
    # finds hundreds of "functions" in the rest; they are dropped.
    vb = VB6Image(EXE)
    entry = info.image_base + info.entry_point_rva
    code_ok = lambda a: vb.is_code(a) or a == entry          # noqa: E731
    byaddr = {f['address']: f for f in json.load(open(catalog))['functions'] if code_ok(f['address'])}
    print('[*] VB6 %s, code 0x%08X-0x%08X, %d event handlers' % ('native' if vb.native else 'P-CODE',
                                                               vb.code_start, vb.code_end, len(vb.seeds())))
    # Seeds: vtable slots, plus the unresolved targets runs reported
    # (seed_from_log.py -> work/run_seeds.json). Those found in bring-up are
    # kept in seeds/run_seeds.json, which is committed: addresses only, and a
    # fresh checkout has to lift the same functions.
    want = {a for a in load_seeds(os.path.join(WORK, 'seeds.json'))
            | load_seeds(os.path.join(WORK, 'run_seeds.json'))
            | load_seeds(os.path.join(_HERE, 'seeds', 'run_seeds.json'))
            | set(vb.seeds())
            if code_ok(a)} - set(byaddr)
    for a in want:
        byaddr[a] = {'address': a, 'entry_kind': 'start'}
    print('[*] catalog %d functions, +%d seeded entries' % (len(byaddr) - len(want), len(want)))

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    text = [s for s in info.sections if s.name == '.text'][0]
    code = open(EXE, 'rb').read()[text.raw_offset:text.raw_offset + text.raw_size]
    # The whole image as mapped, for the EH tables in .rdata.
    mapped = pefile.PE(EXE).get_memory_mapped_image()
    base = info.image_base
    read = lambda va, n: mapped[va - base:va - base + n] if 0 <= va - base < len(mapped) else None  # noqa: E731
    # precise carry: adc/sbb take their carry from the flag state that set it
    # (64-bit adds and subtracts; ra2's run_lift.py has the history).
    # computed ret: VB native code runs its cleanup block as `push resume; jmp
    # cleanup` ... `ret`, so a ret to an address it pushed is a jump.
    lifter = Lifter(iat_map=iat, lifted=set(byaddr), precise_carry=True, precise_sbb=True,
                    computed_ret=True)

    os.makedirs(OUT, exist_ok=True)
    for fn in os.listdir(OUT):                       # a smaller lift must not leave stale chunks
        if fn.startswith('recomp_') and fn.endswith('.c'):
            os.remove(os.path.join(OUT, fn))
    starts = {a for a in byaddr if byaddr[a].get('entry_kind') != 'alias'}
    starts -= find_splits(md, code, cs, ce, starts)   # still dispatchable, just not a wall
    # Where a function resumes after its own catch blocks. Nothing branches
    # there (the catch funclet returns the address), so the catalog often
    # starts a function at it and the parent's body stops short.
    eh_at = {}
    for a in byaddr:
        r = resume_points(md, read, list(md.disasm(read(a, 64) or b'', a))[:12])
        if r:
            eh_at[a] = r
    # A VB procedure with On Error: the runtime continues inside it at its
    # handler labels and Resume Next points, with its own ebp (entry esp - 4).
    vb_eh = vb.error_resumes()
    for a, pts in vb_eh.items():
        eh_at[a] = sorted(set(eh_at.get(a, ())) | set(pts))
        byaddr.setdefault(a, {'address': a})
    starts -= set().union(*eh_at.values()) if eh_at else set()

    entries, chunk, idx, errors, dirty, ehs, unimpl = [], [], 0, 0, 0, 0, {}
    # A direct branch or call to an address nothing catalogued is a tail call
    # or shared code the catalog missed; it has to be dispatchable, so each
    # round's outside targets are lifted in the next, until none are new.
    todo, added = sorted(byaddr), 0
    while todo:
        outside = set()
        for addr in todo:
            fname = 'sub_%08X' % addr
            reached, behind, called = set(), set(), set()
            end, clean = true_extent(md, code, cs, addr, min(addr + EXTENT_REACH, ce), starts,
                                     reached=reached, behind=behind, called=called)
            for r in eh_at.get(addr, ()):
                if cs <= r < ce:
                    e2, _ = true_extent(md, code, cs, r, min(r + EXTENT_REACH, ce), starts,
                                        reached=reached, behind=behind, called=called)
                    end = max(end, e2)
            outside |= {t for t in behind if t not in reached} | called
            dirty += not clean
            try:
                lo = min(reached) if reached else addr
                insns, leaders = (linear_disassemble_function(md, code, cs, lo, end, reached=reached)
                                  if end > addr else ([], None))
                if leaders is not None:
                    leaders.add(addr)
                eh = eh_at.get(addr)
                ehs += bool(eh)
                body = (lift_function_linear(lifter, fname, insns, leaders, addr, eh_resume=eh,
                                             eh_off=4 if addr in vb_eh else None) if insns
                        else 'void %s(void) { }\n' % fname)
            except Exception as e:                  # noqa: BLE001 -- counted, not hidden
                body = '/* ERROR %s: %s */\nvoid %s(void) { }\n' % (fname, e, fname)
                errors += 1
            for m in re.findall(r'UNIMPLEMENTED: (\w+)', body):   # lifted as a no-op: says so
                unimpl[m] = unimpl.get(m, 0) + 1
            chunk.append((body, addr, fname))
            entries.append(addr)
            if len(chunk) >= args.split:
                write_chunk(OUT, idx, chunk)
                idx, chunk = idx + 1, []
                print('[*]   %d lifted (%d err)' % (len(entries), errors), flush=True)
        todo = sorted(t for t in outside if code_ok(t) and t not in byaddr)
        for t in todo:
            byaddr[t] = {'address': t}
        added += len(todo)
    if chunk:
        write_chunk(OUT, idx, chunk)
        idx += 1

    entries.sort()
    with open(os.path.join(OUT, 'recomp_funcs.h'), 'w', newline='\n') as f:
        f.write('/* Periodic_Table_2002.exe - AUTO-GENERATED by run_lift.py */\n#pragma once\n#include <stdint.h>\n\n'
                + ''.join('void sub_%08X(void);\n' % a for a in entries))
    with open(os.path.join(OUT, 'recomp_dispatch.c'), 'w', newline='\n') as f:
        f.write('/* Periodic_Table_2002.exe - AUTO-GENERATED by run_lift.py */\n'
                '#include "recomp_types.h"\n#include "recomp_funcs.h"\n\n'
                'const recomp_dispatch_entry_t recomp_dispatch_table[] = {\n'
                + ''.join('    { 0x%08Xu, sub_%08X },\n' % (a, a) for a in entries)
                + '};\nconst uint32_t recomp_dispatch_count = %d;\n'
                  'const uint32_t pt_entry_va = 0x%08Xu;\n' % (len(entries), entry))

    lines = sum(sum(1 for _ in open(os.path.join(OUT, fn), encoding='utf-8', errors='replace'))
                for fn in os.listdir(OUT))
    stats = {'lifted': len(entries), 'added': added, 'errors': errors, 'no_terminator': dirty,
             'catch': ehs, 'files': idx, 'lines': lines, 'unimplemented': unimpl}
    json.dump(stats, open(os.path.join(WORK, 'lift_stats.json'), 'w'), indent=1)
    print('=' * 60)
    print('  lifted %d (+%d outside the catalog)   errors %d   no terminator %d   catch %d'
          % (len(entries), added, errors, dirty, ehs))
    if unimpl:
        print('  unimplemented: ' + ' '.join('%s %d' % kv for kv in sorted(unimpl.items(), key=lambda kv: -kv[1])))
    print('  %s lines of C in %d files, %.0fs' % (format(lines, ','), idx, time.time() - t0))
    print('=' * 60)


if __name__ == '__main__':
    main()
