"""
Desenho da árvore rubro-negra em SVG.

Usa a própria estrutura da árvore (nada é reimplementado aqui). Cada
nó vira um círculo vermelho ou preto; `rotulo` define o texto dentro
do nó e `dica` o texto que aparece ao passar o mouse.
"""

import html
from typing import Any, Callable, Dict, List, Optional

from rubro_negra import ArvoreRubroNegra, VERMELHO

RAIO = 23
ESPACO_X = 58
ESPACO_Y = 76
MARGEM = 34

COR_VERMELHO = "#C9382E"
COR_PRETO = "#1C2530"
COR_ARESTA = "#8795A6"
COR_DESTAQUE = "#E8A317"


def svg_da_arvore(
    arvore: ArvoreRubroNegra,
    destaque: Optional[Any] = None,
    rotulo: Optional[Callable[[Any], str]] = None,
    dica: Optional[Callable[[Any, Any], str]] = None,
) -> str:
    """Retorna o SVG da árvore. `destaque` circunda a chave informada."""
    rotulo = rotulo or str

    if arvore.raiz is arvore.NIL:
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="110" '
            'viewBox="0 0 320 110"><text x="160" y="58" text-anchor="middle" '
            'font-size="15" fill="#5B6878">sem reservas nesta sala</text></svg>'
        )

    nos: List[Any] = []

    def percorrer(no, nivel):
        if no is arvore.NIL:
            return
        percorrer(no.esq, nivel + 1)
        nos.append((no, nivel))
        percorrer(no.dir, nivel + 1)

    percorrer(arvore.raiz, 0)

    posicoes: Dict[int, Any] = {}
    maior_nivel = 0
    for indice, (no, nivel) in enumerate(nos):
        posicoes[id(no)] = (MARGEM + indice * ESPACO_X, MARGEM + nivel * ESPACO_Y)
        maior_nivel = max(maior_nivel, nivel)

    largura = max(MARGEM * 2 + (len(nos) - 1) * ESPACO_X, 320)
    altura = MARGEM * 2 + maior_nivel * ESPACO_Y

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" '
        f'viewBox="0 0 {largura} {altura}" role="img" '
        f'aria-label="Árvore rubro-negra com {len(nos)} nós">'
    ]

    for no, _ in nos:
        x, y = posicoes[id(no)]
        for filho in (no.esq, no.dir):
            if filho is not arvore.NIL:
                fx, fy = posicoes[id(filho)]
                partes.append(
                    f'<line x1="{x}" y1="{y}" x2="{fx}" y2="{fy}" '
                    f'stroke="{COR_ARESTA}" stroke-width="2"/>'
                )

    for no, _ in nos:
        x, y = posicoes[id(no)]
        cor = COR_VERMELHO if no.cor == VERMELHO else COR_PRETO
        texto = rotulo(no.chave)
        tamanho_fonte = 14 if len(texto) <= 3 else 12

        partes.append("<g>")
        if dica is not None:
            partes.append(f"<title>{html.escape(dica(no.chave, no.valor))}</title>")
        if destaque is not None and no.chave == destaque:
            partes.append(
                f'<circle cx="{x}" cy="{y}" r="{RAIO + 6}" fill="none" '
                f'stroke="{COR_DESTAQUE}" stroke-width="3"/>'
            )
        partes.append(f'<circle cx="{x}" cy="{y}" r="{RAIO}" fill="{cor}"/>')
        partes.append(
            f'<text x="{x}" y="{y + 4}" text-anchor="middle" font-size="{tamanho_fonte}" '
            f'font-weight="600" fill="#FFFFFF">{html.escape(texto)}</text>'
        )
        partes.append("</g>")

    partes.append("</svg>")
    return "".join(partes)
