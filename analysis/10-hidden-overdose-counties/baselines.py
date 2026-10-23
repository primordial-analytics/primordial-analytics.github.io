"""Baselines the spatial model has to beat.

nb_fit:        non-spatial Poisson-gamma model. Counts are negative binomial with a state-specific rate
               (shrunk toward the national rate) and one shared overdispersion. Same censored likelihood.
residual_split: the common shortcut. State total minus published counts, split over the hidden
               counties by population, clipped to the hidden range.
"""
import numpy as np
import jax
import jax.numpy as jnp
from jax.scipy.special import gammaln, logsumexp
from scipy.optimize import minimize

jax.config.update("jax_enable_x64", True)


def _nb_logpmf(k, m, alpha):
    p = alpha / (alpha + m)
    return gammaln(k + alpha) - gammaln(alpha) - gammaln(k + 1.0) + alpha * jnp.log(p) + k * jnp.log1p(-p)


def nb_fit(pop, state_idx, nstates, ex, y_ex, ce, hi_ce):
    """Penalized maximum likelihood. Returns a function mapping county index -> NB mean."""
    pop100k = jnp.asarray(pop / 1e5)
    kmax = int(hi_ce.max())
    ks = jnp.arange(1, kmax + 1)[None, :]
    keep = ks <= jnp.asarray(hi_ce)[:, None]
    y = jnp.asarray(y_ex)

    def nll(theta):
        mu0, ls, la = theta[0], theta[1], theta[2]
        log_r = mu0 + jnp.exp(ls) * theta[3:]            # state log rates, shrunk toward mu0
        alpha = jnp.exp(la)
        m = jnp.exp(log_r)[state_idx] * pop100k
        ll = _nb_logpmf(y, m[ex], alpha).sum()
        lw = jnp.where(keep, _nb_logpmf(ks, m[ce][:, None], alpha), -jnp.inf)
        ll += logsumexp(lw, axis=1).sum()
        prior = 0.5 * (theta[3:] ** 2).sum() + 0.5 * ((ls + 1.0) / 1.0) ** 2 + 0.5 * (la / 3.0) ** 2
        return -(ll) + prior

    f = jax.jit(jax.value_and_grad(nll))
    x0 = np.zeros(3 + nstates)
    x0[0] = 3.0
    res = minimize(lambda x: tuple(np.asarray(v) for v in f(jnp.asarray(x))), x0, jac=True, method="L-BFGS-B")
    th = res.x
    alpha = float(np.exp(th[2]))
    mean = np.exp(th[0] + np.exp(th[1]) * th[3:])[state_idx] * pop / 1e5
    return mean, alpha


def nb_trunc_pmf(mean, alpha, hi):
    """pmf over k = 1..max(hi) of an NB(mean, alpha) truncated to 1..hi, one row per county."""
    kmax = int(hi.max())
    ks = np.arange(1, kmax + 1)[None, :]
    lp = np.asarray(_nb_logpmf(jnp.asarray(ks), jnp.asarray(mean)[:, None], alpha))
    lp = np.where(ks <= hi[:, None], lp, -np.inf)
    lp -= lp.max(1, keepdims=True)
    p = np.exp(lp)
    return p / p.sum(1, keepdims=True)


def residual_split(t, status, hi, state_totals):
    """State residual split by population over the hidden counties of the state, clipped to 1..hi."""
    est = np.full(len(t), np.nan)
    exact = status == "exact"
    hidden = status == "censored"
    pub = t[exact].groupby("state").y.sum()
    for s, g in t[hidden].groupby("state"):
        resid = max(state_totals[s] - pub.get(s, 0.0), 0.0) if s in state_totals.index else np.nan
        share = g["pop"] / g["pop"].sum()
        est[t.index.get_indexer(g.index)] = np.clip(resid * share.values, 1, hi[t.index.get_indexer(g.index)])
    return est
