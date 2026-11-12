# Contributing

Issues and pull requests are welcome.

## The one rule

**Nothing from the program goes in the repository.** No exe, no OCX, no
runtime DLL, no lifted C (`src/recomp/gen/`), no catalog (`work/`), no
disassembly listings, nothing generated from `Periodic_Table_2002.exe`. The
tool ships; its output is made on each person's machine from their own copy.
`.gitignore` covers the usual paths; check `git status` before you commit
anyway. Screenshots of the program running are fine.

## Before a pull request

1. Build from a clean lift: `py -3 run_lift.py` (expected: `errors 0`), then
   `build.cmd`.
2. Run the conformance harness ([docs/testing.md](docs/testing.md)):
   ```
   py -3 -I tools\pt_diff.py
   ```
   No step may lose an identical element panel or table (the caption flake is in docs/testing.md). A new behavior comes with a step that
   shows it.

## Where your code comes from

Original work or MIT-compatible only. Don't port anything from Wine, ReactOS
or another GPL project.

## Where a fix belongs

- A bug in the lifter, the catalog, `vb6.py` or the native32 runtime belongs
  in [pcrecomp](https://github.com/sp00nznet/pcrecomp) (today on branch
  `pcrecomp-periodictable`), not here.
- A fix to the program itself is a patch in `run_lift.py`, with a comment
  that says what it fixes and why.
- A wall you got past goes in `docs/bringup.md`: what it looked like, what it
  was, what moved it.
