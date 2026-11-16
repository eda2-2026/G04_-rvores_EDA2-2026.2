"""
Testes automatizados da árvore rubro-negra.

Executar (não precisa instalar nada):
    python -m unittest discover -s tests -v

Também funciona com pytest:
    pytest tests/
"""

import math
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rubro_negra import ArvoreRubroNegra, PRETO, VERMELHO


def limite_altura(n: int) -> float:
    """Limite teórico de níveis: 2*log2(n+1) arestas => +1 em níveis."""
    return 2 * math.log2(n + 1) + 1


class TestArvoreVazia(unittest.TestCase):
    def test_arvore_vazia(self):
        arv = ArvoreRubroNegra()
        self.assertEqual(len(arv), 0)
        self.assertEqual(arv.em_ordem(), [])
        self.assertEqual(arv.altura(), 0)
        self.assertIsNone(arv.minimo())
        self.assertIsNone(arv.maximo())
        self.assertEqual(arv.validar(), [])

    def test_buscar_em_arvore_vazia(self):
        encontrado, comparacoes = ArvoreRubroNegra().buscar(10)
        self.assertFalse(encontrado)
        self.assertEqual(comparacoes, 0)

    def test_remover_de_arvore_vazia(self):
        self.assertFalse(ArvoreRubroNegra().remover(10))


class TestInsercao(unittest.TestCase):
    def test_um_elemento_raiz_preta(self):
        arv = ArvoreRubroNegra()
        self.assertTrue(arv.inserir(10))
        self.assertEqual(arv.raiz.cor, PRETO)
        self.assertEqual(len(arv), 1)
        self.assertEqual(arv.validar(), [])

    def test_tres_chaves_crescentes_forcam_rotacao(self):
        """10, 20, 30 degeneraria em lista; a rotação deixa 20 na raiz."""
        arv = ArvoreRubroNegra()
        for chave in (10, 20, 30):
            arv.inserir(chave)

        self.assertEqual(arv.raiz.chave, 20)
        self.assertEqual(arv.raiz.cor, PRETO)
        self.assertEqual(arv.raiz.esq.chave, 10)
        self.assertEqual(arv.raiz.esq.cor, VERMELHO)
        self.assertEqual(arv.raiz.dir.chave, 30)
        self.assertEqual(arv.raiz.dir.cor, VERMELHO)
        self.assertEqual(arv.rotacoes, 1)
        self.assertEqual(arv.validar(), [])

    def test_recoloracao_sem_rotacao(self):
        """Pai e tio vermelhos: só recolore (caso 1)."""
        arv = ArvoreRubroNegra()
        for chave in (20, 10, 30):
            arv.inserir(chave)
        rotacoes_antes = arv.rotacoes

        arv.inserir(5)

        self.assertEqual(arv.rotacoes, rotacoes_antes)
        self.assertEqual(arv.raiz.esq.cor, PRETO)
        self.assertEqual(arv.raiz.dir.cor, PRETO)
        self.assertEqual(arv.validar(), [])

    def test_chave_repetida_e_ignorada(self):
        arv = ArvoreRubroNegra()
        self.assertTrue(arv.inserir(7))
        self.assertFalse(arv.inserir(7))
        self.assertEqual(len(arv), 1)
        self.assertEqual(arv.em_ordem(), [7])

    def test_em_ordem_fica_ordenado(self):
        arv = ArvoreRubroNegra()
        chaves = [41, 38, 31, 12, 19, 8, 50, 45, 1, 99]
        for chave in chaves:
            arv.inserir(chave)
        self.assertEqual(arv.em_ordem(), sorted(chaves))
        self.assertEqual(arv.minimo(), 1)
        self.assertEqual(arv.maximo(), 99)

    def test_insercao_crescente_mantem_propriedades_e_altura(self):
        arv = ArvoreRubroNegra()
        n = 5000
        for chave in range(1, n + 1):
            arv.inserir(chave)
            if chave % 250 == 0:
                self.assertEqual(arv.validar(), [])

        self.assertEqual(len(arv), n)
        self.assertLessEqual(arv.altura(), limite_altura(n))

    def test_insercao_decrescente_mantem_propriedades_e_altura(self):
        arv = ArvoreRubroNegra()
        n = 5000
        for chave in range(n, 0, -1):
            arv.inserir(chave)

        self.assertEqual(arv.validar(), [])
        self.assertLessEqual(arv.altura(), limite_altura(n))

    def test_validar_em_cada_passo_com_chaves_aleatorias(self):
        rng = random.Random(42)
        arv = ArvoreRubroNegra()
        for chave in rng.sample(range(10_000), 600):
            arv.inserir(chave)
            self.assertEqual(arv.validar(), [])


