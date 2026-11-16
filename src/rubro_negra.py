"""
Árvore Rubro-Negra (Red-Black Tree)
====================================

Árvore binária de busca auto-balanceada. Cada nó tem uma cor (vermelho
ou preto) e a árvore mantém, após cada inserção e remoção, as
seguintes propriedades:

    1. Todo nó é vermelho ou preto.
    2. A raiz é preta.
    3. Todo nó NIL (folha vazia) é preto.
    4. Um nó vermelho nunca tem filho vermelho.
    5. Todo caminho de um nó até suas folhas NIL passa pela mesma
       quantidade de nós pretos (altura negra).

Dessas propriedades decorre que a altura da árvore é, no máximo,
2 * log2(n + 1) (medida em arestas), garantindo busca, inserção e
remoção em O(log n) no pior caso.

Implementação baseada no pseudocódigo do livro CLRS (Cormen et al.,
"Introduction to Algorithms", capítulo 13), adaptada para Python.
Usa um nó sentinela único (NIL) para representar todas as folhas
vazias, como no livro.

Extensões para uso em aplicações (além do CLRS):
    - cada nó guarda, junto da chave, um `valor` associado;
    - consultas de vizinhança (piso, predecessor, sucessor) e consulta
      por faixa, todas em O(log n) (+ k para os k itens da faixa);
    - contador `visitas` de nós percorridos, para medir o custo real
      das consultas.

Complexidades (pior caso):
    buscar / piso / predecessor / sucessor   O(log n)
    faixa                                    O(log n + k)
    inserir                                  O(log n), no máx. 2 rotações
    remover                                  O(log n), no máx. 3 rotações
"""

from typing import Any, List, Optional, Tuple

VERMELHO = True
PRETO = False


class No:
    """Nó da árvore rubro-negra."""

    __slots__ = ("chave", "valor", "cor", "esq", "dir", "pai")

    def __init__(
        self,
        chave: Any,
        cor: bool,
        nil: Optional["No"] = None,
        valor: Any = None,
    ):
        self.chave = chave
        self.valor = valor
        self.cor = cor
        self.esq = nil
        self.dir = nil
        self.pai = nil


