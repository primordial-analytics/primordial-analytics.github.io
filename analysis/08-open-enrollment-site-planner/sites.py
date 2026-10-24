"""Site planning: which venues put the most eligible uninsured people within reach.

Reach of a plan S: sum over tracts i of w_i * min(1, sum over sites j in S of a_ij). w_i is the expected number of
eligible uninsured people in tract i; a_ij = exp(-2 (d_ij / R)^2) if d_ij <= R, else 0, is the share of tract i's people
a site at j is expected to reach; d is straight-line miles x 1.3 (a stated circuity factor, no road network) and R the
travel distance. The cap at 1 is the competing-site discount: a person near several sites is counted once. The objective
is monotone and submodular, so greedy is within 1 - 1/e of the best plan; the browser runs the same greedy rule, and
this module also solves each county exactly as a mixed-integer program (HiGHS) to report the gap.
"""
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import csr_matrix, hstack, identity

CIRCUITY = 1.3
R_DEFAULT = {0: 15.0, 1: 5.0, 2: 3.0}  # miles by density class: rural, suburban, urban
R_MAX = 25.0  # the largest travel distance the planner offers
INFLATION_KS = (3, 5, 8)


def haversine_miles(lat1, lon1, lat2, lon2):
    """Pairwise great-circle miles between points 1 (n) and points 2 (m): n x m."""
    la1, lo1, la2, lo2 = map(np.radians, (lat1[:, None], lon1[:, None], lat2[None, :], lon2[None, :]))
    a = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 2 * 3958.8 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def county_radius(density_class, pop):
    """Default travel distance for a county from where its people live: urban if half live in urban tracts, suburban if half
    live in urban or suburban tracts, otherwise rural."""
    pop = np.asarray(pop, float)
    tot = max(pop.sum(), 1.0)
    urban = pop[density_class == 2].sum() / tot
    mixed = pop[density_class >= 1].sum() / tot
    return R_DEFAULT[2] if urban >= 0.5 else (R_DEFAULT[1] if mixed >= 0.5 else R_DEFAULT[0])


def reach_matrix(tract_lat, tract_lon, site_lat, site_lon, R):
    d = CIRCUITY * haversine_miles(tract_lat, tract_lon, site_lat, site_lon)
    return np.where(d <= R, np.exp(-2.0 * (d / R) ** 2), 0.0)


def plan_coverage(a, sel):
    """Per-tract share reached, capped at 1."""
    return np.minimum(1.0, a[:, list(sel)].sum(1)) if len(sel) else np.zeros(a.shape[0])


def reach(a, w, sel):
    return float(w @ plan_coverage(a, sel))


def greedy(a, w, k, fixed=()):
    """Greedy maximum coverage. `fixed` sites are in the plan already and do not count toward k."""
    sel = list(fixed)
    cov = plan_coverage(a, sel)
    chosen = []
    for _ in range(min(k, a.shape[1] - len(sel))):
        gain = w @ (np.minimum(1.0, cov[:, None] + a) - cov[:, None])
        gain[sel] = -1.0
        j = int(np.argmax(gain))
        if gain[j] <= 0:
            break
        sel.append(j)
        chosen.append(j)
        cov = np.minimum(1.0, cov + a[:, j])
    return chosen


def exact(a, w, k, time_limit=30.0):
    """Best k sites as a mixed-integer program. Returns (sites, reach, optimal, mip_gap)."""
    n, m = a.shape
    keep = np.flatnonzero(a.sum(0) > 0)
    if len(keep) <= k:
        sel = list(keep)
        return sel, reach(a, w, sel), True, 0.0
    A = csr_matrix(a[:, keep])
    # variables: x (len(keep) binary), z (n, 0..1);  z_i - sum_j a_ij x_j <= 0;  sum x = k;  maximise w.z
    cons = [LinearConstraint(hstack([-A, identity(n, format="csr")]), -np.inf, 0.0),
            LinearConstraint(np.r_[np.ones(len(keep)), np.zeros(n)][None, :], k, k)]
    integrality = np.r_[np.ones(len(keep)), np.zeros(n)]
    res = milp(c=-np.r_[np.zeros(len(keep)), w], constraints=cons, integrality=integrality, bounds=Bounds(0, 1),
               options={"time_limit": time_limit, "mip_rel_gap": 1e-4})
    if res.x is None:
        return [], 0.0, False, np.nan
    sel = [int(keep[j]) for j in np.flatnonzero(res.x[:len(keep)] > 0.5)]
    return sel, reach(a, w, sel), bool(res.status == 0), float(getattr(res, "mip_gap", np.nan) or 0.0)


def nearest_unused(site_d, tract_order, k, vv=None, min_sep=0.0):
    """Strategy picks: for each ranked tract take the nearest venue not yet used (and, when vv and min_sep are given, farther than
    min_sep miles from every venue already taken; a tract with no such venue is skipped). site_d is tracts x sites distances,
    vv the venue-to-venue distances."""
    used, sel = set(), []
    for i in tract_order:
        for j in np.argsort(site_d[i]):
            if j in used:
                continue
            if vv is not None and any(vv[j, u] <= min_sep for u in sel):
                continue
            used.add(j)
            sel.append(int(j))
            break
        if len(sel) == k:
            break
    return sel


def plan_variance_ratio(a, draws, sel):
    """True variance of a plan's reach (from the posterior draws, which share county-wide error) over the variance obtained by
    treating tracts as independent. draws: tracts x K of the eligible count."""
    c = plan_coverage(a, sel)
    ind_var = (c ** 2 * draws.var(1)).sum()
    return float((c @ draws).var() / ind_var) if ind_var > 0 else np.nan


def inflation_factor(a, mean, draws, ks=INFLATION_KS):
    """County factor for the planner's interval: the square root of the mean variance ratio over the greedy plans of 3, 5 and 8
    sites (the plans a user is shown). mean and draws are for the eligible count per tract."""
    if a.shape[1] < 2 or draws.shape[0] < 2:
        return 1.0
    ratios = [plan_variance_ratio(a, draws, greedy(a, mean, k)) for k in ks]
    ratios = [r for r in ratios if np.isfinite(r)]
    return float(np.sqrt(np.mean(ratios))) if ratios else 1.0
