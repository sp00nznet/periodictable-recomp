r"""Conformance harness: the same script on the original and the recomp, screens diffed.

    py -3 -I tools/pt_diff.py [--only orig|recomp] [--recomp build/periodictablerecomp.exe]

Both run on a hidden desktop (tools/rp.py). The script: wait for the main
window; click Fe (element details); Search > Search Elements, type Au, OK
(the search). After each step the main window is captured with PrintWindow
into work/diff/<who>_<step>.png and the two are compared pixel for pixel.
The element labels are windowless VB Labels (no WM_GETTEXT), so the pixels
are the text. Exit 0 when every step is IDENTICAL; SKIP (exit 0) without game\."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rp  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, 'game')
EXE = os.path.join(GAME, 'Periodic_Table_2002.exe')
HOST = os.path.abspath(sys.argv[sys.argv.index('--recomp') + 1] if '--recomp' in sys.argv
                       else os.path.join(ROOT, 'build', 'periodictablerecomp.exe'))
OUT = os.path.join(ROOT, 'work', 'diff')


def main_form(pid):
    f = [h for h in rp.tops(pid) if rp.cls(h) == 'ThunderRT6FormDC']
    return f[0] if f else None


def click(h):
    r = rp.W.RECT(); rp.u.GetClientRect(h, rp.ctypes.byref(r))
    lp = (r.bottom // 2) << 16 | (r.right // 2)
    rp.u.SendMessageW(h, 0x201, 1, lp); rp.u.SendMessageW(h, 0x202, 0, lp)   # WM_LBUTTONDOWN/UP


def run(who, cmd):
    pid = rp.launch(cmd, GAME, log=os.path.join(OUT, who + '.log'))
    shots = []
    try:
        m = rp.wait(lambda: main_form(pid), 'main window', 60)
        time.sleep(3)
        def snap(step):
            p = os.path.join(OUT, '%s_%s.png' % (who, step)); rp.snap(m, p); shots.append(p)
        snap('1_start')
        click(next(c for c in rp.kids(m) if rp.text(c) == 'Fe')); time.sleep(1.5)
        snap('2_element_Fe')
        rp.u.PostMessageW(m, 0x111, 7, 0)                       # Search > Search Elements
        dlg = rp.wait(lambda: next((h for h in rp.tops(pid) if rp.text(h) == 'Element Search'), None),
                      'search box', 20)
        buf = rp.ctypes.create_unicode_buffer('Au')
        rp.u.SendMessageW(rp.u.GetDlgItem(dlg, 4900), 0x000C, 0, rp.ctypes.addressof(buf))   # WM_SETTEXT
        print('edit holds', repr(rp.text(rp.u.GetDlgItem(dlg, 4900)))) if os.environ.get('PT_DUMP') else None
        rp.u.PostMessageW(rp.u.GetDlgItem(dlg, 1), 0xF5, 0, 0)    # BM_CLICK on OK
        rp.wait(lambda: not rp.u.IsWindow(dlg), 'search box to close', 20); time.sleep(1.5)
        rp.dump(pid) if os.environ.get('PT_DUMP') else None
        snap('3_search_Au')
    finally:
        rp.kill(pid)
    return shots


def same(a, b):
    from PIL import Image, ImageChops
    A, B = Image.open(a), Image.open(b)
    if A.size != B.size:
        return 'size %s vs %s' % (A.size, B.size)
    box = ImageChops.difference(A, B).getbbox()
    return None if box is None else 'differs in %s' % (box,)


# The original itself draws its start screen one of two ways at random: the
# bold captions come out one pixel wider or narrower (3 of 8 runs of the
# unmodified exe one way, and the share drifts over minutes; a Windows font
# measurement race, stable within a run, the recomp has it too). So the
# pair (recomp, original) is run up to ATTEMPTS times, back to back, and it
# passes when one pair matches at every step.
ATTEMPTS = 4


def main():
    if not os.path.exists(EXE):
        print('SKIP: no game/Periodic_Table_2002.exe'); return 0
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
    for k in range(ATTEMPTS if only is None else 1):
        r = run('recomp', '"%s" --run --game "%s" %s' % (HOST, GAME, os.environ.get('PT_HOSTARGS', ''))) if only != 'orig' else []
        o = run('orig', '"%s"' % EXE) if only != 'recomp' else []
        if not (o and r):
            return 0
        diffs = [same(a, b) for a, b in zip(o, r)]
        if not any(diffs) or k == ATTEMPTS - 1:
            break
        print('attempt %d: %d/%d steps identical, again' % (k + 1, diffs.count(None), len(diffs)))
    for a, d in zip(o, diffs):
        print('%-14s %s' % (os.path.basename(a)[5:-4], d or 'IDENTICAL'))
    print('%d/%d steps identical' % (diffs.count(None), len(diffs)))
    return 1 if any(diffs) or len(o) != len(r) else 0


if __name__ == '__main__':
    sys.exit(main())
