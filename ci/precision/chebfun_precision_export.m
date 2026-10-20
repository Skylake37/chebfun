function chebfun_precision_export()
% Actual original Chebfun calculations on MATLAB, exported at 17 digits.
% Physical (unweighted) quadrature: LG/LGR/LGL/Fejer-I/Clenshaw-Curtis.
root = pwd;
outdir = fullfile(root, 'precision_results');
if ~exist(outdir, 'dir')
    mkdir(outdir);
end
meta = fopen(fullfile(outdir, 'matlab_environment.txt'), 'w');
assert(meta > 0);
fprintf(meta, 'MATLAB_VERSION=%s\n', version);
fprintf(meta, 'MATLAB_RELEASE=%s\n', version('-release'));
for name = {'legpts', 'chebpts', 'legpoly'}
    functionName = name{1};
    functionPath = which(functionName);
    assert(startsWith(functionPath, [root filesep], 'IgnoreCase', true));
    relativePath = strrep(functionPath(numel(root)+2:end), filesep, '/');
    fprintf(meta, 'CHEBFUN_%s=%s\n', upper(functionName), relativePath);
end
fclose(meta);

families = {'LG','LGRminus','LGRplus','LGL','CG','CGL'};
for g = 1:numel(families)
    family = families{g};
    if strcmp(family, 'CG') || strcmp(family, 'CGL')
        ns = [9, 17, 33, 65, 129, 257];
    else
        ns = [8, 16, 32, 64, 96, 128];
    end
    for n = ns
        switch family
            case 'LG'
                [x, w] = legpts(n);
            case 'LGRminus'
                [x, w] = radaupts(n);
            case 'LGRplus'
                [x, w] = radaupts(n);
                x = -flipud(x(:));
                w = flipud(w(:));
            case 'LGL'
                [x, w] = lobpts(n);
            case 'CG'
                [x, w] = chebpts(n, 1);
            case 'CGL'
                [x, w] = chebpts(n, 2);
        end
        x = x(:);
        w = w(:);
        assert(numel(x) == n && numel(w) == n);
        assert(all(isfinite(x)) && all(isfinite(w)) && all(w > 0));
        assert(all(diff(x) > 0));
        assert(abs(sum(w)-2) < 5e-11);
        filename = fullfile(outdir, sprintf('%s_n%d.csv', family, n));
        fid = fopen(filename, 'w');
        assert(fid > 0);
        fprintf(fid, 'x,w\n');
        fprintf(fid, '%.17g,%.17g\n', [x.'; w.']);
        fclose(fid);
        fprintf('EXPORTED %s n=%d; sum(w)-2=%.4e\n', family, n, sum(w)-2);
    end
end

sample_x = [-0.99, -0.81, -0.50, -0.13, 0.0, 0.23, 0.75, 0.99].';
fid = fopen(fullfile(outdir, 'polynomial_values.csv'), 'w');
assert(fid > 0);
fprintf(fid, 'family,degree,x,value\n');
for degree = [8, 32, 64, 128]
    lp = legpoly(degree);
    cp = chebpoly(degree);
    lv = feval(lp, sample_x);
    cv = feval(cp, sample_x);
    assert(all(isfinite(lv(:))) && all(isfinite(cv(:))));
    for k = 1:numel(sample_x)
        fprintf(fid, 'Legendre,%d,%.17g,%.17g\n', degree, sample_x(k), lv(k));
        fprintf(fid, 'Chebyshev,%d,%.17g,%.17g\n', degree, sample_x(k), cv(k));
    end
end
fclose(fid);
fprintf('CHEBFUN_MATLAB_EXPORT_COMPLETE\n');
end
