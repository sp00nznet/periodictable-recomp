# One-click setup for the Periodic Table 2002 1.2.1 static recompilation. Run it by
# double-clicking Setup.cmd in the repo folder; the README's "Step by step" is
# the same thing by hand, command for command.
#
# It checks the tools, copies your Periodic Table 2002 and its four OCX
# controls into game\ (straight out of its .msi with msiexec /a, which installs
# nothing, or from an installed copy), writes a manifest for the controls,
# finds every function, lifts it to C, builds
# build\periodictablerecomp.exe and leaves a shortcut to it in this folder. Each
# step is skipped when its output already exists (-Force redoes them), so a
# rerun after a failure resumes. Everything it does goes to setup.log.
#
#   -GameDir <the .msi, or the installed folder>   skip the question (-Game works too)
#   -Yes                                        answer yes to every install question
#
# The toolkit is ..\pcrecomp (PCRECOMP overrides it). Under recomp-launcher
# (RECOMP_LAUNCHER=1) it never waits for Enter, and exit code 0 means the
# shortcut is there. Nothing is ever downloaded of Periodic Table 2002 itself.
param([switch]$Force, [switch]$Yes, [Alias('Game')][string]$GameDir = "")
$Game = $GameDir

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Toolkit = $env:PCRECOMP
if (-not $Toolkit) {
  $Toolkit = Join-Path (Split-Path -Parent $Root) 'pcrecomp'
}
$env:PCRECOMP = $Toolkit   # the Python steps read it too
$Log = Join-Path $Root 'setup.log'
Set-Location $Root
function Log($t) { Add-Content -Path $Log -Value $t -Encoding UTF8 }
Log "==== setup $(Get-Date -Format s)"

function Say($t, $c = 'Gray') { Write-Host $t -ForegroundColor $c; Log $t }
function Step($n, $t) { Write-Host ""; Say "[$n/7] $t" 'Cyan' }
function Pause-End { if (-not $Yes -and $env:RECOMP_LAUNCHER -ne '1') { Read-Host "Press Enter to close" | Out-Null } }
function Fail($t) {
  Say ""; Say "Setup stopped: $t" 'Red'
  Say "The details are in $Log. Fix that and run Setup.cmd again; finished steps are skipped." 'Yellow'
  Pause-End; exit 1
}
trap { Fail "$_" }
function Ask($q) { if ($Yes) { Say "$q yes"; return $true }; $a = Read-Host "$q [Y/n]"; return -not ($a -match '^[nN]') }
function Refresh-Path {
  $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}
# Run a program with its output in the log. Windows PowerShell turns a native
# program's stderr into errors, so 'Stop' is off while it runs.
function Exec([string[]]$cmd) {
  $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  $rest = @($cmd | Select-Object -Skip 1)   # @(): a one-element slice would splat as characters
  & $cmd[0] @rest 2>&1 | ForEach-Object { Log "$_" }
  $code = $LASTEXITCODE
  $ErrorActionPreference = $old
  return $code
}
function Run($what, [string[]]$cmd) {
  Say "  $what..."
  $code = Exec $cmd
  if ($code -ne 0) { Fail "$what failed (exit code $code)." }
}

if ($env:RECOMP_LAUNCHER -ne '1') { Clear-Host }
Say "Periodic Table 2002 1.2.1: static recompilation setup" 'White'
Say "You need your own installed copy of Periodic Table 2002 1.2.1 (the folder holding Periodic_Table_2002.exe) and about 300 MB free."

# ---------------------------------------------------------------- tools
Step 1 "Checking the tools"
# A Python that answers "Python 3.x". The Store's placeholder "python" (the
# one that opens the Store) answers nothing, so asking is the reliable test.
function Find-Python {
  # The per-user install winget makes, before PATH has it.
  $user = @(Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | ForEach-Object { ,@($_.FullName) })
  foreach ($c in (@(@('py', '-3'), @('python'), @('python3')) + $user)) {
    if (-not (Get-Command $c[0] -ErrorAction SilentlyContinue)) { continue }
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    $rest = @($c | Select-Object -Skip 1)
    $v = (& $c[0] @rest --version 2>&1 | Out-String).Trim()
    $ErrorActionPreference = $old
    if ($v -match '^Python 3\.(\d+)' -and [int]$Matches[1] -ge 10) { return ,$c }
  }
  return $null
}
$pyargs = Find-Python
if (-not $pyargs) {
  Say "  Python 3.10 or newer is not installed."
  if (-not (Ask "  Install Python 3.12 now (winget, for your user only, about 30 MB)?")) { Fail "Python 3 is required." }
  if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Fail "winget is missing. Install 'App Installer' from the Microsoft Store, or install Python yourself."
  }
  Exec @('winget', 'install', '-e', '--id', 'Python.Python.3.12', '--scope', 'user', '--accept-package-agreements', '--accept-source-agreements') | Out-Null
  Refresh-Path
  $pyargs = Find-Python
  if (-not $pyargs) { Fail "Python installed, but it can't be found. Install Python 3.12 from python.org yourself." }
}
Say "  Python: $($pyargs -join ' ')"

