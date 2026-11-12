# Building

The technical route; `Setup.cmd` runs exactly these steps.

Prerequisites: Python 3.10+ (`py -3`, or `python`; the Microsoft Store's
`python` alias is not Python), `pip install pefile capstone pillow`, Visual
Studio 2022 or its Build Tools with "Desktop development with C++" (CMake and
Ninja come with it), and the toolkit beside this folder:

```
  some-folder\
    pcrecomp\        <- git clone -b pcrecomp-periodictable https://github.com/sp00nznet/pcrecomp
    periodictable\   <- this repository
```

1. Unpack the .msi (nothing is installed) and copy the exe, as
   `Periodic_Table_2002.exe`, and the four controls into `game\`, and the exe
   into `work\` too:
   ```
   msiexec /a "C:\path\Periodic Table 2002.msi" /qn TARGETDIR=%TEMP%\pt2002
   mkdir game work
   copy "%TEMP%\pt2002\Program Files\Periodic Table 2002\Periodic Table 2002.exe" game\Periodic_Table_2002.exe
   copy "%TEMP%\pt2002\Program Files\Common Files\*.ocx" game\
   copy "%TEMP%\pt2002\Windows\System32\Redist\MS\System\comdlg32.ocx" game\
   copy "%TEMP%\pt2002\Windows\System32\Redist\MS\System\msinet.ocx" game\
   copy game\Periodic_Table_2002.exe work\
   ```
2. Write the manifest that names every control (nothing is registered):
   ```
   py -3 -I tools\make_manifest.py game
   ```
   Expected: `wrote game\Periodic_Table_2002.exe.manifest`.
3. Catalog the functions:
   ```
   py -3 ..\pcrecomp\tools\disasm\disasm32.py work\Periodic_Table_2002.exe -o work\functions.json
   ```
   Expected, last lines: `Functions: 991` ... `Wrote work/functions.json`.
4. Lift:
   ```
   py -3 run_lift.py
   ```
   Expected: `lifted 912 (+0 outside the catalog)   errors 0 ... catch 9`.
5. Build (the compiler is found by `build.cmd`):
   ```
   build.cmd
   ```
   Expected: `Linking C executable periodictablerecomp.exe`.
6. Run:
   ```
   build\periodictablerecomp.exe --run
   ```

Trip-ups: `run_lift.py` and `build.cmd` look for the toolkit at
`..\pcrecomp`; set `PCRECOMP` (and `CMAKE_ARGS=-DPCRECOMP=...`) if it is
elsewhere. "Error 339: Component ... not correctly registered" means an OCX or
the manifest is missing from `game\`.

## Usage

```
build\periodictablerecomp.exe --run                    # the program
build\periodictablerecomp.exe                          # map and bind only, then stop
build\periodictablerecomp.exe --run --watchdog 60      # end it after 60 s
build\periodictablerecomp.exe --run --native-trace     # every call into msvbvm60, to stderr
set NATIVE32_TRACE_EH=1                                # trace VB runtime errors and where they resume
py -3 -I tools\pt_diff.py                              # the conformance check, below
```

## The pieces

The steps above are the build. The host is `src/runtime/host.c` (from the
AmazingMIDI recomp's); the lift driver is `run_lift.py`, which keeps only the
code a VB6 exe really has (pcrecomp `tools/pe/vb6.py`): the native code range,
the event and Declare stubs, and gives each procedure with `On Error` a
landing pad for the runtime's resume points. [bringup.md](bringup.md)
has the story of each piece.
