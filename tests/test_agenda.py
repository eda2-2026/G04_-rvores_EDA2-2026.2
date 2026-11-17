
import os
import random
import sys
import unittest
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agenda import (
    Agenda,
    ConflitoDeHorario,
    DadosInvalidos,
    HorarioInvalido,
    ReservaNaoEncontrada,
    SalaNaoEncontrada,
)

DIA = date(2026, 11, 20)


def h(hora, minuto=0, dia=DIA):
    return datetime(dia.year, dia.month, dia.day, hora, minuto)


def nova_agenda():
    agenda = Agenda()
    agenda.adicionar_sala("Sala 101", 40, "sala")
    agenda.adicionar_sala("Lab 1", 25, "laboratorio")
    return agenda


class TestReservasESalas(unittest.TestCase):
    def test_reserva_simples(self):
        agenda = nova_agenda()
        reserva, custo = agenda.reservar(1, "Aula", "Prof. A", h(8), h(10))
        self.assertEqual(reserva.id, 1)
        self.assertEqual(agenda.reservas_do_dia(1, DIA), [reserva])
        self.assertEqual(custo["reservas_na_sala"], 0)

    def test_sala_inexistente(self):
        with self.assertRaises(SalaNaoEncontrada):
            nova_agenda().reservar(99, "Aula", "Prof. A", h(8), h(10))

    def test_campos_obrigatorios(self):
        agenda = nova_agenda()
        with self.assertRaises(DadosInvalidos):
            agenda.reservar(1, "  ", "Prof. A", h(8), h(10))
        with self.assertRaises(DadosInvalidos):
            agenda.reservar(1, "Aula", "", h(8), h(10))

    def test_sala_com_dados_invalidos(self):
        agenda = nova_agenda()
        with self.assertRaises(DadosInvalidos):
            agenda.adicionar_sala("", 10)
        with self.assertRaises(DadosInvalidos):
            agenda.adicionar_sala("Sala X", 0)
        with self.assertRaises(DadosInvalidos):
            agenda.adicionar_sala("Sala X", 10, "quadra")
        with self.assertRaises(DadosInvalidos):
            agenda.adicionar_sala("sala 101", 10)


class TestValidacaoDeHorario(unittest.TestCase):
    def test_fim_antes_ou_igual_ao_inicio(self):
        agenda = nova_agenda()
        with self.assertRaises(HorarioInvalido):
            agenda.reservar(1, "Aula", "A", h(10), h(10))
        with self.assertRaises(HorarioInvalido):
            agenda.reservar(1, "Aula", "A", h(10), h(9))

    def test_dias_diferentes(self):
        agenda = nova_agenda()
        with self.assertRaises(HorarioInvalido):
            agenda.reservar(1, "Aula", "A", h(20), h(21, dia=DIA + timedelta(days=1)))

    def test_fora_do_horario_de_funcionamento(self):
        agenda = nova_agenda()
        with self.assertRaises(HorarioInvalido):
            agenda.reservar(1, "Aula", "A", h(6, 30), h(8))
        with self.assertRaises(HorarioInvalido):
            agenda.reservar(1, "Aula", "A", h(21), h(22, 30))

    def test_limites_do_horario_sao_aceitos(self):
        agenda = nova_agenda()
        agenda.reservar(1, "Manhã", "A", h(7), h(8))
        agenda.reservar(1, "Noite", "A", h(21), h(22))
        self.assertEqual(len(agenda.reservas_do_dia(1, DIA)), 2)


class TestDeteccaoDeConflito(unittest.TestCase):
    def setUp(self):
        self.agenda = nova_agenda()
        self.agenda.reservar(1, "Existente", "A", h(10), h(12))

    def _deve_conflitar(self, inicio, fim):
        with self.assertRaises(ConflitoDeHorario) as contexto:
            self.agenda.reservar(1, "Nova", "B", inicio, fim)
        self.assertEqual(contexto.exception.conflito.titulo, "Existente")

    def test_sobreposicao_no_comeco(self):
        self._deve_conflitar(h(9), h(10, 30))

    def test_sobreposicao_no_fim(self):
        self._deve_conflitar(h(11, 30), h(13))

    def test_nova_contida_na_existente(self):
        self._deve_conflitar(h(10, 30), h(11, 30))

    def test_nova_contem_a_existente(self):
        self._deve_conflitar(h(9), h(13))

    def test_mesmo_horario_exato(self):
        self._deve_conflitar(h(10), h(12))

    def test_mesmo_inicio_com_duracao_diferente(self):
        self._deve_conflitar(h(10), h(10, 30))

    def test_reservas_encostadas_sao_permitidas(self):
        self.agenda.reservar(1, "Antes", "B", h(9), h(10))
        self.agenda.reservar(1, "Depois", "B", h(12), h(13))
        self.assertEqual(len(self.agenda.reservas_do_dia(1, DIA)), 3)

    def test_conflito_so_com_vizinho_anterior_longo(self):
        agenda = nova_agenda()
        agenda.reservar(1, "Longa", "A", h(8), h(12))
        with self.assertRaises(ConflitoDeHorario) as contexto:
            agenda.reservar(1, "Nova", "B", h(11), h(11, 30))
        self.assertEqual(contexto.exception.conflito.titulo, "Longa")

    def test_salas_diferentes_nao_conflitam(self):
        self.agenda.reservar(2, "Mesmo horário, outra sala", "B", h(10), h(12))

    def test_dias_diferentes_nao_conflitam(self):
        outro_dia = DIA + timedelta(days=1)
        self.agenda.reservar(1, "Amanhã", "B", h(10, dia=outro_dia), h(12, dia=outro_dia))

    def test_conflito_nao_altera_a_agenda(self):
        with self.assertRaises(ConflitoDeHorario):
            self.agenda.reservar(1, "Nova", "B", h(11), h(13))
        self.assertEqual(len(self.agenda.reservas_do_dia(1, DIA)), 1)

    def test_resposta_do_conflito_traz_custo(self):
        with self.assertRaises(ConflitoDeHorario) as contexto:
            self.agenda.reservar(1, "Nova", "B", h(11), h(13))
        resposta = contexto.exception.para_resposta()
        self.assertIn("custo", resposta)
        self.assertEqual(resposta["conflito"]["titulo"], "Existente")


