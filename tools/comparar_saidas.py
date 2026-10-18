from pathlib import Path
import sys, numpy as np, pandas as pd

def comparar(a,b,rtol=1e-6):
    rows=[]
    for pa in sorted(Path(a).glob("*.csv")):
        pb=Path(b)/pa.name
        if not pb.exists(): rows.append((pa.name,"ausente_depois",None)); continue
        x=pd.read_csv(pa,encoding="utf-8-sig"); y=pd.read_csv(pb,encoding="utf-8-sig")
        if x.shape!=y.shape or list(x.columns)!=list(y.columns): rows.append((pa.name,"estrutura_diferente",f"{x.shape} x {y.shape}")); continue
        dif=0
        for c in x.columns:
            if pd.api.types.is_numeric_dtype(x[c]) and pd.api.types.is_numeric_dtype(y[c]):
                iguais=np.isclose(x[c],y[c],rtol=rtol,equal_nan=True)
            else: iguais=x[c].astype("string").fillna("<NA>").eq(y[c].astype("string").fillna("<NA>")).to_numpy()
            dif+=int((~iguais).sum())
        rows.append((pa.name,"igual" if dif==0 else "diferente",f"{dif} células diferentes"))
    return pd.DataFrame(rows,columns=["arquivo","status","detalhe"])
if __name__=="__main__":
    r=comparar(sys.argv[1],sys.argv[2]); print(r.to_string(index=False)); raise SystemExit(0 if (r.status=="igual").all() else 1)
