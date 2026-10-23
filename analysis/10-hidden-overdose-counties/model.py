"""County overdose model: Poisson counts with an interval-censored likelihood and a spatial CAR prior.

  y_i ~ Poisson(mu_i)                     published counts (zero or 10+)
  P(1 <= y_i <= hi_i | mu_i)              suppressed counts (hi = 9)
  log mu_i = log(pop_i / 1e5) + a + X_i b + u_state(i) + e_i
  e ~ Normal(0, sigma^2 [(1 - rho) I + rho Q]^-1)     Leroux CAR on the county adjacency graph (Q = Laplacian)

rho = 0 is independent county noise, rho = 1 is the fully smooth ICAR field. We use the Leroux form
instead of BYM2 because its precision matrix is well conditioned: NUTS needs about 200 steps per
iteration where BYM2 on 3,144 counties hit the 1,023-step cap and did not converge in our runs.
Optionally, for states where the published state total minus the published county counts is plausible,
that residual is a soft constraint on the sum of the suppressed counts.
"""
import os

os.environ.setdefault("XLA_FLAGS", "--xla_force_host_platform_device_count=4")
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import jax
import jax.numpy as jnp
import numpy as np
import numpyro
import numpyro.distributions as dist
import scipy.sparse as sp
from jax.scipy.special import gammaln, logsumexp
from numpyro.infer import MCMC, NUTS
from scipy.sparse.csgraph import connected_components

jax.config.update("jax_enable_x64", True)
numpyro.set_host_device_count(4)

URBAN_LEVELS = [2, 3, 4, 5, 6]  # NCHS 2013 codes; 1 (large central metro) is the reference
REL_TOL = 0.05  # slack for state-total vs county-count mismatch (cause unconfirmed), share of the state total


def standardize(t):
    """Covariate matrix for all counties; missing values take the state median, then the national median."""
    cols = {}
    cols["log_density"] = np.log(t["pop"] / t.land_sqmi.clip(lower=1))
    for c in ["pct_uninsured", "pct_low_income"]:
        x = t[c].copy()
        x = x.fillna(x.groupby(t.state).transform("median")).fillna(x.median())
        cols[c] = x
    X = np.column_stack(list(cols.values()))
    X = (X - X.mean(0)) / X.std(0)
    dummies = np.column_stack([(t.urban_rural == k).astype(float) for k in URBAN_LEVELS])
    names = list(cols) + [f"urban_rural_{k}" for k in URBAN_LEVELS]
    return np.column_stack([X, dummies]), names


def laplacian_eigenvalues(edges, n):
    """Eigenvalues of the graph Laplacian (block-diagonal over connected components)."""
    A = sp.coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])), shape=(n, n))
    A = (A + A.T).tocsr()
    ncomp, comp = connected_components(A, directed=False)
    eig = []
    for c in range(ncomp):
        idx = np.where(comp == c)[0]
        Ac = A[idx][:, idx].toarray()
        eig.append(np.linalg.eigvalsh(np.diag(Ac.sum(1)) - Ac))
    return np.clip(np.concatenate(eig), 0, None)


def prepare(t, edges, status, hi, state_totals=None, constrain=False, pending=False):
    """Pack a county table into the arrays the model needs.

    status: array of 'exact' | 'censored' | 'missing'; hi: upper bound for censored cells.
    """
    n = len(t)
    X, names = standardize(t)
    states = sorted(t.state.unique())
    sidx = np.array([states.index(s) for s in t.state])
    offset = np.log(t["pop"].values / 1e5)
    if pending:
        offset = offset + np.log(1 - t.pct_pending.values / 100)
    exact = status == "exact"
    cens = status == "censored"
    d = dict(n=n, X=X, names=names, states=states, sidx=sidx, edges=edges, offset=offset,
             lap_eig=laplacian_eigenvalues(edges, n),
             exact=np.where(exact)[0], y_exact=t.y.values[exact].astype(float),
             cens=np.where(cens)[0], hi_cens=np.asarray(hi)[cens].astype(int))
    d["kmax"] = int(d["hi_cens"].max())
    # State sum constraint: residual = state total - published county counts (exact cells only).
    d["con_state"] = np.array([], dtype=int)
    if constrain:
        pub = t[exact].groupby("state").y.sum()
        nsup = pd_count(t, cens)
        hisum = t[cens].assign(hi=np.asarray(hi)[cens]).groupby("state").hi.sum()
        dq = pd_count(t, status == "missing")
        rows = []
        for s in states:
            if s not in state_totals.index or dq.get(s, 0) > 0 or nsup.get(s, 0) == 0:
                continue
            resid = state_totals[s] - pub.get(s, 0.0)
            if nsup[s] <= resid <= hisum[s]:  # inside the logical bounds
                rows.append((states.index(s), resid, REL_TOL * state_totals[s]))
        if rows:
            r = np.array(rows)
            d["con_state"], d["con_resid"], d["con_sd"] = r[:, 0].astype(int), r[:, 1], r[:, 2]
            d["cens_state_pos"] = sidx[d["cens"]]
    return d


