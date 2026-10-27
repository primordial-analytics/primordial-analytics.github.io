"""The funder network: funders and peer organizations joined by grants, and four ways to rank funders for one
organization, compared on later years (backtest()).

  popular_near   funders ranked by how many peers in the organization's 3-digit ZIP area they fund, then its state
  adding_state   funders ranked by how many peers in the organization's state they began funding in the last training
                 year: funders taking on new grantees nearby
  popular_state  funders ranked by how many peers in the organization's state they fund
  popular        funders ranked by how many peers they fund anywhere
  shared         "funds your peers": funders of the organizations that share funders with this one, each peer weighted by
                 how many funders it shares, and each shared funder by 1 / log(1 + the number of peers it funds), so a
                 funder that funds everyone says little (Adamic-Adar)
  pagerank       personalized PageRank from the organization over the whole network (restart probability 0.15)

A funder that already funds the organization is never suggested to it.
"""
import numpy as np
import pandas as pd
from scipy import sparse

METHODS = ["popular_near", "adding_state", "popular_state", "popular", "shared", "pagerank"]
TOP = 10
RESTART = 0.15
SEED = 12


class Network:
    """Funder x peer matrix from edges (funder_ein, peer_ein, tax_year) in the chosen years. peers: STATE and zip3 by
    peer EIN."""

    def __init__(self, edges, peers):
        self.funders = np.array(sorted(edges.funder_ein.unique()))
        self.peers = np.array(sorted(peers.index))
        fi = pd.Series(np.arange(len(self.funders)), self.funders)
        pi = pd.Series(np.arange(len(self.peers)), self.peers)
        e = edges[["funder_ein", "peer_ein"]].drop_duplicates()
        e = e[e.peer_ein.isin(pi.index)]
        self.A = sparse.csr_matrix((np.ones(len(e)), (fi[e.funder_ein].values, pi[e.peer_ein].values)),
                                   shape=(len(self.funders), len(self.peers)))
        self.fi, self.pi = fi, pi
        p = peers.reindex(self.peers)
        self.state_of = np.unique(p.STATE.fillna("").values, return_inverse=True)[1]
        self.zip3_of = np.unique((p.STATE.fillna("") + p.zip3.fillna("")).values, return_inverse=True)[1]
        last = edges.tax_year.max()
        before = set(map(tuple, edges[edges.tax_year < last][["funder_ein", "peer_ein"]].values))
        n = e.merge(edges[edges.tax_year == last][["funder_ein", "peer_ein"]].drop_duplicates())
        n = n[[t not in before for t in map(tuple, n.values)]]
        self.Anew = sparse.csr_matrix((np.ones(len(n)), (fi[n.funder_ein].values, pi[n.peer_ein].values)),
                                      shape=self.A.shape)

    def scores(self, method, cols):
        """Funder scores (funders x len(cols)) for the peers at matrix columns `cols`."""
        A = self.A
        if method == "popular":
            return np.repeat(np.asarray(A.sum(1)), len(cols), axis=1)
        if method == "popular_state":
            return self._by(A, self.state_of, cols) + 1e-3 * np.asarray(A.sum(1))  # ties: national count
        if method == "popular_near":
            return self._by(A, self.zip3_of, cols) + 1e-3 * self.scores("popular_state", cols)
        if method == "adding_state":
            return self._by(self.Anew, self.state_of, cols) + 1e-3 * self.scores("popular_state", cols)
        if method == "shared":
            deg = np.asarray(A.sum(1)).ravel()
            W = sparse.diags(1 / np.log1p(np.maximum(deg, 1)))
            sim = (A.T @ W @ A[:, cols]).toarray()  # peers x cols
            sim[cols, np.arange(len(cols))] = 0
            return A @ sim + 1e-6 * self.scores("popular_state", cols)  # ties and cold starts: the state ranking
        if method == "pagerank":
            nf, npr = A.shape
            B = sparse.bmat([[None, A], [A.T, None]]).tocsr()
            out = np.asarray(B.sum(1)).ravel()
            P = sparse.diags(1 / np.maximum(out, 1)) @ B  # row-stochastic where there are edges
            r = np.zeros((nf + npr, len(cols)))
            r[nf + np.asarray(cols), np.arange(len(cols))] = 1
            x = r.copy()
            for _ in range(40):
                x = RESTART * r + (1 - RESTART) * (P.T @ x)
            return x[:nf] + 1e-9 * self.scores("popular_state", cols)
        raise ValueError(method)

    @staticmethod
    def _by(M, group_of, cols):
        G = sparse.csr_matrix((np.ones(M.shape[1]), (np.arange(M.shape[1]), group_of)))
        return (M @ G).toarray()[:, group_of[cols]]

    def top(self, method, cols, k=TOP):
        """Top-k funder rows for each column, never a funder the peer already has."""
        s = self.scores(method, cols)
        s[self.A[:, cols].toarray() > 0] = -np.inf
        idx = np.argpartition(-s, k, axis=0)[:k]
        order = np.argsort(-np.take_along_axis(s, idx, 0), axis=0)
        return np.take_along_axis(idx, order, 0)


def backtest(edges, peers, train, test, rng_seed=SEED, reps=1000):
    """Train on tax years `train`, score the funders each peer gained in years `test`.

    Peers scored: those with at least one funder in training and at least one new funder in the test years. New funders
    that gave nothing to any peer in training cannot be suggested by any method; their share is reported as `unseen`.
    Returns a summary table (hit rate: share of peers with at least one new funder in their top 10; recall: share of
    new funders found in the top 10; both with bootstrap 95% intervals over peers) and the peers scored.
    """
    tr = edges[edges.tax_year.isin(train)]
    te = edges[edges.tax_year.isin(test)]
    net = Network(tr, peers)
    had = tr.groupby("peer_ein").funder_ein.agg(set)
    new = te.groupby("peer_ein").funder_ein.agg(set)
    new = {p: s - had.get(p, set()) for p, s in new.items()}
    peers = [p for p in net.peers if p in had.index and new.get(p)]
    reach = {p: {f for f in new[p] if f in net.fi.index} for p in peers}
    unseen = 1 - sum(len(v) for v in reach.values()) / sum(len(new[p]) for p in peers)
    cols = net.pi[peers].values
    rows = {}
    for m in METHODS:
        top = net.top(m, cols)
        hits = np.array([len(set(net.funders[top[:, j]]) & new[p]) for j, p in enumerate(peers)])
        size = np.array([len(new[p]) for p in peers])
        rows[m] = pd.DataFrame({"peer": peers, "hits": hits, "new": size})
    rng = np.random.default_rng(rng_seed)
    boot = rng.integers(0, len(peers), size=(reps, len(peers)))
    out = []
    for m, d in rows.items():
        hit = (d.hits > 0).values.astype(float)
        rec = d.hits.values / d.new.values
        hb, rb = hit[boot].mean(1), rec[boot].mean(1)
        out.append(dict(method=m, peers=len(d), hit_rate=hit.mean(), hit_lo=np.quantile(hb, .025),
                        hit_hi=np.quantile(hb, .975), recall=rec.mean(), recall_lo=np.quantile(rb, .025),
                        recall_hi=np.quantile(rb, .975)))
    return pd.DataFrame(out).set_index("method"), rows, unseen
