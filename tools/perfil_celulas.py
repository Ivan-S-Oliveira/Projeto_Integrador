"""Executa um notebook célula a célula e mostra onde estão o tempo e a memória."""
from __future__ import annotations

import argparse
import csv
import json
import queue
import threading
import time
from pathlib import Path

import psutil
from jupyter_client import KernelManager

RAIZ = Path(__file__).resolve().parents[1]
PASTA_SAIDA = RAIZ / "outputs" / "final"
MB = 1024 * 1024
INTERVALO_AMOSTRA_S = 0.2


class MedidorMemoria(threading.Thread):
    """Lê a memória residente do kernel e dos filhos a cada 0,2 s e guarda o pico."""

    def __init__(self, pid: int) -> None:
        super().__init__(daemon=True)
        self.processo = psutil.Process(pid)
        self.pico = 0.0
        self.atual = 0.0
        self._parar = threading.Event()

    def _ler_mb(self) -> float:
        total = 0
        try:
            for p in [self.processo, *self.processo.children(recursive=True)]:
                try:
                    total += p.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return total / MB

    def run(self) -> None:
        while not self._parar.is_set():
            self.atual = self._ler_mb()
            self.pico = max(self.pico, self.atual)
            time.sleep(INTERVALO_AMOSTRA_S)

    def reiniciar_pico(self) -> None:
        self.atual = self._ler_mb()
        self.pico = self.atual

    def parar(self) -> None:
        self._parar.set()


def _resumo(codigo: str, limite: int = 70) -> str:
    """Primeira linha útil da célula, para identificá-la na tabela."""
    for linha in codigo.splitlines():
        texto = linha.strip()
        if texto and not set(texto) <= set("#=-─ "):
            return texto[:limite]
    return ""


def _executar(km: KernelManager, kc, codigo: str) -> str | None:
    """Envia o código ao kernel e espera terminar."""
    id_msg = kc.execute(codigo, store_history=True, allow_stdin=False)
    erro = None
    while True:
        try:
            msg = kc.get_iopub_msg(timeout=5)
        except queue.Empty:
            if not km.is_alive():
                return "O kernel morreu durante a célula (quase sempre falta de memória)."
            continue
        if msg["parent_header"].get("msg_id") != id_msg:
            continue
        tipo = msg["msg_type"]
        if tipo == "error":
            conteudo = msg["content"]
            erro = f"{conteudo.get('ename')}: {conteudo.get('evalue')}"
        elif tipo == "status" and msg["content"]["execution_state"] == "idle":
            break
    try:
        kc.get_shell_msg(timeout=30)
    except queue.Empty:
        pass
    return erro


def perfilar(caminho: Path, ate: int | None, trocas: list[tuple[str, str]], pular: list[str]) -> list[dict]:
    notebook = json.loads(caminho.read_text(encoding="utf-8"))
    celulas = notebook.get("cells", [])
    memoria = psutil.virtual_memory()
    print(f"Máquina: {memoria.total / 1024**3:.1f} GB de RAM, {memoria.available / 1024**3:.1f} GB livres agora, "
          f"{psutil.cpu_count(logical=True)} processadores lógicos.")

    km = KernelManager(kernel_name="python3")
    km.start_kernel(cwd=str(caminho.parent))
    kc = km.client()
    kc.start_channels()
    kc.wait_for_ready(timeout=120)
    pid = km.provisioner.pid
    medidor = MedidorMemoria(pid)
    medidor.start()

    linhas: list[dict] = []
    pico_global = 0.0
    try:
        for numero, celula in enumerate(celulas, start=1):
            if ate is not None and numero > ate:
                break
            if celula.get("cell_type") != "code":
                continue
            fonte = celula.get("source", "")
            codigo = "".join(fonte) if isinstance(fonte, list) else fonte
            if not codigo.strip():
                continue
            if any(t in codigo for t in pular):
                linhas.append({"celula": numero, "duracao_s": 0.0, "rss_antes_mb": round(medidor.atual),
                               "rss_depois_mb": round(medidor.atual), "pico_mb": round(medidor.atual),
                               "subida_mb": 0, "delta_mb": 0, "status": "pulada", "resumo": _resumo(codigo)})
                continue
            for antigo, novo in trocas:
                codigo = codigo.replace(antigo, novo)

            medidor.reiniciar_pico()
            antes = medidor.atual
            inicio = time.perf_counter()
            erro = _executar(km, kc, codigo)
            duracao = time.perf_counter() - inicio
            time.sleep(INTERVALO_AMOSTRA_S * 1.5)
            depois = medidor.atual
            pico = max(medidor.pico, depois)
            pico_global = max(pico_global, pico)
            linhas.append({"celula": numero, "duracao_s": round(duracao, 1), "rss_antes_mb": round(antes),
                           "rss_depois_mb": round(depois), "pico_mb": round(pico), "subida_mb": round(pico - antes),
                           "delta_mb": round(depois - antes),
                           "status": "ERRO: " + erro if erro else "ok", "resumo": _resumo(codigo)})
            print(f"célula {numero:>3} · {duracao:7.1f} s · pico {pico:8.0f} MB · "
                  f"{'ERRO ' + erro if erro else 'ok'}", flush=True)
            if erro:
                break
    finally:
        medidor.parar()
        kc.stop_channels()
        km.shutdown_kernel(now=True)
    return linhas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("notebook", type=Path)
    ap.add_argument("--ate", type=int, default=None)
    ap.add_argument("--trocar", nargs=2, action="append", default=[], metavar=("ANTIGO", "NOVO"))
    ap.add_argument("--pular-texto", action="append", default=[], dest="pular")
    args = ap.parse_args()

    caminho = args.notebook if args.notebook.is_absolute() else (RAIZ / args.notebook)
    caminho = caminho.resolve()
    if not caminho.is_file():
        print(f"Notebook não encontrado: {caminho}")
        return 1

    linhas = perfilar(caminho, args.ate, [tuple(t) for t in args.trocar], args.pular)
    if not linhas:
        print("Nenhuma célula de código foi executada.")
        return 1

    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    saida = PASTA_SAIDA / f"perfil_celulas_{caminho.stem}.csv"
    with saida.open("w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        escritor.writeheader()
        escritor.writerows(linhas)

    executadas = [l for l in linhas if l["status"] != "pulada"]
    print("\nCélulas que mais fizeram a memória subir (pico menos o valor antes da célula):")
    for l in sorted(executadas, key=lambda x: x["subida_mb"], reverse=True)[:8]:
        print(f"  célula {l['celula']:>3} · subiu {l['subida_mb']:>7} MB · pico {l['pico_mb']:>7} MB · "
              f"{l['duracao_s']:>6} s · {l['resumo']}")
    maior = max(executadas, key=lambda x: x["pico_mb"])
    print(f"\nMaior pico absoluto do kernel: {maior['pico_mb']:,} MB, na célula {maior['celula']}.")
    print("\nCélulas mais demoradas:")
    for l in sorted(executadas, key=lambda x: x["duracao_s"], reverse=True)[:8]:
        print(f"  célula {l['celula']:>3} · {l['duracao_s']:>7} s · pico {l['pico_mb']:>6} MB · {l['resumo']}")
    total_s = sum(l["duracao_s"] for l in executadas)
    pico = max(l["pico_mb"] for l in executadas)
    print(f"\n{len(executadas)} células · {total_s:.0f} s no total · pico do kernel {pico:,} MB")
    print(f"Tabela completa: {saida}")
    return 0 if not any(str(l["status"]).startswith("ERRO") for l in linhas) else 2


if __name__ == "__main__":
    raise SystemExit(main())
