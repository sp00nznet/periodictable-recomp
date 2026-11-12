# Periodic Table 2002 — Static Recompilation

Static recompilation of **Periodic Table 2002** 1.2.1 (Clint Garafolo, 2002-2004),
a Visual Basic 6 periodic table reference, from its shipping Win32 executable
to native C. The VB6 code (native code, not P-code) is lifted, and Microsoft's
own VB6 runtime, `msvbvm60.dll`, runs beside it as a native module, with the
program's OCX controls. It runs the author's code; it is not a rewrite. It is
pcrecomp's first Visual Basic program.

Built on the [pcrecomp](https://github.com/sp00nznet/pcrecomp) toolchain,
branch **`pcrecomp-periodictable`** (the VB6 runtime support, not merged into
`main` yet), following its shared house style like the other
[pcrecomp projects](https://github.com/sp00nznet/pcrecomp#the-projects-that-built-this).

![Iron, after clicking Fe](docs/screenshots/element-iron.png)

## Getting Started

You need **your own copy of Periodic Table 2002 1.2.1**: `Periodic Table
2002.msi` (on the Internet Archive in the Tucows collection, item
`tucows_363354_Periodic_Table_2002`), or the folder it installed to. Nothing
from the program is in this repository or downloaded for you. You don't have
to install it: Setup unpacks the .msi with `msiexec /a`, which installs
nothing, and takes the program and its four OCX controls from it.

### The setup scripts

1. Download this repository (the green **Code** button, then **Download ZIP**)
   and unzip it somewhere with 300 MB free.
2. Windows: double-click **`Setup.cmd`**. There is no Linux or macOS build
   yet; `setup.sh` says so and exits.
3. Run it with the **`Periodic Table 2002`** shortcut in that folder.

The script asks before installing anything (Python, `pefile` and `capstone`,
Git, the Visual Studio 2022 Build Tools), clones pcrecomp's
`pcrecomp-periodictable` branch beside this folder, asks where the .msi is
(`-GameDir <path>` skips the question, `-Yes` answers yes to every install),
then catalogs, lifts and builds `build\periodictablerecomp.exe`. A rerun
skips finished steps; if it stops it says why, and the details are in
`setup.log`. The build takes about 3 minutes. Building by hand, step by step,
is in **[docs/building.md](docs/building.md)**.

It is trialware: the program counts its own 5-day trial in
`HKCU\Software\Periodic Table 2002`, and the recompilation runs that
unchanged.

## Status

**v0.1.0, alpha.** It starts, shows an element's details and searches. The
conformance harness compares those three screens with the original's pixel
for pixel: 3 of 3 IDENTICAL when v0.1.0 was tagged. Reruns on 2026-11-12 (a
fresh clone and this checkout) gave 1 and 2 of 3: the element panel, the
table and the search result match every time, and the differing pixels are
only in the caption and menu bar (y 7-43), which step varies run to run, so
it reads as window-activation timing in the harness rather than the lift
(ROADMAP.md).

| | |
|---|---|
| Functions found (`disasm32`) | 991; 760 in the VB code range, the rest is VB data |
| Lifted to C | 912, 0 errors, 9 procedures with `On Error` landing pads |
| Imports (`msvbvm60.dll`) | 99: 80 native, 19 shimmed, 0 unresolved |
| Harness (`tools/pt_diff.py`) | startup, click Fe, search Au: 3 of 3 at v0.1.0; 1-2 of 3 on today's reruns, caption and menu bar only |

Not checked yet: Print, Check for Update, the Key form, About. There is no
`--headless --record` mode yet; the harness runs on a hidden desktop instead.
[bringup.md](docs/bringup.md) is the log of each wall and its fix, and
[ROADMAP.md](ROADMAP.md) what comes next.

## Screenshots

Captured by the harness from the recompiled program:

| | |
|---|---|
| ![Iron, after clicking Fe](docs/screenshots/element-iron.png) | ![Gold, found by Search > Search Elements](docs/screenshots/search-gold.png) |

## Documentation

- [docs/building.md](docs/building.md): building by hand, the command line, the pieces
- [docs/testing.md](docs/testing.md): the conformance harness
- [docs/bringup.md](docs/bringup.md): every wall so far and its fix
- [ROADMAP.md](ROADMAP.md), [CHANGELOG.md](CHANGELOG.md), [CONTRIBUTING.md](CONTRIBUTING.md)

## Contributors

See **[CONTRIBUTORS.md](CONTRIBUTORS.md)** for who did what.

## License

MIT for this repository's own code ([LICENSE](LICENSE)). Periodic Table 2002
is © Clint Garafolo / GarfInc, and the VB6 runtime and controls are ©
Microsoft; none of their files, and nothing generated from them, is in this
repository ([NOTICE.md](NOTICE.md)).
