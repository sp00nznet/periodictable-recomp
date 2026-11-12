# Notice

The MIT license in [LICENSE](LICENSE) covers what is ours in this repository:
the host, the lift driver, the setup scripts, the tools and the documentation.
It does not cover the program.

*Periodic Table 2002* is © 2002-2004 Clint Garafolo / GarfInc (trialware), and
the Visual Basic 6 runtime and controls (`msvbvm60.dll`, `comdlg32.ocx`,
`msinet.ocx`) are © Microsoft. None of them is ours to license. Their
executables, controls and data are not in this repository and are excluded by
`.gitignore`.

- You need your own copy of the program to use any of this. Setup copies it
  from your .msi or install into `game/`; the pipeline reads it from there.
- Lifted code is a derivative work of the binary it came from. Anything the
  pipeline writes into `work/` or `src/recomp/gen*/` carries whatever license
  the original carries, not this one. The MIT grant stops at our own work.

The host (`src/runtime/host.c`) and `run_lift.py` started from the AmazingMIDI
recomp's, and `tools/rp.py` is the Retail Plus Lite recomp's: all our own
work, MIT. There is no third-party code in this repository.