class TestBusca(unittest.TestCase):
    def setUp(self):
        self.arv = ArvoreRubroNegra()
        for chave in (50, 20, 70, 10, 30, 60, 80):
            self.arv.inserir(chave)

    def test_busca_existente(self):
        encontrado, comparacoes = self.arv.buscar(30)
        self.assertTrue(encontrado)
        self.assertGreaterEqual(comparacoes, 1)

    def test_busca_inexistente(self):
        encontrado, _ = self.arv.buscar(35)
        self.assertFalse(encontrado)

    def test_operador_in(self):
        self.assertIn(60, self.arv)
        self.assertNotIn(61, self.arv)

    def test_comparacoes_limitadas_pela_altura(self):
        _, comparacoes = self.arv.buscar(80)
        self.assertLessEqual(comparacoes, self.arv.altura())


class TestRemocao(unittest.TestCase):
    def _arvore(self, chaves):
        arv = ArvoreRubroNegra()
        for chave in chaves:
            arv.inserir(chave)
        return arv

    def test_remover_inexistente(self):
        arv = self._arvore([1, 2, 3])
        self.assertFalse(arv.remover(99))
        self.assertEqual(len(arv), 3)

    def test_remover_unico_elemento(self):
        arv = self._arvore([5])
        self.assertTrue(arv.remover(5))
        self.assertEqual(len(arv), 0)
        self.assertEqual(arv.em_ordem(), [])
        self.assertEqual(arv.validar(), [])

    def test_remover_folha_vermelha(self):
        arv = self._arvore([20, 10, 30])
        self.assertTrue(arv.remover(10))
        self.assertEqual(arv.em_ordem(), [20, 30])
        self.assertEqual(arv.validar(), [])

    def test_remover_raiz_com_dois_filhos(self):
        arv = self._arvore([20, 10, 30, 5, 15, 25, 35])
        self.assertTrue(arv.remover(20))
        self.assertEqual(arv.em_ordem(), [5, 10, 15, 25, 30, 35])
        self.assertEqual(arv.validar(), [])

    def test_remover_todos_em_ordem_crescente(self):
        chaves = list(range(1, 201))
        arv = self._arvore(chaves)
        for chave in chaves:
            self.assertTrue(arv.remover(chave))
            self.assertEqual(arv.validar(), [])
        self.assertEqual(len(arv), 0)

    def test_remover_todos_em_ordem_aleatoria(self):
        rng = random.Random(7)
        chaves = list(range(1, 301))
        arv = self._arvore(chaves)
        rng.shuffle(chaves)
        for chave in chaves:
            self.assertTrue(arv.remover(chave))
            self.assertEqual(arv.validar(), [])
        self.assertEqual(len(arv), 0)

    def test_inserir_depois_de_esvaziar(self):
        arv = self._arvore([1, 2, 3])
        for chave in (1, 2, 3):
            arv.remover(chave)
        arv.inserir(42)
        self.assertEqual(arv.em_ordem(), [42])
        self.assertEqual(arv.raiz.cor, PRETO)
        self.assertEqual(arv.validar(), [])


class TestContraUmOraculo(unittest.TestCase):
    """Compara a árvore com o `set` do Python em operações aleatórias."""

    def test_operacoes_aleatorias_misturadas(self):
        rng = random.Random(2026)
        arv = ArvoreRubroNegra()
        oraculo = set()

        for passo in range(4000):
            chave = rng.randint(0, 400)
            operacao = rng.choice(("inserir", "inserir", "remover", "buscar"))

            if operacao == "inserir":
                self.assertEqual(arv.inserir(chave), chave not in oraculo)
                oraculo.add(chave)
            elif operacao == "remover":
                self.assertEqual(arv.remover(chave), chave in oraculo)
                oraculo.discard(chave)
            else:
                self.assertEqual(arv.buscar(chave)[0], chave in oraculo)

            if passo % 20 == 0:
                self.assertEqual(arv.validar(), [])
                self.assertEqual(arv.em_ordem(), sorted(oraculo))
                self.assertEqual(len(arv), len(oraculo))

        self.assertEqual(arv.validar(), [])
        self.assertEqual(arv.em_ordem(), sorted(oraculo))


class TestValidador(unittest.TestCase):
    """Garante que o validador realmente detecta árvores inválidas."""

    def test_detecta_raiz_vermelha(self):
        arv = ArvoreRubroNegra()
        for chave in (20, 10, 30):
            arv.inserir(chave)
        arv.raiz.cor = VERMELHO
        self.assertTrue(arv.validar())

    def test_detecta_vermelho_com_filho_vermelho(self):
        arv = ArvoreRubroNegra()
        for chave in (20, 10, 30, 5):
            arv.inserir(chave)
        arv.raiz.esq.cor = VERMELHO   # 10 vermelho com filho 5 vermelho
        self.assertTrue(arv.validar())

    def test_detecta_alturas_negras_diferentes(self):
        arv = ArvoreRubroNegra()
        for chave in (20, 10, 30):
            arv.inserir(chave)
        arv.raiz.esq.cor = PRETO      # só o lado esquerdo ganha um preto
        self.assertTrue(arv.validar())