class TestCancelamento(unittest.TestCase):
    def test_cancelar_libera_o_horario(self):
        agenda = nova_agenda()
        reserva, _ = agenda.reservar(1, "Aula", "A", h(10), h(12))
        agenda.cancelar(reserva.id)
        self.assertEqual(agenda.reservas_do_dia(1, DIA), [])
        agenda.reservar(1, "Outra", "B", h(10), h(12))

    def test_cancelar_inexistente(self):
        with self.assertRaises(ReservaNaoEncontrada):
            nova_agenda().cancelar(42)

    def test_cancelar_duas_vezes(self):
        agenda = nova_agenda()
        reserva, _ = agenda.reservar(1, "Aula", "A", h(10), h(12))
        agenda.cancelar(reserva.id)
        with self.assertRaises(ReservaNaoEncontrada):
            agenda.cancelar(reserva.id)

    def test_arvore_continua_valida_apos_cancelamentos(self):
        agenda = nova_agenda()
        ids = []
        for dia in range(1, 29):
            reserva, _ = agenda.reservar(
                1, "Aula", "A",
                h(8, dia=date(2026, 11, dia)),
                h(9, dia=date(2026, 11, dia))
            )
            ids.append(reserva.id)
        for reserva_id in ids[::2]:
            agenda.cancelar(reserva_id)
        self.assertEqual(agenda.arvores[1].validar(), [])
        self.assertEqual(len(agenda.reservas), 14)


class TestHorariosLivres(unittest.TestCase):
    def setUp(self):
        self.agenda = nova_agenda()
        self.agenda.reservar(1, "A", "X", h(8), h(9))
        self.agenda.reservar(1, "B", "X", h(10), h(12))

    def test_intervalos_livres(self):
        livres = self.agenda.horarios_livres(1, DIA, 30)
        self.assertEqual(livres, [(h(7), h(8)), (h(9), h(10)), (h(12), h(22))])

    def test_filtra_por_duracao_minima(self):
        livres = self.agenda.horarios_livres(1, DIA, 90)
        self.assertEqual(livres, [(h(12), h(22))])

    def test_dia_sem_reservas_esta_todo_livre(self):
        outro = DIA + timedelta(days=3)
        self.assertEqual(
            self.agenda.horarios_livres(1, outro, 60),
            [(h(7, dia=outro), h(22, dia=outro))]
        )

    def test_duracao_invalida(self):
        with self.assertRaises(DadosInvalidos):
            self.agenda.horarios_livres(1, DIA, 0)


class TestSalasLivres(unittest.TestCase):
    def setUp(self):
        self.agenda = Agenda()
        self.agenda.adicionar_sala("Grande", 100, "auditorio")
        self.agenda.adicionar_sala("Média", 40, "sala")
        self.agenda.adicionar_sala("Pequena", 20, "sala")
        self.agenda.adicionar_sala("Lab", 25, "laboratorio")
        self.agenda.reservar(2, "Ocupa a Média", "X", h(10), h(12))

    def test_so_devolve_salas_livres_da_menor_para_a_maior(self):
        salas, custo = self.agenda.salas_livres(h(10), h(11))
        self.assertEqual([s.nome for s in salas], ["Pequena", "Lab", "Grande"])
        self.assertEqual(custo["salas_verificadas"], 4)

    def test_filtro_de_capacidade(self):
        salas, _ = self.agenda.salas_livres(h(10), h(11), capacidade_minima=30)
        self.assertEqual([s.nome for s in salas], ["Grande"])

    def test_filtro_de_tipo(self):
        salas, _ = self.agenda.salas_livres(h(10), h(11), tipo="laboratorio")
        self.assertEqual([s.nome for s in salas], ["Lab"])

    def test_todas_livres_em_outro_horario(self):
        salas, _ = self.agenda.salas_livres(h(14), h(15))
        self.assertEqual(len(salas), 4)

    def test_horario_invalido(self):
        with self.assertRaises(HorarioInvalido):
            self.agenda.salas_livres(h(11), h(10))


