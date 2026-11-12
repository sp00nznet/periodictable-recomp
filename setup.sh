#!/bin/sh
# There is no Linux or macOS build of this recompilation yet: the host runs on
# pcrecomp's native32, which calls the real 32-bit msvbvm60.dll and the
# program's OCX controls, and that has only been built and tested on Windows.
echo "Periodic Table 2002 recomp: only Windows is supported so far. Run Setup.cmd on Windows."
echo "See ROADMAP.md."
exit 1
