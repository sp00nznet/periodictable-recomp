# Testing

## The conformance harness

```
py -3 -I tools\pt_diff.py [--only orig|recomp] [--recomp build\periodictablerecomp.exe]
```

It runs the same script on the original (`game\Periodic_Table_2002.exe`) and
on the recomp, each on a hidden desktop (`tools/rp.py`), so nothing reaches
the screens and it works over RDP: wait for the main window, click **Fe**,
then **Search > Search Elements**, type `Au`, OK. After each step it captures
the main window with `PrintWindow` into `work\diff\<who>_<step>.png` and
compares the two pictures pixel for pixel. The element panel is drawn with
windowless VB labels (no `WM_GETTEXT`), so the pixels are the text.

Figure: **3 of 3 IDENTICAL** at v0.1.0. Reruns on 2026-11-12 gave 1 and 2
of 3, with the differences only in the caption and menu bar (y 7-43) and a
different step each run: the active/inactive caption, a harness timing issue
still to fix.

It needs Pillow in the Python that runs it. `-I` skips user site-packages,
so a `pip install --user pillow` into the Microsoft Store Python is not seen;
use a python.org Python (`py -3.12 -I tools\pt_diff.py`) with Pillow
installed for all users. It exits 0 only when every step is
identical. Without `game\` it prints `SKIP: no game/Periodic_Table_2002.exe`
and exits 0, so a machine without the program (netlab's test VMs) reports a
skip, not a pass.

`--recomp` takes another host, for example netlab's
`build-farm\periodictablerecomp.exe` (recipe `projects/periodictable-recomp.env`
in recomp-netlab).

## Tracing

`--native-trace` prints every call into `msvbvm60.dll` to stderr;
`NATIVE32_TRACE_EH=1` traces VB runtime errors and where they resume.
