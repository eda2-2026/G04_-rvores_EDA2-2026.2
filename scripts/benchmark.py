"""
Experimento: verificar conflito de horário com a árvore rubro-negra
x varrendo a lista inteira de reservas.

Cenário: uma sala com n reservas de 30 minutos, uma por hora, em
sequência (o pior caso para uma árvore sem balanceamento, pois as
chaves entram em ordem crescente). Consultas aleatórias de 15 minutos,
em passos de 5 minutos: uma parte cai em conflito, outra cabe.

Uso:
    python scripts/benchmark.py
    python scripts/benchmark.py --tamanhos 1000 10000 100000 --consultas 300
    python scripts/benchmark.py --saida docs/resultados_benchmark.md
"""

import argparse
import os
import random
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rubro_negra import ArvoreRubroNegra

BASE = datetime(2026, 1, 1, 7, 0)


def montar(n):
    """Retorna (árvore, lista) com n reservas (inicio, fim)."""
    arvore = ArvoreRubroNegra()
    lista = []
    inicio_montagem = time.perf_counter()
    for i in range(n):
        inicio = BASE + timedelta(minutes=60 * i)
        fim = inicio + timedelta(minutes=30)
        arvore.inserir(inicio, (inicio, fim))
        lista.append((inicio, fim))
    return arvore, lista, time.perf_counter() - inicio_montagem


def conflito_na_arvore(arvore, inicio, fim):
    anterior = arvore.piso(inicio)
    if anterior is not None and anterior[1][1] > inicio:
        return True
    proxima = arvore.sucessor(inicio)
    return proxima is not None and proxima[1][0] < fim


def conflito_por_varredura(lista, inicio, fim):
    """Retorna (há_conflito, comparações): compara com cada reserva até achar uma."""
    comparacoes = 0
    for i, f in lista:
        comparacoes += 1
        if i < fim and f > inicio:
            return True, comparacoes
    return False, comparacoes


def formatar_tempo(segundos):
    micros = segundos * 1_000_000
    return f"{micros:.1f} µs" if micros < 1000 else f"{micros / 1000:.2f} ms"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tamanhos", type=int, nargs="+", default=[1000, 10000, 100000])
    parser.add_argument("--consultas", type=int, default=300)
    parser.add_argument("--semente", type=int, default=2026)
    parser.add_argument("--saida", default=None)
    args = parser.parse_args()

    rng = random.Random(args.semente)
    linhas = [
        "| Reservas na sala | Altura da árvore | Árvore: nós visitados (média) | Varredura: comparações (média) "
        "| Árvore: tempo por consulta | Varredura: tempo por consulta | Mesma resposta nas duas |",
        "|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    print(linhas[0]); print(linhas[1], flush=True)

    for n in args.tamanhos:
        arvore, lista, _ = montar(n)

        consultas = []
        for _ in range(args.consultas):
            inicio = BASE + timedelta(minutes=5 * rng.randrange(0, 12 * n))
            consultas.append((inicio, inicio + timedelta(minutes=15)))

        # árvore
        visitas_antes = arvore.visitas
        resultados_arvore = []
        t0 = time.perf_counter()
        for inicio, fim in consultas:
            resultados_arvore.append(conflito_na_arvore(arvore, inicio, fim))
        tempo_arvore = (time.perf_counter() - t0) / len(consultas)
        visitas_medias = (arvore.visitas - visitas_antes) / len(consultas)

        # varredura
        resultados_varredura = []
        total_comparacoes = 0
        t0 = time.perf_counter()
        for inicio, fim in consultas:
            achou, comparacoes = conflito_por_varredura(lista, inicio, fim)
            resultados_varredura.append(achou)
            total_comparacoes += comparacoes
        tempo_varredura = (time.perf_counter() - t0) / len(consultas)

        iguais = "sim" if resultados_arvore == resultados_varredura else "NÃO"
        linha = (
            f"| {n} | {arvore.altura()} | {visitas_medias:.1f} | {total_comparacoes / len(consultas):.1f} "
            f"| {formatar_tempo(tempo_arvore)} | {formatar_tempo(tempo_varredura)} | {iguais} |"
        )
        linhas.append(linha)
        print(linha, flush=True)

    if args.saida:
        os.makedirs(os.path.dirname(os.path.abspath(args.saida)), exist_ok=True)
        with open(args.saida, "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(linhas) + "\n")
        print(f"\nTabela salva em {args.saida}")


if __name__ == "__main__":
    main()
