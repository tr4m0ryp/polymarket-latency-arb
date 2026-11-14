"""Which Binance feed does the 5m book follow? 50 ms receipt-clock grid: spot bookTicker mid,
USD-M perp bookTicker mid, 5m Up-token book mid (spread <= 5 c). Prints cross-correlations and a
joint lagged regression of book changes on both feeds (standardized betas).

    python3 latency/leadlag/leadlag.py <hour> [<hour> ...]   (hour = unix_ts // 3600)"""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import load, book
hours = [int(h) for h in sys.argv[1:]]
L = load.LIVE
def files(s): return [p for h in hours for p in L.glob(f"*/{s}-{h}.tsv.gz")]
def bn(s):
    rows=[]
    for p in files(s):
        for t,raw in load._lines(p):
            d=json.loads(raw)["data"]
            if s=="binance" and "b" in d and "a" in d: rows.append((t,0.0,(float(d["b"])+float(d["a"]))/2))
            elif s=="binance_fut" and "b" in d: rows.append((t,d["T"]/1e3,(float(d["b"])+float(d["a"]))/2))
    return pd.DataFrame(rows,columns=["t","ts","px"]).sort_values("t")
sp, fu = bn("binance"), bn("binance_fut")
clob = pd.concat([load._clob(p) for p in files("clob_5m")]).sort_values("t", kind="stable")
mk = load.markets(); mk = mk[mk.fam=="5m"]
dt=0.05; t0=max(sp.t.iloc[0],fu.t.iloc[0]); t1=min(sp.t.iloc[-1],fu.t.iloc[-1])
grid=np.arange(t0,t1,dt)
def lvl(df,col="t"):
    i=np.searchsorted(df[col].to_numpy(),grid,side="right")-1
    return np.log(df.px.to_numpy()[np.clip(i,0,None)])
rs, rf = np.diff(lvl(sp)), np.diff(lvl(fu))
pm = np.full(len(grid), np.nan)
for m in mk.itertuples():
    rows = clob[clob.market==m.condition_id]
    if len(rows)<100: continue
    top,_ = book.replay(rows, m.up, np.array([]))
    sel=(grid>m.start+5)&(grid<m.end-30)
    bb,ba=book.top_at(top,grid[sel]); mid=(bb+ba)/2
    mid[(ba-bb)>0.05]=np.nan
    pm[sel]=mid
dpm=np.diff(pm)
def xc(a,b,k):  # corr(a[t], b[t-k])
    x,y=(a[k:],b[:len(b)-k]) if k>=0 else (a[:k],b[-k:])
    ok=~(np.isnan(x)|np.isnan(y)); return np.corrcoef(x[ok],y[ok])[0,1]
ks=[-4,-2,0,1,2,3,4,5,6,8,10,14,20,30]
print("hours",hours,"bins",len(rs))
print("lag ms      ", [int(k*dt*1e3) for k in ks])
print("PM vs spot  ", [round(xc(dpm,rs,k),3) for k in ks])
print("PM vs perp  ", [round(xc(dpm,rf,k),3) for k in ks])
print("spot vs perp", [round(xc(rs,rf,k),3) for k in ks])
# partial: regress dpm on lagged spot and perp jointly, k=1..20
X=[];names=[]
for k in range(1,21):
    X.append(np.r_[np.full(k,np.nan),rs[:-k]]); names.append(f"s{k}")
    X.append(np.r_[np.full(k,np.nan),rf[:-k]]); names.append(f"f{k}")
X=np.array(X).T; ok=~np.isnan(X).any(1)&~np.isnan(dpm)
Xs=(X[ok]-X[ok].mean(0))/X[ok].std(0); b=np.linalg.lstsq(np.c_[np.ones(ok.sum()),Xs],dpm[ok],rcond=None)[0][1:]
print("joint betas (x1e4) spot:",[round(b[2*i]*1e4,2) for i in range(20)])
print("joint betas (x1e4) perp:",[round(b[2*i+1]*1e4,2) for i in range(20)])
print("sum spot",round(b[0::2].sum()*1e4,2),"sum perp",round(b[1::2].sum()*1e4,2))
