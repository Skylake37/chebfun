#!/usr/bin/env python3
"""Compare original MATLAB/Chebfun output with NumPy against 80-digit references.

All CSV input comes from chebfun_precision_export.m running in MATLAB.
Chebyshev quadrature uses physical (unweighted) Fejer-I / Clenshaw-Curtis weights.
"""
import csv
import math
from pathlib import Path

import mpmath as mp
import numpy as np
from numpy.polynomial import chebyshev as C
from numpy.polynomial import legendre as L

mp.mp.dps = 80
OUT = Path("precision_results")
GRIDS = ("LG", "LGRminus", "LGRplus", "LGL", "CG", "CGL")


def moment(k):
    return mp.mpf(2) / (1 - k*k) if k % 2 == 0 else mp.mpf(0)


def legendre_prime(m, z):
    return m * (mp.legendre(m-1, z) - z*mp.legendre(m, z)) / (1-z*z)


def refine_legendre_root(family, n, index, initial):
    if family in ("LGRminus", "LGL") and index == 0:
        return mp.mpf(-1)
    if family in ("LGRplus", "LGL") and index == n-1:
        return mp.mpf(1)
    if family == "LG":
        fn = lambda z: mp.legendre(n, z)
    elif family in ("LGRminus", "LGRplus"):
        # Left Radau interior: P_(n-1)+P_n=0. Right Radau: P_(n-1)-P_n=0.
        fn = (lambda z: mp.legendre(n-1, z)+mp.legendre(n,z)) if family == "LGRminus" else (lambda z: mp.legendre(n-1,z)-mp.legendre(n,z))
    else:
        fn = lambda z: legendre_prime(n-1, z)
    z = mp.findroot(fn, mp.mpf(float(initial)), solver="newton", tol=mp.mpf("1e-68"), verify=True)
    if abs(fn(z)) > mp.mpf("1e-62"):
        raise ArithmeticError(f"Reference root residual too large: {family} n={n} i={index}")
    if abs(z-mp.mpf(float(initial))) > mp.mpf("1e-8"):
        raise ArithmeticError(f"Reference root changed branch: {family} n={n} i={index}")
    return z


def legendre_reference(family, n, seeds):
    xx = [refine_legendre_root(family, n, j, x) for j, x in enumerate(seeds)]
    if family == "LG":
        ww = [2 / ((1-x*x)*legendre_prime(n,x)**2) for x in xx]
    elif family == "LGL":
        ww = [mp.mpf(2)/(n*(n-1)*mp.legendre(n-1,x)**2) for x in xx]
    else:
        ww = []
        for j, x in enumerate(xx):
            if (family == "LGRminus" and j == 0) or (family == "LGRplus" and j == n-1):
                ww.append(mp.mpf(2)/(n*n))
            elif family == "LGRminus":
                ww.append((1-x)/(n*n*mp.legendre(n-1,x)**2))
            else:
                ww.append((1+x)/(n*n*mp.legendre(n-1,x)**2))
    return xx, ww


def chebyshev_reference(family, n):
    xx, ww = [], []
    if family == "CG":
        for j in range(n):
            angle = mp.pi*(2*n-2*j-1)/(2*n)
            xx.append(mp.cos(angle))
            val = moment(0)+2*sum(moment(k)*mp.cos(k*angle) for k in range(2,n,2))
            ww.append(val/n)
    else:
        N = n-1
        for j in range(n):
            angle = mp.pi*(N-j)/N
            xx.append(mp.cos(angle))
            val = moment(0)+(-1)**j*moment(N)
            val += 2*sum(moment(k)*mp.cos(k*angle) for k in range(2,N,2))
            endpoint = mp.mpf("0.5") if j in (0, n-1) else mp.mpf(1)
            ww.append(endpoint*val/N)
    return xx, ww


def read_xy(filename):
    with filename.open(newline="") as f:
        rows = list(csv.DictReader(f))
    x = np.array([float(r["x"]) for r in rows], dtype=np.float64)
    w = np.array([float(r["w"]) for r in rows], dtype=np.float64)
    return x, w


def max_float_error(values, reference, relative=False):
    err = []
    for x, xr in zip(values, reference):
        numerator = abs(mp.mpf(float(x))-xr)
        err.append(float(numerator/abs(xr) if relative else numerator))
    return max(err, default=0.0)


def grid_metrics(family, n, source, x, w, xr, wr):
    assert len(x) == len(w) == len(xr) == len(wr) == n
    assert np.all(np.isfinite(x)) and np.all(np.isfinite(w)) and np.all(w>0)
    assert np.all(np.diff(x)>0)
    assert np.max(np.abs(w.sum()-2)) < 1e-10
    return {
        "grid": family, "n": n, "source": source,
        "node_max_abs_error": max_float_error(x, xr),
        "weight_max_abs_error": max_float_error(w, wr),
        "weight_max_rel_error": max_float_error(w, wr, relative=True),
        "node_antisymmetry_error": float(np.max(np.abs(x+x[::-1]))),
        "weight_sum_error": float(abs(w.sum()-2)),
    }


def write_csv(path, rows, fieldnames=None):
    if not rows:
        return
    with path.open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=fieldnames or list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)


