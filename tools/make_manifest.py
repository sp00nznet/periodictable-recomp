r"""Write a registration-free COM manifest for the app's two OCX controls.

    py -3 -I tools/make_manifest.py game

The installer registers PowerButton.ocx and activelock1884.ocx in HKCR; we
never run it (or regsvr32). Instead Periodic_Table_2002.exe.manifest beside
the exe lists every control class from each OCX's type library, and Windows
(and the recomp host, through CreateActCtx) finds them from that."""
import ctypes, ctypes.wintypes as W, os, sys, uuid

oa = ctypes.OleDLL('oleaut32')
oa.SysFreeString.argtypes = [ctypes.c_void_p]
P = ctypes.c_void_p


def call(obj, slot, *args, res=ctypes.HRESULT):
    """Call vtable slot `slot` of COM object pointer `obj`."""
    vt = ctypes.cast(ctypes.cast(obj, ctypes.POINTER(P))[0], ctypes.POINTER(P))
    return ctypes.WINFUNCTYPE(res, P, *[P if type(a).__name__ == "CArgObject" else type(a) for a in args])(vt[slot])(obj, *args)


def guid(p):
    return '{%s}' % str(uuid.UUID(bytes_le=ctypes.string_at(p, 16))).upper()


def name_of(tl, idx):
    b = ctypes.c_wchar_p()
    call(tl, 9, ctypes.c_int(idx), ctypes.byref(b), P(), P(), P())   # ITypeLib::GetDocumentation
    return b.value


def ocx_entry(path):
    tl = P()
    oa.LoadTypeLibEx(ctypes.c_wchar_p(path), 2, ctypes.byref(tl))      # REGKIND_NONE
    la = P(); call(tl, 7, ctypes.byref(la))                            # GetLibAttr
    tlb = guid(la)
    raw = ctypes.string_at(la.value + 24, 4)
    ver = '%d.%d' % (int.from_bytes(raw[:2], 'little'), int.from_bytes(raw[2:], 'little'))
    lib = name_of(tl, -1)
    out = ['  <file name="%s">' % os.path.basename(path),
           '    <typelib tlbid="%s" version="%s" helpdir="" flags=""/>' % (tlb, ver)]
    for i in range(call(tl, 3, res=ctypes.c_uint)):                    # GetTypeInfoCount
        ti = P(); call(tl, 4, ctypes.c_uint(i), ctypes.byref(ti))
        ta = P(); call(ti, 3, ctypes.byref(ta))                        # GetTypeAttr
        kind = ctypes.c_int.from_address(ta.value + 44).value          # x64 TYPEATTR.typekind
        if kind == 5:                                                  # TKIND_COCLASS
            out.append('    <comClass clsid="%s" tlbid="%s" threadingModel="Apartment" progid="%s.%s"'
                       ' miscStatusContent="recomposeonresize,cantlinkinside,insideout,activatewhenvisible,setclientsitefirst"/>'
                       % (guid(ta), tlb, lib, name_of(tl, i)))
    return out + ['  </file>']


def main():
    game = sys.argv[1] if len(sys.argv) > 1 else 'game'
    lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">',
             '  <assemblyIdentity name="PeriodicTable2002" version="1.2.1.0" type="win32"/>']
    for f in ('PowerButton.ocx', 'activelock1884.ocx', 'comdlg32.ocx', 'msinet.ocx'):
        lines += ocx_entry(os.path.abspath(os.path.join(game, f)))
    lines.append('</assembly>')
    out = os.path.join(game, 'Periodic_Table_2002.exe.manifest')
    open(out, 'w', newline='\r\n').write('\n'.join(lines) + '\n')
    print('wrote', out)


if __name__ == '__main__':
    main()
