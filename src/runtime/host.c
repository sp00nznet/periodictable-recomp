/*
 * Periodic Table 2002 - static recompilation host.
 *
 * A 32-bit host on pcrecomp's runtime/native32 (the native bridge, callbacks
 * and the machine lock; see its header). The lifted Periodic_Table_2002.exe
 * is a native-code Visual Basic 6 program: every import is MSVBVM60.DLL, which
 * runs natively with the guest's registers and stack, and whose runtime
 * errors reach the program's On Error handlers (native32_vb6_runtime,
 * vb6rt.c). What is here is only the guest image, its folder, its command
 * line, the OCX controls' activation context and the fault report. From the
 * AmazingMIDI host.
 *
 * Linked at /BASE:0x60000000 (CMakeLists.txt) so 0x00400000 is free when
 * main() maps the image.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "native32.h"
#include "recomp_trace.h"

extern const uint32_t pt_entry_va;       /* recomp_dispatch.c */

#define PT_BASE 0x00400000u

static DWORD g_watchdog_s;
static char  g_app[MAX_PATH];            /* the app folder, with a trailing '\' */
static char  g_guest_exe[MAX_PATH];


/* ------------------------------------------------------------ reports */

recomp_func_t recomp_lookup_manual(uint32_t va) { (void)va; return NULL; }

/* Added after native32's own handler, so callbacks are resolved first and
 * only real faults get here. */
static LONG CALLBACK crash(EXCEPTION_POINTERS* ep) {
    EXCEPTION_RECORD* r = ep->ExceptionRecord;
    if ((r->ExceptionCode & 0xF0000000u) != 0xC0000000u) {
        fprintf(stderr, "[exception] 0x%08lX at 0x%p, in sub_%08X, last native call %s\n",
                r->ExceptionCode, r->ExceptionAddress, g_cur_func, g_cur_import);
        return EXCEPTION_CONTINUE_SEARCH;
    }
    fprintf(stderr, "\n=== fault 0x%08lX at 0x%p ===\n", r->ExceptionCode, r->ExceptionAddress);
    if (r->ExceptionCode == EXCEPTION_ACCESS_VIOLATION && r->NumberParameters >= 2) {
        ULONG_PTR op = r->ExceptionInformation[0];
        uint32_t at = (uint32_t)r->ExceptionInformation[1];
        fprintf(stderr, "  %s of 0x%08X%s\n", op == 0 ? "read" : op == 1 ? "write" : "execute", at,
                native32_in_guest(at) ? " (inside the guest image)" : at < 0x10000 ? " (null/low)" : "");
    }
    recomp_trace_flush();
    fprintf(stderr, "  in lifted sub_%08X, last native call %s\n", g_cur_func, g_cur_import);
    fprintf(stderr, "  eax=%08X ecx=%08X edx=%08X ebx=%08X esp=%08X ebp=%08X esi=%08X edi=%08X\n",
            g_eax, g_ecx, g_edx, g_ebx, g_esp, g_ebp, g_esi, g_edi);
    native32_dump_icalls(12);
    recomp_dump_trace("fault");
    TerminateProcess(GetCurrentProcess(), 3);
    return EXCEPTION_CONTINUE_SEARCH;
}

static DWORD WINAPI watchdog(LPVOID unused) {
    (void)unused;
    Sleep(g_watchdog_s * 1000);
    fprintf(stderr, "\n[watchdog] %lu s: in sub_%08X, last native call %s\n",
            g_watchdog_s, g_cur_func, g_cur_import);
    TerminateProcess(GetCurrentProcess(), 4);
    return 0;
}

int main(int argc, char** argv) {
    const char* app = "game";
    int run = 0;
    setvbuf(stderr, NULL, _IONBF, 0);
    for (int i = 1; i < argc; i++) {
        int n = recomp_trace_arg(argc, argv, i);
        if (n) { i += n - 1; continue; }
        if (!strcmp(argv[i], "--run")) run = 1;
        else if (!strcmp(argv[i], "--game") && i + 1 < argc) app = argv[++i];
        else if (!strcmp(argv[i], "--watchdog") && i + 1 < argc) g_watchdog_s = strtoul(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--native-trace")) native32_trace_native = 1;
        else if (!strcmp(argv[i], "--callbacks")) native32_trace_callbacks = 1;
        else {
            printf("usage: periodictablerecomp [--run] [--game DIR] [--watchdog S]\n"
                   "                         [--native-trace] [--callbacks]\n"
                   "  without --run: map and bind Periodic_Table_2002.exe, then stop (no window)\n");
            recomp_trace_help();
            return argv[i][1] == 'h' || argv[i][2] == 'h' ? 0 : 1;
        }
    }
    GetFullPathNameA(app, MAX_PATH - 1, g_app, NULL);
    if (g_app[strlen(g_app) - 1] != '\\') strcat(g_app, "\\");
    _snprintf(g_guest_exe, sizeof g_guest_exe - 1, "%sPeriodic_Table_2002.exe", g_app);

    native32_init();
    /* The OCX controls come from Periodic_Table_2002.exe.manifest (tools/
     * make_manifest.py), not the registry: the same activation context the
     * original gets from Windows, made by hand for this host. */
    char man[MAX_PATH];
    _snprintf(man, sizeof man - 1, "%s.manifest", g_guest_exe);
    ACTCTXA ac = { sizeof ac, ACTCTX_FLAG_ASSEMBLY_DIRECTORY_VALID, man };
    ac.lpAssemblyDirectory = g_app;
    HANDLE hac = CreateActCtxA(&ac);
    ULONG_PTR cookie;
    if (hac == INVALID_HANDLE_VALUE || !ActivateActCtx(hac, &cookie))
        fprintf(stderr, "no activation context from %s (%lu): run tools/make_manifest.py\n", man, GetLastError());
    AddVectoredExceptionHandler(0, crash);
    printf("Periodic Table 2002 recomp host\n  lifted functions in dispatch: %u\n", recomp_dispatch_count);
    uint32_t span = native32_map(g_guest_exe, PT_BASE);
    if (!span) { fprintf(stderr, "cannot map %s at 0x%08X\n", g_guest_exe, PT_BASE); return 1; }
    printf("  mapped Periodic_Table_2002.exe: 0x%08X-0x%08X\n", PT_BASE, PT_BASE + span);
    int unresolved = native32_bind(PT_BASE, NULL, 0);   /* every import is MSVBVM60's */
    printf("  imports bound, %d unresolved\n", unresolved);
    if (unresolved) return 1;
    /* MSVBVM60 runs with the guest ABI, and its errors reach On Error: vb6rt.c. */
    if (!native32_vb6_runtime()) fprintf(stderr, "MSVBVM60 was not set up (vb6rt.c)\n");
    if (!run) {
        printf("\n(dry run: image mapped and bound; --run enters 0x%08X)\n", pt_entry_va);
        return 0;
    }
    if (!SetCurrentDirectoryA(g_app)) { fprintf(stderr, "cannot enter %s\n", g_app); return 1; }
    if (g_watchdog_s) CloseHandle(CreateThread(NULL, 0, watchdog, NULL, 0, NULL));
    printf("  entering 0x%08X\n\n", pt_entry_va);
    fflush(stdout);
    native32_call_guest(pt_entry_va, 0, NULL);
    printf("\nentry returned eax=%08X\n", g_eax);
    return (int)g_eax;
}
