# Changelog

## [0.1.0] - 2026-11-12

### Added
- `Periodic_Table_2002.exe` 1.2.1 (Visual Basic 6, native code) lifted to C:
  912 functions, 0 errors, on pcrecomp's `native32` with the real
  `msvbvm60.dll` as a native module (needs pcrecomp branch
  `pcrecomp-periodictable`: `tools/pe/vb6.py`, `runtime/native32/vb6rt.c`).
- `run_lift.py`: keeps only the code a VB6 exe has (the native code range, its
  event, vtable and Declare stubs; the rest of `.text` is VB data), seeds the
  event handlers and cleanup blocks from the VB header, and gives the 9
  procedures with `On Error` a landing pad at every resume point.
- `tools/make_manifest.py`: a registration-free COM manifest for the four OCX
  controls, so nothing is registered (the original reads the same manifest).
- `tools/pt_diff.py`: the conformance harness. Start, click Fe, search Au, on
  the original and the recomp on a hidden desktop, window pixels compared:
  3/3 IDENTICAL.
- `Setup.cmd` / `tools/setup.ps1`: the one-click route, from the .msi
  (unpacked with `msiexec /a`, nothing installed) or an installed folder; ends
  with a `Periodic Table 2002` shortcut.
- A netlab recipe (`projects/periodictable-recomp.env` in recomp-netlab).
