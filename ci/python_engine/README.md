# Windows self-hosted GitHub Actions: Python, MATLAB and Chebfun

This fork has two workflows that can run on the same Windows PC using your
installed MATLAB license and **Python 3.11.9**, invoked as `python`.

- [Python calls MATLAB Chebfun (Engine)](../../.github/workflows/chebfun-python-engine.yml)
  constructs Chebfun `classdef` objects, invokes methods from Python and
  converts the numerical results to NumPy.
- [Chebfun vs NumPy precision](../../.github/workflows/chebfun-numpy-precision.yml)
  supports **windows-local** for the same runner, and retains its existing
  GitHub-hosted Ubuntu comparison.

## Register and start your local runner

From [Settings -> Actions -> Runners](https://github.com/Skylake37/chebfun/settings/actions/runners),
add a Windows x64 self-hosted runner. Use GitHub's current download and
registration commands and include the custom label `matlab-engine`:

```powershell
.\config.cmd --url https://github.com/Skylake37/chebfun --token <TOKEN> --labels matlab-engine
.\run.cmd
```

Start `run.cmd` under the Windows user with access to the MATLAB license.
The runner must have Git for Windows, PowerShell 7 (`pwsh`), Python 3.11.9
available as `python`, and MATLAB R2026a installed at
`C:\Program Files\MATLAB\R2026a`. The workflows also permit selecting
R2026b if installed later.

Use the Actions tab's **Run workflow** button to trigger either workflow.
For the precision comparison choose `execution_environment = windows-local`.

## Fast incremental execution

The Windows jobs contain no third-party `uses:` steps. They do not download
`actions/checkout`, `actions/setup-python`, or `actions/upload-artifact`.

They use `GITHUB_WORKSPACE` for a **persistent Git working copy**:

1. First execution: initialize the worktree and fetch the requested commit.
2. Subsequent executions: `git fetch --depth=1` the exact GitHub-triggering
   commit and force-checkout its tracked contents.
3. Reuse your existing `python` interpreter.
4. Check local NumPy (`2.3.5`) and, for the precision workflow, mpmath
   (`1.3.0`); run `python -m pip install` only if necessary.
5. Start the already installed MATLAB on demand.

The Engine job uses R2026a/R2026b's **preinstalled MATLAB Engine for Python**
from `<matlabroot>\extern\engines\python\dist` using `PYTHONPATH`.
No `matlabengine` pip installation is required.

Each job's results stay on the runner under:

- `<GITHUB_WORKSPACE>\python_engine_results\results.json`
- `<GITHUB_WORKSPACE>\precision_results\SUMMARY.md`

A copy is archived by GitHub run ID under
`<GITHUB_WORKSPACE>\_local_results\engine\<run-id>-<attempt>` or
`<GITHUB_WORKSPACE>\_local_results\precision\<run-id>-<attempt>`.
Paths are printed in the job log and summary; **GitHub artifacts are no
longer uploaded**, avoiding another Action download. The initial Git
fetch still needs access to GitHub, and it fetches new commits on reruns.

The working copy is treated as a build checkout: its tracked files are
force-reset to the workflow's commit each run. Keep any local experimental
edits in a separate Git clone.

## Run the Engine demo manually

From the Chebfun repository root in PowerShell:

```powershell
python --version
$env:MATLAB_RELEASE = 'R2026a'
$matlabRoot = Join-Path $env:ProgramFiles 'MATLAB\R2026a'
$env:PYTHONPATH = Join-Path $matlabRoot 'extern\engines\python\dist'
python -m pip install numpy==2.3.5
python ci/python_engine/chebfun_engine_demo.py
```

The Python script adds the repository root to the MATLAB path so the
`@chebfun` class directory resolves normally. It creates the actual
`chebfun` class objects inside the MATLAB engine workspace, uses
`eng.eval(...)` to execute their overloaded `feval`, `diff`, `roots` and
`sum` methods, and calls a standard `chebpts` function with `eng.feval`.
The resulting MATLAB numeric arrays are converted with `tomemoryview()`.

## Security

Self-hosted runners execute repository code with the local Windows user's
permissions. Restrict access to workflow changes and triggers, and prefer
a dedicated low-privilege user or machine for public repositories.