class TestValorEConsultasDeVizinhanca(unittest.TestCase):
    """Valor associado à chave, piso/predecessor/sucessor e faixa."""

    def _arvore(self, chaves):
        arv = ArvoreRubroNegra()
        for chave in chaves:
            arv.inserir(chave, f"v{chave}")
        return arv

    def test_valor_associado_a_chave(self):
        arv = self._arvore([10, 20, 30])
        self.assertEqual(arv.obter(20), "v20")
        self.assertIsNone(arv.obter(25))
        self.assertEqual(arv.obter(25, "nada"), "nada")

    def test_valor_acompanha_a_chave_apos_remocoes(self):
        """A remoção religa nós (sucessor assume o lugar): valores não podem se perder."""
        chaves = list(range(1, 200))
        arv = self._arvore(chaves)
        for chave in range(1, 200, 3):
            arv.remover(chave)
        for chave, valor in arv.itens():
            self.assertEqual(valor, f"v{chave}")
        self.assertEqual(arv.validar(), [])

    def test_casos_simples(self):
        arv = self._arvore([10, 20, 30, 40, 50])
        self.assertEqual(arv.piso(25), (20, "v20"))
        self.assertEqual(arv.piso(30), (30, "v30"))
        self.assertIsNone(arv.piso(5))
        self.assertEqual(arv.predecessor(30), (20, "v20"))
        self.assertIsNone(arv.predecessor(10))
        self.assertEqual(arv.sucessor(30), (40, "v40"))
        self.assertEqual(arv.sucessor(25), (30, "v30"))
        self.assertIsNone(arv.sucessor(50))

    def test_faixa_com_e_sem_limite_superior(self):
        arv = self._arvore([10, 20, 30, 40, 50])
        self.assertEqual([c for c, _ in arv.faixa(20, 40)], [20, 30])
        self.assertEqual([c for c, _ in arv.faixa(20, 40, incluir_maximo=True)], [20, 30, 40])
        self.assertEqual(arv.faixa(41, 49), [])
        self.assertEqual(arv.faixa(0, 1000), arv.itens())

    def test_consultas_em_arvore_vazia(self):
        arv = ArvoreRubroNegra()
        self.assertIsNone(arv.piso(1))
        self.assertIsNone(arv.predecessor(1))
        self.assertIsNone(arv.sucessor(1))
        self.assertEqual(arv.faixa(0, 10), [])

    def test_contra_resposta_ingenua_com_chaves_aleatorias(self):
        rng = random.Random(99)
        chaves = rng.sample(range(0, 2000, 2), 300)   # só pares: sobram ímpares ausentes
        arv = self._arvore(chaves)
        ordenadas = sorted(chaves)

        for consulta in range(-3, 2005, 7):
            menores_iguais = [c for c in ordenadas if c <= consulta]
            menores = [c for c in ordenadas if c < consulta]
            maiores = [c for c in ordenadas if c > consulta]

            esperado_piso = menores_iguais[-1] if menores_iguais else None
            esperado_pred = menores[-1] if menores else None
            esperado_suc = maiores[0] if maiores else None

            self.assertEqual((arv.piso(consulta) or (None,))[0], esperado_piso)
            self.assertEqual((arv.predecessor(consulta) or (None,))[0], esperado_pred)
            self.assertEqual((arv.sucessor(consulta) or (None,))[0], esperado_suc)

        for _ in range(200):
            a, b = sorted((rng.randint(-10, 2010), rng.randint(-10, 2010)))
            esperado = [c for c in ordenadas if a <= c < b]
            self.assertEqual([c for c, _ in arv.faixa(a, b)], esperado)
            esperado_inc = [c for c in ordenadas if a <= c <= b]
            self.assertEqual([c for c, _ in arv.faixa(a, b, True)], esperado_inc)

    def test_consulta_visita_no_maximo_a_altura(self):
        arv = self._arvore(range(1, 5001))
        antes = arv.visitas
        arv.sucessor(2500)
        self.assertLessEqual(arv.visitas - antes, arv.altura())

        antes = arv.visitas
        arv.piso(2500)
        self.assertLessEqual(arv.visitas - antes, arv.altura())


if __name__ == "__main__":
    unittest.main()
