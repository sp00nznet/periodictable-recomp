# Bring-up: Periodic Table 2002, pcrecomp's first Visual Basic 6 program

How a native-code VB6 exe came up on `native32`, in the order things broke.
The toolkit half is in pcrecomp `main`
(`tools/pe/vb6.py`, `runtime/native32/vb6rt.c`).

## The download

`tucows_363354_Periodic_Table_2002.zip` holds `Periodic_Table_2002.zip`, which
holds `Periodic Table 2002.msi`: a Windows Installer package made with Wise
for Windows Installer, not a Wise script installer (so pcrecomp's
`extract_wise.py` is not the tool here). `msiexec /a` unpacks it without
installing anything, and gives the full tree: the exe, `PowerButton.ocx`,
`activelock1884.ocx`, and the VB6 runtime redistributables (`msvbvm60.dll`,
`comdlg32.ocx`, `msinet.ocx`, ...). `7z x` gives only the four files of the
product's own cab; the runtime files are in merge-module streams 7z does not
list.

## P-code or native

The entry point is `push 0x004021B0; call ThunRTMain`. At 0x004021B0 is the
`VB5!` header; its ProjectInfo (+30h) has `lpNativeCode` = 0x00453000
(non-zero only in a native build) and the code range 0x004308D0-0x00451B50,
whose procedures start `55 8B EC` (`push ebp; mov ebp, esp`). **Native code**,
so it lifts like any x86, and MSVBVM60 runs natively beside it.
`py -3 ..\pcrecomp\tools\pe\vb6.py work\Periodic_Table_2002.exe` prints this.

## Registration-free controls

The original, run from the unpacked folder, fails with "Error 339: Component
'activelock1884.ocx' ... not correctly registered". Rather than register
anything, `tools/make_manifest.py` reads each OCX's type library and writes
`Periodic_Table_2002.exe.manifest`, a side-by-side manifest listing every
control class. Windows uses it for the original; the host makes the same
activation context with `CreateActCtx` before entering the program.

## What a VB6 .text holds

`disasm32` found 991 "functions". A VB6 `.text` is mostly data (the header,
object tables, BSTR constants, form data), and a third of those were strings
decoded as code. `run_lift.py` keeps only what `vb6.py` calls code: the native
range, the import thunks, the event stubs (`sub dword [esp+4], n; jmp
handler`), the vtable stubs (`jmp handler`) and the Declare stubs (`mov eax,
[cache]; or eax, eax; je; jmp eax; push decl; call DllFunctionCall`). The
event handlers come from the forms' event sink tables, which no call reaches.

## The runtime's calling convention

MSVBVM60's helpers are not the C ABI: `__vbaStrCopy`, `__vbaFreeStr`,
`__vbaVarMove` take ecx and edx; `__vbaChkstk` moves esp and zeroes the new
locals (a String local starts as a NULL BSTR, and the next `__vbaStrCopy` frees
whatever was there: heap corruption until it was zeroed). The fix is the one
Retail Plus Lite's CA-Visual Objects runtime got: the whole DLL is a
guest-ABI range (`native32_add_guest_abi`), entered with the guest's registers
on the guest's stack, and calling back with them.

The `_adj_fdiv_*`/`_adj_fprem*`/`_adj_fptan`/`_adj_fpatan` imports (the
Pentium FDIV workarounds) work on the x87 stack, which is the lifted one, so
they are native32 built-ins now, like `_CIsin`.

## Cleanup blocks: `push resume; jmp cleanup ... ret`

Every VB procedure exits through its cleanup block by pushing the address to
continue at and jumping; the block ends in `ret`. Lifted as a return, that
went back to the wrong caller and freed the same strings twice. The lifter's
`computed_ret` (Messiah's) makes such a `ret` a jump.

## Runtime errors and On Error

At startup the program takes three runtime errors on purpose (`On Error Resume
Next` around the license control and the network check). A VB error is a real
`RaiseException(0xC000008F)` inside MSVBVM60, and VB finds the procedure's
frame through fs:[0], where the guest's frames are not (they are in the
guest's own TIB). `vb6rt.c`:

- calls into MSVBVM60 run with the guest's SEH chain on the real fs:[0], so
  `__vbaOnError` writes the mode into the right frame;
- a vectored handler first asks the native frames above the guest's (a VB
  OCX's own procedures handle their own errors), then moves to the host stack
  and walks the guest's chain with seh32;
- `__vbaExceptHandler` continues inside the procedure through one small helper
  (`mov esp, [ebp+10h]; mov ebp, [ebp+0Ch]; call ecx; jmp ebx`), which is
  patched to longjmp into the lifted body's landing pad. `vb6.py
  error_resumes` reads each procedure's descriptor (`mov dword [ebp-14h],
  desc`): its `On Error GoTo` labels (desc+10h) and its Resume Next points
  (desc+14h, one per statement), and `run_lift.py` gives the procedure a
  `RECOMP_EH_FRAME` at those addresses.

`NATIVE32_TRACE_EH=1` prints each error, the statement it was in, and where it
resumed:

```
[vb6rt] in the procedure of frame 07F6F638, statement 11 at 0x0044DEEF
[vb6rt] continue at 0x0044DEEF, ebp 0x07F6F658 esp 0x07F6F528
```

The first version dispatched every 0xC000008F to the guest's frames, and the
license control's own handled error came out as the program's "Error 6:
Overflow in Main" box.

## The window frame

The recomp's window was 10 pixels bigger. Windows sizes a frame by the exe's
subsystem version, and the original is a 4.0 exe, so the host is linked
`/SUBSYSTEM:CONSOLE,5.01` (the oldest the linker allows). Then the pictures
matched.

## The harness

`tools/pt_diff.py` (on `tools/rp.py`'s hidden desktop): start, click Fe,
search Au; the main window captured after each step. The element panel is
windowless VB labels, so pixels, not WM_GETTEXT. The search box needs
WM_SETTEXT by message (SetWindowText from another process does not reach an
edit). The original itself renders its bold captions one pixel wider in some
runs (a Windows-side race, stable within a run), so the harness reruns the
pair until they agree, up to four times.