def main():
    summary = []
    by_node = []
    for family in GRIDS:
        files = sorted(OUT.glob(f"{family}_n*.csv"), key=lambda p: int(p.stem.split("_n")[-1]))
        if len(files) != 6:
            raise RuntimeError(f"{family}: expected six real MATLAB exports, found {len(files)}")
        for filename in files:
            n = int(filename.stem.split("_n")[-1])
            x, w = read_xy(filename)
            if family in ("CG", "CGL"):
                xr, wr = chebyshev_reference(family, n)
            else:
                xr, wr = legendre_reference(family, n, x)
            if abs(sum(wr)-2) > mp.mpf("1e-60"):
                raise ArithmeticError(f"Reference quadrature normalization wrong: {family} n={n}")
            mat = grid_metrics(family, n, "MATLAB-Chebfun", x, w, xr, wr)
            summary.append(mat)
            for j in range(n):
                by_node.append({
                    "grid":family, "n":n, "index":j,
                    "matlab_x":f"{x[j]:.17g}", "matlab_w":f"{w[j]:.17g}",
                    "reference_x_35digits":mp.nstr(xr[j],35),
                    "reference_w_35digits":mp.nstr(wr[j],35),
                    "matlab_node_abs_error":f"{float(abs(mp.mpf(float(x[j]))-xr[j])):.9g}",
                    "matlab_weight_rel_error":f"{float(abs(mp.mpf(float(w[j]))-wr[j])/wr[j]):.9g}",
                })
            if family == "LG":
                xn, wn = L.leggauss(n)
                summary.append(grid_metrics(family, n, "NumPy.leggauss", xn, wn, xr, wr))
            elif family == "CG":
                # NumPy chebpts1 supplies nodes, but chebgauss weights integrate
                # f/sqrt(1-x*x), so physical weights must not be compared to them.
                xn = C.chebpts1(n)
                summary.append({
                    "grid":family, "n":n, "source":"NumPy.chebpts1 (nodes only)",
                    "node_max_abs_error":max_float_error(xn,xr),
                    "weight_max_abs_error":"", "weight_max_rel_error":"",
                    "node_antisymmetry_error":float(np.max(np.abs(xn+xn[::-1]))),
                    "weight_sum_error":"",
                })
            elif family == "CGL":
                xn = C.chebpts2(n)
                summary.append({
                    "grid":family, "n":n, "source":"NumPy.chebpts2 (nodes only)",
                    "node_max_abs_error":max_float_error(xn,xr),
                    "weight_max_abs_error":"", "weight_max_rel_error":"",
                    "node_antisymmetry_error":float(np.max(np.abs(xn+xn[::-1]))),
                    "weight_sum_error":"",
                })
            print(f"COMPARED {family:9} n={n:4} Chebfun xerr={mat['node_max_abs_error']:.3e} wrel={mat['weight_max_rel_error']:.3e}", flush=True)
    write_csv(OUT/"grid_summary.csv", summary)
    write_csv(OUT/"chebfun_per_node.csv", by_node)

    poly_rows = []
    with (OUT/"polynomial_values.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            family, n = row["family"], int(row["degree"])
            x, y = float(row["x"]), float(row["value"])
            xx = mp.mpf(float(x))  # same rounded input to both evaluators
            if family == "Legendre":
                yr = mp.legendre(n, xx)
                yn = float(L.legval(x, [0.0]*n + [1.0]))
            else:
                yr = mp.chebyt(n, xx)
                yn = float(C.chebval(x, [0.0]*n + [1.0]))
            poly_rows.append({
                "family":family, "degree":n, "x":f"{x:.17g}",
                "matlab_chebfun_value":f"{y:.17g}", "numpy_value":f"{yn:.17g}",
                "reference_value_35digits":mp.nstr(yr, 35),
                "matlab_abs_error":float(abs(mp.mpf(float(y))-yr)),
                "numpy_abs_error":float(abs(mp.mpf(float(yn))-yr)),
            })
    if len(poly_rows) != 64:
        raise RuntimeError(f"Expected 64 actual MATLAB polynomial evaluations, got {len(poly_rows)}")
    write_csv(OUT/"polynomial_summary.csv", poly_rows)

    with (OUT/"SUMMARY.md").open("w") as f:
        f.write("# Actual MATLAB/Chebfun vs NumPy precision\n\n")
        f.write("80-decimal-digit mpmath reference; IEEE float64 results. Physical unweighted quadrature weights.\n")
        f.write("LGR/LGL have no direct NumPy polynomial API counterparts; only original Chebfun results are shown.\n\n")
        f.write("| Grid | n | Source | max node abs error | max weight rel error | antisymmetry error |\n")
        f.write("|---|---:|---|---:|---:|---:|\n")
        for r in summary:
            f.write(f"| {r['grid']} | {r['n']} | {r['source']} | {r['node_max_abs_error']:.3e} | ")
            werr = r["weight_max_rel_error"]
            f.write((f"{werr:.3e}" if isinstance(werr,float) else "—")+" | ")
            f.write(f"{r['node_antisymmetry_error']:.3e} |\n")
        f.write("\n## Polynomial evaluations\n\n")
        f.write("| Family | degree | MATLAB/Chebfun max abs error | NumPy max abs error |\n")
        f.write("|---|---:|---:|---:|\n")
        for family in ("Legendre","Chebyshev"):
            for n in (8,32,64,128):
                rr = [r for r in poly_rows if r["family"]==family and r["degree"]==n]
                f.write(f"| {family} | {n} | {max(r['matlab_abs_error'] for r in rr):.3e} | {max(r['numpy_abs_error'] for r in rr):.3e} |\n")
    print("COMPARISON_FINISHED:", OUT/"SUMMARY.md", flush=True)


if __name__ == "__main__":
    main()