class ArvoreRubroNegra:
    """Árvore rubro-negra de chaves comparáveis, sem chaves repetidas."""

    def __init__(self) -> None:
        # Sentinela: representa todas as folhas vazias (sempre preta).
        self.NIL = No(None, PRETO)
        self.NIL.esq = self.NIL.dir = self.NIL.pai = self.NIL

        self.raiz: No = self.NIL
        self.tamanho: int = 0

        # Contador de rotações realizadas (usado nos experimentos).
        self.rotacoes: int = 0

        # Contador acumulado de nós visitados em buscas e consultas.
        self.visitas: int = 0

    # ------------------------------------------------------------------
    # Rotações
    # ------------------------------------------------------------------

    def _rotacao_esquerda(self, x: No) -> None:
        """
              x                 y
             / \\               / \\
            a   y      ->      x   c
               / \\            / \\
              b   c          a   b
        """
        y = x.dir
        x.dir = y.esq
        if y.esq is not self.NIL:
            y.esq.pai = x

        y.pai = x.pai
        if x.pai is self.NIL:
            self.raiz = y
        elif x is x.pai.esq:
            x.pai.esq = y
        else:
            x.pai.dir = y

        y.esq = x
        x.pai = y
        self.rotacoes += 1

    def _rotacao_direita(self, x: No) -> None:
        """
                x             y
               / \\           / \\
              y   c   ->    a   x
             / \\               / \\
            a   b             b   c
        """
        y = x.esq
        x.esq = y.dir
        if y.dir is not self.NIL:
            y.dir.pai = x

        y.pai = x.pai
        if x.pai is self.NIL:
            self.raiz = y
        elif x is x.pai.dir:
            x.pai.dir = y
        else:
            x.pai.esq = y

        y.dir = x
        x.pai = y
        self.rotacoes += 1

    # ------------------------------------------------------------------
    # Busca
    # ------------------------------------------------------------------

    def buscar(self, chave: Any) -> Tuple[bool, int]:
        """
        Busca uma chave na árvore.

        Retorna (encontrado, comparacoes), onde `comparacoes` é a
        quantidade de nós visitados durante a descida.
        """
        no = self.raiz
        comparacoes = 0

        while no is not self.NIL:
            comparacoes += 1
            self.visitas += 1
            if chave == no.chave:
                return True, comparacoes
            no = no.esq if chave < no.chave else no.dir

        return False, comparacoes

    def _buscar_no(self, chave: Any) -> No:
        no = self.raiz
        while no is not self.NIL:
            if chave == no.chave:
                return no
            no = no.esq if chave < no.chave else no.dir
        return self.NIL

    def __contains__(self, chave: Any) -> bool:
        return self._buscar_no(chave) is not self.NIL

    def __len__(self) -> int:
        return self.tamanho

    # ------------------------------------------------------------------
    # Inserção
    # ------------------------------------------------------------------

    def inserir(self, chave: Any, valor: Any = None) -> bool:
        """
        Insere uma chave (com um valor opcional associado). Retorna
        False (sem alterar a árvore) se a chave já existir, e True
        caso contrário.
        """
        pai = self.NIL
        atual = self.raiz

        while atual is not self.NIL:
            pai = atual
            if chave == atual.chave:
                return False
            atual = atual.esq if chave < atual.chave else atual.dir

        # Todo nó novo entra vermelho: isso não altera a altura negra.
        novo = No(chave, VERMELHO, self.NIL, valor)
        novo.pai = pai

        if pai is self.NIL:
            self.raiz = novo
        elif chave < pai.chave:
            pai.esq = novo
        else:
            pai.dir = novo

        self.tamanho += 1
        self._corrigir_insercao(novo)
        return True

    def _corrigir_insercao(self, z: No) -> None:
        """
        Restaura as propriedades após inserir `z` (vermelho). A única
        propriedade que pode estar violada é a 4 (vermelho com filho
        vermelho). Três casos, olhando o "tio" de z:

            Caso 1: tio vermelho  -> recolore pai, tio e avô; sobe.
            Caso 2: tio preto, z é filho "interno" -> rotação para
                    transformar no caso 3.
            Caso 3: tio preto, z é filho "externo" -> recolore e faz
                    uma rotação no avô. Termina.
        """
        while z.pai.cor == VERMELHO:
            if z.pai is z.pai.pai.esq:
                tio = z.pai.pai.dir

                if tio.cor == VERMELHO:                      # caso 1
                    z.pai.cor = PRETO
                    tio.cor = PRETO
                    z.pai.pai.cor = VERMELHO
                    z = z.pai.pai
                else:
                    if z is z.pai.dir:                       # caso 2
                        z = z.pai
                        self._rotacao_esquerda(z)
                    z.pai.cor = PRETO                        # caso 3
                    z.pai.pai.cor = VERMELHO
                    self._rotacao_direita(z.pai.pai)
            else:
                tio = z.pai.pai.esq

                if tio.cor == VERMELHO:                      # caso 1
                    z.pai.cor = PRETO
                    tio.cor = PRETO
                    z.pai.pai.cor = VERMELHO
                    z = z.pai.pai
                else:
                    if z is z.pai.esq:                       # caso 2
                        z = z.pai
                        self._rotacao_direita(z)
                    z.pai.cor = PRETO                        # caso 3
                    z.pai.pai.cor = VERMELHO
                    self._rotacao_esquerda(z.pai.pai)

        self.raiz.cor = PRETO

    # ------------------------------------------------------------------
    # Remoção
    # ------------------------------------------------------------------

    def _transplantar(self, u: No, v: No) -> None:
        """Substitui a subárvore com raiz em `u` pela subárvore em `v`."""
        if u.pai is self.NIL:
            self.raiz = v
        elif u is u.pai.esq:
            u.pai.esq = v
        else:
            u.pai.dir = v
        v.pai = u.pai

    def _minimo_no(self, no: No) -> No:
        while no.esq is not self.NIL:
            no = no.esq
        return no

    def _maximo_no(self, no: No) -> No:
        while no.dir is not self.NIL:
            no = no.dir
        return no

    def remover(self, chave: Any) -> bool:
        """Remove uma chave. Retorna False se ela não existir."""
        z = self._buscar_no(chave)
        if z is self.NIL:
            return False

        y = z
        cor_original_y = y.cor

        if z.esq is self.NIL:
            x = z.dir
            self._transplantar(z, z.dir)
        elif z.dir is self.NIL:
            x = z.esq
            self._transplantar(z, z.esq)
        else:
            # Dois filhos: o sucessor (menor da subárvore direita)
            # ocupa o lugar de z e herda sua cor.
            y = self._minimo_no(z.dir)
            cor_original_y = y.cor
            x = y.dir

            if y.pai is z:
                x.pai = y
            else:
                self._transplantar(y, y.dir)
                y.dir = z.dir
                y.dir.pai = y

            self._transplantar(z, y)
            y.esq = z.esq
            y.esq.pai = y
            y.cor = z.cor

        self.tamanho -= 1

        # Se o nó efetivamente removido era preto, a altura negra de
        # alguns caminhos diminuiu e é preciso corrigir.
        if cor_original_y == PRETO:
            self._corrigir_remocao(x)

        return True

    def _corrigir_remocao(self, x: No) -> None:
        """
        Restaura as propriedades após remover um nó preto. `x` carrega
        um "preto extra". Quatro casos, olhando o irmão `w` de x:

            Caso 1: w vermelho -> rotação transforma em caso 2, 3 ou 4.
            Caso 2: w preto, sobrinhos pretos -> recolore w; sobe.
            Caso 3: w preto, sobrinho "distante" preto e o "próximo"
                    vermelho -> rotação em w, vira caso 4.
            Caso 4: w preto, sobrinho distante vermelho -> recolore e
                    rotaciona o pai. Termina.
        """
        while x is not self.raiz and x.cor == PRETO:
            if x is x.pai.esq:
                w = x.pai.dir

                if w.cor == VERMELHO:                        # caso 1
                    w.cor = PRETO
                    x.pai.cor = VERMELHO
                    self._rotacao_esquerda(x.pai)
                    w = x.pai.dir

                if w.esq.cor == PRETO and w.dir.cor == PRETO:  # caso 2
                    w.cor = VERMELHO
                    x = x.pai
                else:
                    if w.dir.cor == PRETO:                   # caso 3
                        w.esq.cor = PRETO
                        w.cor = VERMELHO
                        self._rotacao_direita(w)
                        w = x.pai.dir
                    w.cor = x.pai.cor                        # caso 4
                    x.pai.cor = PRETO
                    w.dir.cor = PRETO
                    self._rotacao_esquerda(x.pai)
                    x = self.raiz
            else:
                w = x.pai.esq

                if w.cor == VERMELHO:                        # caso 1
                    w.cor = PRETO
                    x.pai.cor = VERMELHO
                    self._rotacao_direita(x.pai)
                    w = x.pai.esq

                if w.dir.cor == PRETO and w.esq.cor == PRETO:  # caso 2
                    w.cor = VERMELHO
                    x = x.pai
                else:
                    if w.esq.cor == PRETO:                   # caso 3
                        w.dir.cor = PRETO
                        w.cor = VERMELHO
                        self._rotacao_esquerda(w)
                        w = x.pai.esq
                    w.cor = x.pai.cor                        # caso 4
                    x.pai.cor = PRETO
                    w.esq.cor = PRETO
                    self._rotacao_direita(x.pai)
                    x = self.raiz

        x.cor = PRETO

    # ------------------------------------------------------------------
    # Consultas de vizinhança e por faixa
    # ------------------------------------------------------------------

    def obter(self, chave: Any, padrao: Any = None) -> Any:
        """Valor associado à chave (ou `padrao` se ela não existir)."""
        no = self._buscar_no(chave)
        return padrao if no is self.NIL else no.valor

    def piso(self, chave: Any) -> Optional[Tuple[Any, Any]]:
        """Maior chave MENOR OU IGUAL a `chave`, como (chave, valor)."""
        return self._vizinho_anterior(chave, inclusivo=True)

    def predecessor(self, chave: Any) -> Optional[Tuple[Any, Any]]:
        """Maior chave ESTRITAMENTE menor que `chave`."""
        return self._vizinho_anterior(chave, inclusivo=False)

    def _vizinho_anterior(self, chave: Any, inclusivo: bool):
        no = self.raiz
        melhor = None

        while no is not self.NIL:
            self.visitas += 1
            if no.chave < chave or (inclusivo and no.chave == chave):
                melhor = no
                if no.chave == chave:
                    break
                no = no.dir
            else:
                no = no.esq

        return None if melhor is None else (melhor.chave, melhor.valor)

    def sucessor(self, chave: Any) -> Optional[Tuple[Any, Any]]:
        """Menor chave ESTRITAMENTE maior que `chave`, como (chave, valor)."""
        no = self.raiz
        melhor = None

        while no is not self.NIL:
            self.visitas += 1
            if no.chave > chave:
                melhor = no
                no = no.esq
            else:
                no = no.dir

        return None if melhor is None else (melhor.chave, melhor.valor)

    def faixa(
        self, minimo: Any, maximo: Any, incluir_maximo: bool = False
    ) -> List[Tuple[Any, Any]]:
        """
        Itens (chave, valor), em ordem crescente, com
        minimo <= chave < maximo (ou <= maximo, se `incluir_maximo`).
        Só desce pelos ramos que podem conter chaves da faixa:
        O(log n + k), onde k é a quantidade de itens devolvidos.
        """
        resultado: List[Tuple[Any, Any]] = []

        def visitar(no: No) -> None:
            if no is self.NIL:
                return
            self.visitas += 1

            if no.chave > minimo:
                visitar(no.esq)

            dentro_do_fim = no.chave < maximo or (incluir_maximo and no.chave == maximo)
            if no.chave >= minimo and dentro_do_fim:
                resultado.append((no.chave, no.valor))

            if no.chave < maximo:
                visitar(no.dir)

        visitar(self.raiz)
        return resultado

    def itens(self) -> List[Tuple[Any, Any]]:
        """Todos os (chave, valor) em ordem crescente de chave."""
        resultado: List[Tuple[Any, Any]] = []

        def visitar(no: No) -> None:
            if no is self.NIL:
                return
            visitar(no.esq)
            resultado.append((no.chave, no.valor))
            visitar(no.dir)

        visitar(self.raiz)
        return resultado

    # ------------------------------------------------------------------
    # Consultas e percursos
    # ------------------------------------------------------------------

    def minimo(self) -> Optional[Any]:
        if self.raiz is self.NIL:
            return None
        return self._minimo_no(self.raiz).chave

    def maximo(self) -> Optional[Any]:
        if self.raiz is self.NIL:
            return None
        return self._maximo_no(self.raiz).chave

    def em_ordem(self) -> List[Any]:
        """Chaves em ordem crescente (percurso em-ordem)."""
        resultado: List[Any] = []

        def visitar(no: No) -> None:
            if no is self.NIL:
                return
            visitar(no.esq)
            resultado.append(no.chave)
            visitar(no.dir)

        visitar(self.raiz)
        return resultado

    def altura(self) -> int:
        """Altura em níveis (árvore vazia = 0, só a raiz = 1)."""

        def calcular(no: No) -> int:
            if no is self.NIL:
                return 0
            return 1 + max(calcular(no.esq), calcular(no.dir))

        return calcular(self.raiz)

    def altura_negra(self) -> int:
        """Quantidade de nós pretos em qualquer caminho raiz -> folha."""
        no = self.raiz
        altura = 0
        while no is not self.NIL:
            if no.cor == PRETO:
                altura += 1
            no = no.esq
        return altura

    # ------------------------------------------------------------------
    # Validação das propriedades
    # ------------------------------------------------------------------

    def validar(self) -> List[str]:
        """
        Verifica todas as propriedades da árvore rubro-negra (e a
        ordem de árvore binária de busca). Retorna a lista de
        violações encontradas; lista vazia significa árvore válida.
        """
        erros: List[str] = []

        if self.NIL.cor != PRETO:
            erros.append("O nó NIL não é preto (propriedade 3).")
        if self.raiz.cor != PRETO:
            erros.append("A raiz não é preta (propriedade 2).")
        if self.raiz is not self.NIL and self.raiz.pai is not self.NIL:
            erros.append("O pai da raiz deveria ser NIL.")

        def percorrer(no: No, minimo: Any, maximo: Any) -> int:
            """Retorna a altura negra da subárvore (NIL conta 1)."""
            if no is self.NIL:
                return 1

            if (minimo is not None and no.chave <= minimo) or (
                maximo is not None and no.chave >= maximo
            ):
                erros.append(f"Ordem BST violada no nó {no.chave}.")

            if no.cor == VERMELHO and (
                no.esq.cor == VERMELHO or no.dir.cor == VERMELHO
            ):
                erros.append(
                    f"Nó vermelho {no.chave} tem filho vermelho (propriedade 4)."
                )

            if no.esq is not self.NIL and no.esq.pai is not no:
                erros.append(f"Ponteiro pai inconsistente à esquerda de {no.chave}.")
            if no.dir is not self.NIL and no.dir.pai is not no:
                erros.append(f"Ponteiro pai inconsistente à direita de {no.chave}.")

            h_esq = percorrer(no.esq, minimo, no.chave)
            h_dir = percorrer(no.dir, no.chave, maximo)

            if h_esq != h_dir:
                erros.append(
                    f"Alturas negras diferentes sob o nó {no.chave} "
                    f"({h_esq} x {h_dir}) (propriedade 5)."
                )

            return h_esq + (1 if no.cor == PRETO else 0)

        percorrer(self.raiz, None, None)

        if len(self.em_ordem()) != self.tamanho:
            erros.append("O tamanho registrado não bate com a quantidade de nós.")

        return erros

    # ------------------------------------------------------------------
    # Representação textual
    # ------------------------------------------------------------------

    def desenhar(self) -> str:
        """
        Desenha a árvore "deitada" (raiz à esquerda, subárvore direita
        em cima). (V) = vermelho, (P) = preto.
        """
        if self.raiz is self.NIL:
            return "(árvore vazia)"

        linhas: List[str] = []

        def visitar(no: No, nivel: int) -> None:
            if no is self.NIL:
                return
            visitar(no.dir, nivel + 1)
            cor = "V" if no.cor == VERMELHO else "P"
            linhas.append("      " * nivel + f"{no.chave}({cor})")
            visitar(no.esq, nivel + 1)

        visitar(self.raiz, 0)
        return "\n".join(linhas)