if ((Exec ($pyargs + @('-c', 'import pefile, capstone'))) -ne 0) {
  Say "  The Python packages pefile and capstone are missing (about 20 MB)."
  if (-not (Ask "  Install them now (pip, for your user only)?")) { Fail "pefile and capstone are required." }
  Run "Installing pefile and capstone" ($pyargs + @('-m', 'pip', 'install', '--user', 'pefile', 'capstone'))
}

if (-not (Test-Path (Join-Path $Toolkit 'tools\lift\lift32.py'))) {
  Say "  The pcrecomp toolkit is not beside this folder ($Toolkit)."
  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    if (-not (Ask "  git is needed to fetch it. Install Git for Windows now (winget, about 60 MB)?")) { Fail "git is needed to fetch pcrecomp." }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { Fail "winget is missing. Install Git for Windows yourself." }
    Exec @('winget', 'install', '-e', '--id', 'Git.Git', '--accept-package-agreements', '--accept-source-agreements') | Out-Null
    Refresh-Path
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Fail "Git did not install. Install Git for Windows yourself." }
  }
  if (-not (Ask "  Download it now (git, about 20 MB)?")) { Fail "pcrecomp is required at $Toolkit." }
  Run "Cloning pcrecomp" @('git', 'clone', '--depth', '1', 'https://github.com/sp00nznet/pcrecomp', $Toolkit)
}
Say "  pcrecomp: $Toolkit"

# Visual Studio 2022 or its Build Tools, with the C++ x86 compiler; CMake and
# Ninja ship inside that workload, so build.cmd needs nothing else.
function Find-VS {
  foreach ($p in @("${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe",
                   "$env:ProgramFiles\Microsoft Visual Studio\Installer\vswhere.exe")) {
    if (Test-Path $p) {
      $vs = & $p -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
      if ($vs) { return $vs }
    }
  }
  foreach ($d in (Get-ChildItem "$env:ProgramFiles\Microsoft Visual Studio\2022", "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022" -Directory -ErrorAction SilentlyContinue)) {
    if (Test-Path "$($d.FullName)\VC\Auxiliary\Build\vcvarsall.bat") { return $d.FullName }
  }
  return $null
}
if (-not (Find-VS)) {
  Say "  Visual Studio 2022 with the C++ tools is not installed. The recompiled game is C, and this is the compiler."
  if (-not (Ask "  Install the Visual Studio 2022 Build Tools with the C++ workload now (winget, about 3 GB)?")) { Fail "a C compiler (Visual Studio 2022 C++) is required." }
  if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { Fail "winget is missing. Install Visual Studio 2022 Build Tools with 'Desktop development with C++' yourself." }
  Exec @('winget', 'install', '-e', '--id', 'Microsoft.VisualStudio.2022.BuildTools', '--accept-package-agreements', '--accept-source-agreements',
         '--override', '--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended') | Out-Null
  if (-not (Find-VS)) { Fail "the Build Tools did not install. Install Visual Studio 2022 with 'Desktop development with C++' yourself." }
}
Say "  C compiler: $(Find-VS)"

