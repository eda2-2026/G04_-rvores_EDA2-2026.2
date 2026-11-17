
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app import criar_app

RESERVA = {
    "sala_id": 1,
    "titulo": "Aula de ED2",
    "responsavel": "Prof. Almeida",
    "inicio": "2026-11-20T10:00",
    "fim": "2026-11-20T12:00",
}


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.caminho = os.path.join(self.pasta.name, "reservas.json")
        self.app = criar_app(self.caminho, com_exemplo=False)
        self.cliente = self.app.test_client()

    def tearDown(self):
        self.pasta.cleanup()

    def test_lista_salas_padrao(self):
        resposta = self.cliente.get("/api/salas")
        self.assertEqual(resposta.status_code, 200)
        self.assertGreaterEqual(len(resposta.get_json()["salas"]), 1)

    def test_criar_reserva(self):
        resposta = self.cliente.post("/api/reservas", json=RESERVA)
        self.assertEqual(resposta.status_code, 201)
        corpo = resposta.get_json()
        self.assertEqual(corpo["reserva"]["titulo"], "Aula de ED2")
        self.assertIn("comparacoes", corpo["custo"])

    def test_conflito_devolve_409_com_detalhes(self):
        self.cliente.post("/api/reservas", json=RESERVA)
        sobreposta = dict(RESERVA, titulo="Outra", inicio="2026-11-20T11:00", fim="2026-11-20T13:00")
        resposta = self.cliente.post("/api/reservas", json=sobreposta)

        self.assertEqual(resposta.status_code, 409)
        corpo = resposta.get_json()
        self.assertEqual(corpo["conflito"]["titulo"], "Aula de ED2")
        self.assertIn("custo", corpo)
        self.assertIn("conflita", corpo["erro"])

    def test_reserva_encostada_e_aceita(self):
        self.cliente.post("/api/reservas", json=RESERVA)
        depois = dict(RESERVA, titulo="Depois", inicio="2026-11-20T12:00", fim="2026-11-20T13:00")
        self.assertEqual(self.cliente.post("/api/reservas", json=depois).status_code, 201)

    def test_agenda_do_dia(self):
        self.cliente.post("/api/reservas", json=RESERVA)
        corpo = self.cliente.get("/api/agenda?dia=2026-11-20").get_json()
        self.assertEqual(corpo["abertura"], "07:00")
        self.assertEqual(corpo["fechamento"], "22:00")
        sala1 = next(s for s in corpo["salas"] if s["id"] == 1)
        self.assertEqual(len(sala1["reservas"]), 1)

        vazio = self.cliente.get("/api/agenda?dia=2026-11-21").get_json()
        self.assertTrue(all(s["reservas"] == [] for s in vazio["salas"]))

    def test_cancelar_reserva(self):
        reserva_id = self.cliente.post("/api/reservas", json=RESERVA).get_json()["reserva"]["id"]
        self.assertEqual(self.cliente.delete(f"/api/reservas/{reserva_id}").status_code, 200)
        self.assertEqual(self.cliente.delete(f"/api/reservas/{reserva_id}").status_code, 404)
        self.assertEqual(self.cliente.post("/api/reservas", json=RESERVA).status_code, 201)

    def test_horarios_livres(self):
        self.cliente.post("/api/reservas", json=RESERVA)
        corpo = self.cliente.get("/api/horarios-livres?sala_id=1&dia=2026-11-20&duracao=60").get_json()
        self.assertEqual(
            [(i["inicio"][11:], i["fim"][11:]) for i in corpo["livres"]],
            [("07:00", "10:00"), ("12:00", "22:00")],
        )

    def test_salas_livres_exclui_a_ocupada(self):
        self.cliente.post("/api/reservas", json=RESERVA)
        url = "/api/salas-livres?inicio=2026-11-20T10:30&fim=2026-11-20T11:30"
        ids = [s["id"] for s in self.cliente.get(url).get_json()["salas"]]
        self.assertNotIn(1, ids)
        self.assertGreater(len(ids), 0)

    def test_erros_de_validacao(self):
        casos = [
            (dict(RESERVA, titulo=""), 400),
            (dict(RESERVA, fim="2026-11-20T09:00"), 400),
            (dict(RESERVA, inicio="2026-11-20T05:00"), 400),
            (dict(RESERVA, inicio="isso não é data"), 400),
            (dict(RESERVA, sala_id=999), 404),
            (dict(RESERVA, sala_id="abc"), 400),
        ]
        for corpo, esperado in casos:
            with self.subTest(corpo=corpo):
                resposta = self.cliente.post("/api/reservas", json=corpo)
                self.assertEqual(resposta.status_code, esperado)
                self.assertIn("erro", resposta.get_json())

    def test_corpo_que_nao_e_json(self):
        resposta = self.cliente.post("/api/reservas", data="texto solto", content_type="text/plain")
        self.assertEqual(resposta.status_code, 400)

    def test_parametro_dia_invalido(self):
        self.assertEqual(self.cliente.get("/api/agenda?dia=ontem").status_code, 400)
        self.assertEqual(self.cliente.get("/api/agenda").status_code, 400)

    def test_criar_sala(self):
        resposta = self.cliente.post("/api/salas", json={"nome": "Sala Nova", "capacidade": 15, "tipo": "sala"})
        self.assertEqual(resposta.status_code, 201)
        repetida = self.cliente.post("/api/salas", json={"nome": "Sala Nova", "capacidade": 15})
        self.assertEqual(repetida.status_code, 400)

    def test_dados_persistem_entre_reinicios(self):
        self.cliente.post("/api/reservas", json=RESERVA)

        reiniciado = criar_app(self.caminho, com_exemplo=False).test_client()
        corpo = reiniciado.get("/api/agenda?dia=2026-11-20").get_json()
        sala1 = next(s for s in corpo["salas"] if s["id"] == 1)
        self.assertEqual(sala1["reservas"][0]["titulo"], "Aula de ED2")

        sobreposta = dict(RESERVA, titulo="Outra", inicio="2026-11-20T11:00", fim="2026-11-20T11:30")
        self.assertEqual(reiniciado.post("/api/reservas", json=sobreposta).status_code, 409)

    def test_desenho_da_arvore_e_estatisticas(self):
        self.cliente.post("/api/reservas", json=RESERVA)
        svg = self.cliente.get("/api/arvore/1")
        self.assertEqual(svg.status_code, 200)
        self.assertEqual(svg.mimetype, "image/svg+xml")
        self.assertIn("<svg", svg.get_data(as_text=True))
        self.assertEqual(self.cliente.get("/api/arvore/999").status_code, 404)

        estatisticas = self.cliente.get("/api/estatisticas").get_json()["salas"]
        self.assertTrue(all(s["valida"] for s in estatisticas))

    def test_nao_ha_texto_html_executavel_no_svg(self):
        corpo = dict(RESERVA, titulo='<script>alert(1)</script>')
        self.cliente.post("/api/reservas", json=corpo)
        svg = self.cliente.get("/api/arvore/1").get_data(as_text=True)
        self.assertNotIn("<script>", svg)


if __name__ == "__main__":
    unittest.main()
