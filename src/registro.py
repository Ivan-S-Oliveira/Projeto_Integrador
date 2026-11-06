"""Registro simples de execuções e medição de tempo."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import gc
import os
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
import pandas as pd

from src import config as C


def _commit() -> str | None:
    try:
        proc = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=C.ROOT_DIR,
                              capture_output=True, text=True, timeout=10)
        return proc.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def salvar_resultado(nome: str, dados: dict[str, Any], pasta_base: Path | None = None) -> Path:
    """Grava metadata.json em outputs/runs/<data>_<nome>/."""
    base = Path(pasta_base) if pasta_base is not None else C.RUNS_DIR
    pasta = base / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}_{nome}"
    pasta.mkdir(parents=True, exist_ok=False)
    registro = {"nome": nome, "utc": datetime.now(timezone.utc).isoformat(), "commit": _commit(),
                "seed": C.SEED, "yaml_sha256": C.supervised_yaml_sha256(), **dados}
    (pasta / "metadata.json").write_text(json.dumps(registro, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return pasta


class Run:
    """Registra uma execução ao sair do bloco with, mesmo com erro."""

    def __init__(self, modelo: str, *, seed: int | None = None, parametros: dict | None = None,
                 dataset: dict | None = None, features: dict | None = None, notas: str | None = None,
                 output_dir: Path | None = None, dataset_path: Path | None = None,
                 dataset_sha256: str | None = None) -> None:
        self.modelo = modelo
        self.seed = seed
        self.parametros = dict(parametros or {})
        self.dataset = dict(dataset or {})
        self.features = dict(features or {})
        self.notas = notas
        self.output_dir = output_dir
        self.dataset_path = dataset_path
        self.dataset_sha256 = dataset_sha256
        self.metricas: dict[str, Any] = {}
        self.pasta: Path | None = None
        self._inicio: float | None = None

    def metrica(self, **kwargs: Any) -> "Run":
        self.metricas.update(kwargs)
        return self

    def anotar(self, texto: str) -> "Run":
        self.notas = f"{self.notas}\n{texto}" if self.notas else texto
        return self

    def add_dataset(self, **kwargs: Any) -> "Run":
        self.dataset.update(kwargs)
        return self

    def __enter__(self) -> "Run":
        self._inicio = time.perf_counter()
        return self

    def __exit__(self, tipo, erro, tb) -> bool:
        self.pasta = salvar_resultado(self.modelo, {
            "status": "ok" if tipo is None else "erro",
            "erro": None if tipo is None else f"{tipo.__name__}: {erro}",
            "duracao_s": time.perf_counter() - self._inicio if self._inicio else None,
            "seed": self.seed if self.seed is not None else C.SEED,
            "parametros": self.parametros, "dataset": self.dataset,
            "dataset_path": self.dataset_path, "dataset_sha256": self.dataset_sha256,
            "features": self.features, "metricas": self.metricas, "notas": self.notas,
        }, self.output_dir)
        print(f"Execução registrada em: {self.pasta}")
        return False


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
        pasta=self.pasta_saida or (C.OUTPUTS_DIR / "performance"); pasta.mkdir(parents=True,exist_ok=True)
        caminho=pasta/f"{self.notebook}.csv"; self.resumo().to_csv(caminho,index=False,encoding="utf-8-sig")
        return caminho