# ---------------------------------------------------------------- the program
Step 2 "Copying your Periodic Table 2002 into game\ and work\"
# The program, its two controls (PowerButton, activelock) and the two
# Microsoft VB6 controls it uses (comdlg32, msinet). The .msi carries all of
# them; an installed copy has them in Common Files and the system folder.
$ocx = @('PowerButton.ocx', 'activelock1884.ocx', 'comdlg32.ocx', 'msinet.ocx')
if ((Test-Path 'game\Periodic_Table_2002.exe') -and (Test-Path 'work\Periodic_Table_2002.exe') -and -not $Force) {
  Say "  Already there (skipping)."
} else {
  $Game = $Game.Trim('"', ' ')
  if (-not $Game) {
    foreach ($d in @((Join-Path $Root 'Periodic Table 2002.msi'), "${env:ProgramFiles(x86)}\Periodic Table 2002", "$env:ProgramFiles\Periodic Table 2002")) {
      if (Test-Path $d) { $Game = $d; Say "  Found $Game"; break }
    }
  }
  if (-not $Game -and $Yes) { Fail "Periodic Table 2002 wasn't found. Give its 'Periodic Table 2002.msi' or its folder with -GameDir." }
  while (-not $Game) {
    $Game = (Read-Host "  Where is 'Periodic Table 2002.msi' (or the folder it installed to)?").Trim('"', ' ')
  }
  if (-not (Test-Path $Game)) { Fail "there is no $Game." }
  New-Item -ItemType Directory -Force 'game', 'work' | Out-Null
  $from = @()
  if ($Game -match '\.msi$') {
    # An administrative install unpacks the files and installs nothing.
    $tmp = Join-Path $env:TEMP "pt2002-msi-$PID"
    Run "Unpacking the .msi" @('msiexec', '/a', (Resolve-Path $Game).Path, '/qn', "TARGETDIR=$tmp")
    $from = @($tmp)
  } else {
    if (Test-Path $Game -PathType Leaf) { $Game = Split-Path -Parent $Game }
    $from = @($Game, "${env:CommonProgramFiles(x86)}", "$env:CommonProgramFiles", "$env:WINDIR\SysWOW64", "$env:WINDIR\System32")
  }
  $exe = Get-ChildItem $from[0] -Recurse -Include 'Periodic Table 2002.exe', 'Periodic_Table_2002.exe' | Select-Object -First 1
  if (-not $exe) { Fail "there is no Periodic Table 2002.exe in $Game." }
  Copy-Item $exe.FullName 'game\Periodic_Table_2002.exe' -Force
  foreach ($o in $ocx) {
    $f = $null
    foreach ($d in $from) { if (-not $f -and (Test-Path $d)) { $f = Get-ChildItem $d -Recurse -Filter $o -ErrorAction SilentlyContinue | Select-Object -First 1 } }
    if (-not $f) { Fail "$o was not found. Give the .msi instead, which carries every control." }
    Copy-Item $f.FullName (Join-Path 'game' $o) -Force
  }
  if ($Game -match '\.msi$') { Remove-Item -Recurse -Force $from[0] }
  Copy-Item 'game\Periodic_Table_2002.exe' 'work\Periodic_Table_2002.exe' -Force
  Say "  Copied to game\ and work\."
}

Step 3 "Writing the controls' manifest"
# Nothing is registered: a manifest beside the exe names every control class
# (tools/make_manifest.py), for the original and the recomp alike.
if ((Test-Path 'game\Periodic_Table_2002.exe.manifest') -and -not $Force) { Say "  Already there (skipping)." }
else { Run "Writing it" ($pyargs + @('-I', 'tools\make_manifest.py', 'game')) }

# ---------------------------------------------------------------- catalog
Step 4 "Finding every function (under a minute)"
if ((Test-Path 'work\functions.json') -and -not $Force) { Say "  Already done (skipping)." }
else { Run "Disassembling Periodic_Table_2002.exe" ($pyargs + @((Join-Path $Toolkit 'tools\disasm\disasm32.py'), 'work\Periodic_Table_2002.exe', '-o', 'work\functions.json')) }

# ---------------------------------------------------------------- lift
Step 5 "Recompiling Periodic_Table_2002.exe to C (under a minute)"
if ((Test-Path 'src\recomp\gen\recomp_dispatch.c') -and -not $Force) { Say "  Already done (skipping)." }
else { Run "Lifting" ($pyargs + @('run_lift.py')) }

# ---------------------------------------------------------------- build
Step 6 "Building build\periodictablerecomp.exe (a minute or two)"
if ((Test-Path 'build\periodictablerecomp.exe') -and -not $Force) { Say "  Already built (skipping)." }
else {
  $env:CMAKE_ARGS = "-DPCRECOMP=$($Toolkit -replace '\\', '/')"
  Run "Compiling" @('cmd', '/d', '/c', "`"$Root\build.cmd`"")
}

# ---------------------------------------------------------------- shortcut
Step 7 "Making the shortcut"
$lnk = Join-Path $Root 'Periodic Table 2002.lnk'
$sh = New-Object -ComObject WScript.Shell
$s = $sh.CreateShortcut($lnk)
$s.TargetPath = Join-Path $Root 'build\periodictablerecomp.exe'
$s.Arguments = '--run'
$s.WorkingDirectory = $Root
$s.IconLocation = (Join-Path $Root 'game\Periodic_Table_2002.exe') + ',0'
$s.Save()
Say "  $lnk"

if (-not (Test-Path $lnk)) { Fail "the shortcut was not made." }
Write-Host ""
Say "Done. Double-click 'Periodic Table 2002' in this folder to run it." 'Green'
Pause-End
exit 0
