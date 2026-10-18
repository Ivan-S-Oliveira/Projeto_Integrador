"""Medição simples de tempo e memória para os notebooks SRAG."""
from __future__ import annotations
import gc, os, threading, time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd
try:
    import psutil
except ImportError:
    psutil = None
try:
    import pyarrow as pa
except ImportError:
    pa = None
_MB = 1_048_576

def rss_mb() -> float:
    return 0.0 if psutil is None else psutil.Process(os.getpid()).memory_info().rss / _MB

def arrow_mb() -> float:
    return 0.0 if pa is None else pa.total_allocated_bytes() / _MB

def memoria_df_mb(obj) -> float:
    uso = obj.memory_usage(index=True, deep=True)
    return float(uso.sum() if hasattr(uso, "sum") else uso) / _MB

def liberar(namespace: dict, nomes, fechar_figuras: bool=True) -> list[str]:
    removidos=[]
    for nome in nomes:
        if nome in namespace:
            del namespace[nome]; removidos.append(nome)
    if fechar_figuras:
        try:
            import matplotlib.pyplot as plt
            plt.close("all")
        except Exception:
            pass
    antes=rss_mb(); gc.collect(); depois=rss_mb()
    print(f"[liberar] {removidos} | RSS {antes:,.0f} -> {depois:,.0f} MB")
    return removidos

class _Pico:
    def __init__(self, intervalo=0.2):
        self.intervalo=intervalo; self.pico=rss_mb(); self.stop=threading.Event()
        self.thread=threading.Thread(target=self._run,daemon=True)
    def _run(self):
        while not self.stop.is_set():
            self.pico=max(self.pico,rss_mb()); time.sleep(self.intervalo)
    def __enter__(self): self.thread.start(); return self
    def __exit__(self,*_):
        self.stop.set(); self.thread.join(timeout=2); self.pico=max(self.pico,rss_mb())

@dataclass
class Monitor:
    notebook: str
    pasta_saida: Path|None=None
    registros: list[dict]=field(default_factory=list)
    @contextmanager
    def etapa(self,nome: str,**extras):
        inicio=time.perf_counter(); rss0=rss_mb(); arr0=arrow_mb(); status="ok"
        try:
            with _Pico() as pico: yield
        except BaseException:
            status="erro"; raise
        finally:
            reg={"notebook":self.notebook,"etapa":nome,"status":status,
                 "duracao_s":round(time.perf_counter()-inicio,3),
                 "rss_inicio_mb":round(rss0,1),"rss_fim_mb":round(rss_mb(),1),
                 "rss_pico_mb":round(pico.pico,1),"arrow_inicio_mb":round(arr0,1),
                 "arrow_fim_mb":round(arrow_mb(),1)}
            reg.update(extras); self.registros.append(reg)
            print(f"[{self.notebook}] {nome}: {reg['duracao_s']}s | pico {reg['rss_pico_mb']} MB | {status}")
    def resumo(self): return pd.DataFrame(self.registros)
    def salvar(self):
        pasta=self.pasta_saida or Path("outputs/performance"); pasta.mkdir(parents=True,exist_ok=True)
        caminho=pasta/f"{self.notebook}.csv"; self.resumo().to_csv(caminho,index=False,encoding="utf-8-sig")
        return caminho
