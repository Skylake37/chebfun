#!/usr/bin/env python3
"""Call real Chebfun classdef code from Python and consume NumPy results."""

import json
import os
from pathlib import Path

import matlab
import matlab.engine
import numpy as np


def as_numpy(value):
    """Copy a MATLAB numeric array to an independent NumPy array."""
    return np.array(value.tomemoryview(), copy=True).reshape(-1)


def main():
    # Chebfun's parent directory belongs on the MATLAB path. Do not genpath()
    # the @class, +package, or private subdirectories separately.
    root = Path(os.environ.get("GITHUB_WORKSPACE", Path(__file__).resolve().parents[2])).resolve()
    eng = matlab.engine.start_matlab("-nodisplay")
    try:
        assert eng.version("-release") == "2026b"
        eng.addpath(str(root), nargout=0)
        resolved = eng.which("chebfun")
        print("Chebfun constructor:", resolved)
        assert resolved and str(root) in resolved

        # chebfun is a MATLAB classdef value class. Keep its instances inside
        # MATLAB; Python receives the outputs of MATLAB method invocations.
        eng.eval("x = chebfun('x'); f = x.^2 - 0.25; df = diff(f);", nargout=0)
        assert eng.eval("isa(f, 'chebfun')")
        assert eng.eval("isa(df, 'chebfun')")

        # Python -> MATLAB: send sample points through the engine workspace.
        points = np.linspace(-1.0, 1.0, 9)
        eng.workspace["sample_points"] = matlab.double(points.reshape(-1, 1).tolist())

        # MATLAB -> Python: call overloaded class methods; convert numeric outputs.
        values = as_numpy(eng.eval("feval(f, sample_points)"))
        derivatives = as_numpy(eng.eval("feval(df, sample_points)"))
        zeros = np.sort(as_numpy(eng.eval("roots(f)")))
        integral = float(eng.eval("sum(f)"))

        # A standard Chebfun function can be called directly by name as well.
        nodes = as_numpy(eng.feval("chebpts", 9.0, nargout=1))

        np.testing.assert_allclose(values, points**2 - 0.25, rtol=0, atol=1e-11)
        np.testing.assert_allclose(derivatives, 2 * points, rtol=0, atol=1e-11)
        np.testing.assert_allclose(zeros, [-0.5, 0.5], rtol=0, atol=1e-11)
        np.testing.assert_allclose(integral, 1.0 / 6.0, rtol=0, atol=1e-11)
        np.testing.assert_allclose(
            nodes, np.polynomial.chebyshev.chebpts2(9), rtol=0, atol=1e-11
        )

        result = {
            "matlab_release": eng.version("-release"),
            "chebfun_class": eng.eval("class(f)"),
            "chebfun_constructor": resolved,
            "sample_points": points.tolist(),
            "function_values": values.tolist(),
            "derivative_values": derivatives.tolist(),
            "roots": zeros.tolist(),
            "integral": integral,
            "chebyshev_points": nodes.tolist(),
        }
        outdir = root / "python_engine_results"
        outdir.mkdir(exist_ok=True)
        (outdir / "results.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, indent=2))
        print("PYTHON_CHEBFUN_ENGINE_PASS")
    finally:
        eng.quit()


if __name__ == "__main__":
    main()
