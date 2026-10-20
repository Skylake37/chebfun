# Python calls MATLAB Chebfun

This example starts MATLAB from Python using the MATLAB Engine API, adds the
checked-out Chebfun root to the MATLAB path, constructs actual `chebfun`
`classdef` objects, invokes their methods, and checks NumPy arrays returned
to Python. It also invokes the regular Chebfun function `chebpts` via
`eng.feval`.

## GitHub Actions

Run **Python calls MATLAB Chebfun (Engine)** from the Actions tab using
**Run workflow**.

The workflow deliberately targets a **self-hosted Linux runner** with the
labels `self-hosted`, `linux`, and `matlab-r2026b`. That runner must have:

- An **independently licensed MATLAB R2026b** installation, available at
  `/usr/local/MATLAB/R2026b` (adjust the workflow's `MATLAB_ROOT` if needed).
- A license usable for MATLAB Engine for Python by the runner service account.
- The standard dependencies needed to run MATLAB and GitHub Actions.

The job installs Python 3.13, NumPy, and the matching R2026b Python
`matlabengine` package, verifies the MATLAB release, and runs the example.
The resulting `python_engine_results/results.json` is uploaded as an artifact.

**Licensing:** MathWorks' public-project GitHub-hosted MATLAB license and
MATLAB batch licensing tokens do not support external-language interfaces,
including the MATLAB Engine API. Therefore `ubuntu-latest` together with
`matlab-actions/setup-matlab` cannot execute this direct Python-to-MATLAB
Engine test under those licenses. Installing a MATLAB release through the
setup action does not itself grant an Engine-compatible license.

## Run locally

With MATLAB R2026b installed and licensed, and a compatible Python
environment:

```bash
python -m pip install numpy==2.3.5 matlabengine==26.2.5
python ci/python_engine/chebfun_engine_demo.py
```

The script locates the repository relative to its own path, so it can be
executed from any working directory. On GitHub Actions it uses
`GITHUB_WORKSPACE`.

## Working with `classdef` methods

Chebfun defines `classdef chebfun` in `@chebfun/chebfun.m`.
Adding **the repository root alone** to the MATLAB path enables MATLAB's
normal `@class` and `+package` method resolution.

The Python code leaves the Chebfun objects `f` and `df` in the MATLAB
engine workspace, then calls arbitrary MATLAB/Chebfun expressions through
`eng.eval(...)`. Ordinary functions can also be invoked directly with
`eng.feval("function_name", ...)`. For example, replace `roots(f)` or
`sum(f)` with other Chebfun functions or overloaded methods. Return numeric
results from the MATLAB expression, then convert them to NumPy using
`tomemoryview()`.

The example verifies function values, the derivative, the integral, two
roots, and Chebyshev points against independent NumPy calculations.