def pd_count(t, mask):
    return t[mask].groupby("state").size()


def _trunc_moments(mu, hi, kmax):
    """Mean and variance of Poisson(mu) truncated to 1..hi, and log P(1 <= Y <= hi), for each cell."""
    k = jnp.arange(1, kmax + 1)[None, :]
    lw = k * jnp.log(mu)[:, None] - mu[:, None] - gammaln(k + 1.0)
    lw = jnp.where(k <= hi[:, None], lw, -jnp.inf)
    lp = logsumexp(lw, axis=1)
    p = jnp.exp(lw - lp[:, None])
    m = (p * k).sum(1)
    v = (p * k ** 2).sum(1) - m ** 2
    return lp, m, v


def model(d, use_covariates=True, use_spatial=True):
    X = jnp.asarray(d["X"])
    n, ns = d["n"], len(d["states"])
    a = numpyro.sample("a", dist.Normal(3.0, 2.0))
    eta = a + jnp.zeros(n)
    if use_covariates:
        b = numpyro.sample("b", dist.Normal(0, 1).expand([X.shape[1]]))
        eta = eta + X @ b
    tau = numpyro.sample("tau_state", dist.HalfNormal(0.5))
    z = numpyro.sample("z_state", dist.Normal(0, 1).expand([ns]))
    eta = eta + (tau * z)[d["sidx"]]
    sigma = numpyro.sample("sigma", dist.HalfNormal(1.0))
    if use_spatial:
        rho = numpyro.sample("rho", dist.Beta(1.0, 1.0))
        eff = numpyro.sample("eff", dist.ImproperUniform(dist.constraints.real, (), (n,)))
        e = jnp.asarray(d["edges"])
        quad = (1 - rho) * (eff ** 2).sum() + rho * ((eff[e[:, 0]] - eff[e[:, 1]]) ** 2).sum()
        logdet = jnp.log(rho * jnp.asarray(d["lap_eig"]) + 1 - rho).sum()
        numpyro.factor("leroux", -n * jnp.log(sigma) + 0.5 * logdet - 0.5 * quad / sigma ** 2)
    else:
        eff = numpyro.sample("eff", dist.Normal(0, sigma).expand([n]))
    eta = eta + eff
    numpyro.deterministic("eta", eta)
    log_mu = eta + jnp.asarray(d["offset"])
    mu = jnp.exp(log_mu)
    ex = d["exact"]
    y = jnp.asarray(d["y_exact"])
    numpyro.factor("ll_exact", (y * log_mu[ex] - mu[ex] - gammaln(y + 1)).sum())
    ce = d["cens"]
    lp, m, v = _trunc_moments(mu[ce], jnp.asarray(d["hi_cens"]), d["kmax"])
    numpyro.factor("ll_cens", lp.sum())
    if len(d["con_state"]):
        ms = jax.ops.segment_sum(m, jnp.asarray(d["cens_state_pos"]), num_segments=ns)[d["con_state"]]
        vs = jax.ops.segment_sum(v, jnp.asarray(d["cens_state_pos"]), num_segments=ns)[d["con_state"]]
        sd = jnp.sqrt(vs + jnp.asarray(d["con_sd"]) ** 2)
        numpyro.factor("state_sum", dist.Normal(ms, sd).log_prob(jnp.asarray(d["con_resid"])).sum())


def fit(d, num_warmup=1000, num_samples=1000, chains=4, seed=0, max_depth=10, **kw):
    """Run NUTS; returns eta draws (draws x counties), hyperparameter draws and sampler diagnostics."""
    kernel = NUTS(lambda: model(d, **kw), target_accept_prob=0.9, max_tree_depth=max_depth)
    mcmc = MCMC(kernel, num_warmup=num_warmup, num_samples=num_samples, num_chains=chains,
                chain_method="parallel", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging", "num_steps"))
    by_chain = mcmc.get_samples(group_by_chain=True)
    keep = [k for k in ("a", "b", "tau_state", "sigma", "rho", "eta") if k in by_chain]
    g = numpyro.diagnostics.summary({k: by_chain[k] for k in keep}, prob=0.9, group_by_chain=True)
    hyper = [k for k in keep if k != "eta"]
    ex = mcmc.get_extra_fields()
    flat = {k: np.asarray(v).reshape((-1,) + np.asarray(v).shape[2:]) for k, v in by_chain.items() if k in keep}
    return dict(eta=flat["eta"], params={k: flat[k] for k in hyper}, names=d["names"],
                divergences=int(np.asarray(ex["diverging"]).sum()),
                mean_steps=float(np.asarray(ex["num_steps"]).mean()),
                hyper_rhat_max=float(max(np.max(g[k]["r_hat"]) for k in hyper)),
                hyper_ess_min=float(min(np.min(g[k]["n_eff"]) for k in hyper)),
                eta_rhat_max=float(np.max(g["eta"]["r_hat"])),
                eta_rhat_gt_1p05=int((g["eta"]["r_hat"] > 1.05).sum()),
                eta_ess_min=float(np.min(g["eta"]["n_eff"])))
