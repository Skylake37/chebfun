# Python calls MATLAB Chebfun on a Windows self-hosted GitHub runner

The GitHub workflow **Python calls MATLAB Chebfun (Engine)** runs on your
own licensed Windows PC. It calls actual Chebfun `classdef` methods from
Python, converts MATLAB arrays to NumPy, verifies results, and uploads JSON.

## Register your Windows computer

1. Open [this repository's Actions runners settings](https://github.com/Skylake37/chebfun/settings/actions/runners)
   and choose **New self-hosted runner** -> **Windows** -> **x64**.
2. In PowerShell, follow the download/extract instructions shown by GitHub.
   Register using the short-lived token shown there:
   ```powershell
   .\config.cmd --url https://github.com/Skylake37/chebfun `
     --token <TOKEN_FROM_GITHUB> `
     --labels matlab-engine
   ```
3. For an initial run, decline Windows service installation and start the
   runner interactively, under the Windows account with the MATLAB license:
   ```powershell
   .\run.cmd
   ```
4. From the repository's **Actions** tab, select
   **Python calls MATLAB Chebfun (Engine)** -> **Run workflow** and choose the
   installed MATLAB release, **R2026a** (default) or **R2026b**.

The job selects the custom labels
`[self-hosted, windows, x64, matlab-engine]`. The runner needs Git,
PowerShell, network access to GitHub and the Python package index, and a
licensed MATLAB installation in the standard location:
`C:\Program Files\MATLAB\R2026a` or `R2026b`.

It uses `actions/setup-python` to provision Python 3.13 and installs the
matching MATLAB Engine package from
`<matlabroot>\extern\engines\python`. This avoids accidentally installing
a PyPI Engine package targeting a different MATLAB release.

## Run the same example directly from PowerShell

From the repository root, with Python 3.13 installed:

```powershell
$env:MATLAB_RELEASE = 'R2026a'  # Change to R2026b when installed
$matlabRoot = Join-Path $env:ProgramFiles "MATLAB\$env:MATLAB_RELEASE"
python -m pip install numpy==2.3.5
python -m pip install (Join-Path $matlabRoot 'extern\engines\python')
python ci/python_engine/chebfun_engine_demo.py
```

## Chebfun classdef resolution

The repository root, containing `@chebfun/chebfun.m`, is added to the MATLAB
path. MATLAB resolves `@class` and `+package` folders automatically;
avoid adding each class/package directory separately using `genpath`.

The Python code keeps `chebfun` objects in the MATLAB engine workspace,
calls `feval(f, ...)`, `diff(f)`, `roots(f)` and `sum(f)` via `eng.eval`,
and calls the ordinary Chebfun function `chebpts` through
`eng.feval("chebpts", ...)`. The results become NumPy arrays via
`tomemoryview()`. To call another Chebfun function or class method, replace
the MATLAB expression and convert its numerical output the same way.

Results are stored in `python_engine_results/results.json` and uploaded by
the workflow.

## Licensing and permissions

GitHub-hosted MATLAB public-project licensing and MATLAB batch licensing
tokens do not support the MATLAB Engine API for Python. This workflow runs
against your local MATLAB license via the Windows self-hosted runner.

Self-hosted runners execute code from the repository with the runner
account's operating-system privileges. Use `workflow_dispatch` and grant
workflow write access only to trusted collaborators, especially for public
repositories.
