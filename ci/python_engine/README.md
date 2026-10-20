# Windows self-hosted GitHub Actions: isolated Python + MATLAB + Chebfun

Both Windows self-hosted jobs use the locally licensed MATLAB installation,
the existing **Python 3.11.9** interpreter (invoked with `python`), and
**uv-managed virtual environments**. They never install or uninstall Python
packages in the system/global interpreter.

- [Python calls MATLAB Chebfun (Engine)](../../.github/workflows/chebfun-python-engine.yml)
  constructs Chebfun `classdef` objects and converts MATLAB results to NumPy.
- [Chebfun vs NumPy precision](../../.github/workflows/chebfun-numpy-precision.yml)
  offers `execution_environment = windows-local`; its GitHub-hosted Ubuntu
  job remains unchanged.

## One-time Windows runner prerequisites

Follow the [self-hosted runner setup](https://github.com/Skylake37/chebfun/settings/actions/runners)
for Windows x64 and register it with the custom `matlab-engine` label.
Run `run.cmd` under your normal, MATLAB-licensed Windows account.

Install uv once if it is missing:

```powershell
winget install --id astral-sh.uv -e
uv --version
python --version  # Expected 3.11.9
```

If uv was installed while the runner was already active, **stop and restart
`run.cmd`** so the runner can see the updated PATH. Git for Windows,
PowerShell 7 (`pwsh`), and MATLAB R2026a at
`C:\Program Files\MATLAB\R2026a` must also be available (or choose R2026b
if installed).

## What the workflows do

The jobs do not invoke third-party `uses:` actions, and update the local
Chebfun checkout incrementally with `git fetch`.

Each Windows job creates its own persistent environment in
`GITHUB_WORKSPACE`:

| Workflow | Virtual environment | Packages installed by uv |
| --- | --- | --- |
| Engine | `.venv-chebfun-engine` | `numpy==2.3.5` |
| Precision | `.venv-chebfun-precision` | `numpy==2.3.5`, `mpmath==1.3.0` |

The workflow locates the Python 3.11.9 executable with `python`, then uses:

```powershell
uv venv --no-python-downloads --python $basePython $venv
uv pip install --python $venvPython numpy==2.3.5
& $venvPython ci/python_engine/chebfun_engine_demo.py
```

The `uv venv` step only runs if the environment is missing; repeated
`uv pip install` calls are incremental. The interpreter is verified to be a
virtual environment before installing any dependency.

The local **global NumPy remains untouched** regardless of the version
installed in either virtual environment. It can stay at 2.4.4.

The Engine job loads MATLAB R2026a/R2026b's preinstalled MATLAB Engine from
`<matlabroot>\extern\engines\python\dist` using `PYTHONPATH`, and executes
the demo under `.venv-chebfun-engine\Scripts\python.exe`.

Results are saved locally under `python_engine_results` or
`precision_results` and additionally archived in `_local_results`, with
run-specific subdirectories. GitHub logs show the archive location. GitHub
artifacts are not uploaded by the Windows jobs.

## Run the Engine demo manually without modifying global Python

From the Chebfun repository root:

```powershell
$env:MATLAB_RELEASE = 'R2026a'
$matlabRoot = Join-Path $env:ProgramFiles 'MATLAB\R2026a'
$env:PYTHONPATH = Join-Path $matlabRoot 'extern\engines\python\dist'
$basePython = (python -c "import sys; print(sys.executable)").Trim()
$venv = Join-Path (Get-Location) '.venv-chebfun-engine'
$venvPython = Join-Path $venv 'Scripts\python.exe'
uv venv --no-python-downloads --python $basePython $venv
uv pip install --python $venvPython numpy==2.3.5
& $venvPython ci/python_engine/chebfun_engine_demo.py
```

To restore an earlier global NumPy version after a run of the **old**
workflow, perform this **manual, explicit** operation only if you intend to
restore the base interpreter:

```powershell
python -m pip install numpy==2.4.4
```

None of the revised Windows workflow steps execute that command.

## Security

A self-hosted runner executes code with the Windows user's permissions.
Restrict workflow changes/triggers and use a dedicated low-privilege runner
account or isolated machine for public repositories.