class TestProximaReserva(unittest.TestCase):
    def test_proxima_reserva(self):
        agenda = nova_agenda()
        agenda.reservar(1, "Primeira", "A", h(8), h(9))
        agenda.reservar(1, "Segunda", "A", h(14), h(15))
        self.assertEqual(agenda.proxima_reserva(1, h(9)).titulo, "Segunda")
        self.assertEqual(agenda.proxima_reserva(1, h(7)).titulo, "Primeira")
        self.assertIsNone(agenda.proxima_reserva(1, h(14)))


class TestPersistencia(unittest.TestCase):
    def test_ida_e_volta_em_dicionario(self):
        agenda = nova_agenda()
        agenda.reservar(1, "Aula", "A", h(8), h(10))
        agenda.reservar(2, "Lab", "B", h(14), h(16))
        copia = Agenda.de_dict(agenda.para_dict())

        self.assertEqual(copia.para_dict(), agenda.para_dict())
        with self.assertRaises(ConflitoDeHorario):
            copia.reservar(1, "Nova", "C", h(9), h(11))

    def test_ids_nao_sao_reaproveitados_apos_cancelar_a_ultima(self):
        agenda = nova_agenda()
        agenda.reservar(1, "A", "X", h(8), h(9))
        ultima, _ = agenda.reservar(1, "B", "X", h(10), h(11))
        agenda.cancelar(ultima.id)

        copia = Agenda.de_dict(agenda.para_dict())
        nova, _ = copia.reservar(1, "C", "X", h(12), h(13))
        self.assertGreater(nova.id, ultima.id)

    def test_dados_inconsistentes_sao_rejeitados(self):
        agenda = nova_agenda()
        agenda.reservar(1, "A", "X", h(8), h(10))
        dados = agenda.para_dict()
        dados["reservas"].append(
            {
                "id": 99,
                "sala_id": 1,
                "titulo": "Sobreposta",
                "responsavel": "Y",
                "inicio": "2026-11-20T09:00",
                "fim": "2026-11-20T11:00"
            }
        )
        with self.assertRaises(ValueError):
            Agenda.de_dict(dados)


class TestContraForcaBruta(unittest.TestCase):
    def test_decisoes_identicas_a_varredura_completa(self):
        rng = random.Random(2026)
        agenda = Agenda()
        agenda.adicionar_sala("Sala", 30)
        ativas = {}

        for passo in range(4000):
            if ativas and rng.random() < 0.25:
                reserva_id = rng.choice(list(ativas))
                agenda.cancelar(reserva_id)
                del ativas[reserva_id]
                continue

            dia = DIA + timedelta(days=rng.randint(0, 6))
            inicio = h(7, dia=dia) + timedelta(minutes=rng.randrange(0, 14 * 60, 15))
            fim = inicio + timedelta(minutes=rng.choice((15, 30, 60, 90, 120)))
            if fim.time() > h(22).time() or fim.date() != inicio.date():
                continue

            tem_conflito = any(i < fim and f > inicio for i, f in ativas.values())

            try:
                reserva, _ = agenda.reservar(1, "Teste", "Y", inicio, fim)
            except ConflitoDeHorario as erro:
                self.assertTrue(tem_conflito, f"passo {passo}: recusou sem haver conflito")
                c = erro.conflito
                self.assertTrue(c.inicio < fim and c.fim > inicio, "conflito apontado não sobrepõe")
            else:
                self.assertFalse(tem_conflito, f"passo {passo}: aceitou havendo conflito")
                ativas[reserva.id] = (inicio, fim)

            if passo % 200 == 0:
                self.assertEqual(agenda.arvores[1].validar(), [])

        self.assertEqual(len(agenda.reservas), len(ativas))
        self.assertEqual(agenda.arvores[1].validar(), [])

        intervalos = sorted(ativas.values())
        for (i1, f1), (i2, f2) in zip(intervalos, intervalos[1:]):
            self.assertLessEqual(f1, i2)


class TestCustoLogaritmico(unittest.TestCase):
    def test_conflito_visita_no_maximo_duas_alturas(self):
        agenda = Agenda()
        agenda.adicionar_sala("Sala", 30)

        for deslocamento in range(1000):
            dia = DIA + timedelta(days=deslocamento)
            agenda.reservar(1, "Aula", "A", h(8, dia=dia), h(9, dia=dia))

        _, custo = agenda.salas_livres(h(8), h(9))
        arvore = agenda.arvores[1]
        _, comparacoes = agenda._achar_conflito(
            1,
            h(8, 30, dia=DIA + timedelta(days=500)),
            h(8, 45, dia=DIA + timedelta(days=500))
        )
        self.assertLessEqual(comparacoes, 2 * arvore.altura())
        self.assertLess(comparacoes, 40)


if __name__ == "__main__":
    unittest.main()
