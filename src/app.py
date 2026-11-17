import os
import sys
import threading
from datetime import date, datetime

from flask import Flask, Response, jsonify, request, send_from_directory

sys.path.insert(0, os.path.dirname(__file__))

from agenda import DadosInvalidos, ErroDeReserva, TIPOS_DE_SALA, ABERTURA, FECHAMENTO
from armazenamento import carregar_agenda, salvar_agenda
from exemplo import criar_agenda_basica, criar_agenda_de_exemplo
from visualizar import svg_da_arvore

RAIZ_PROJETO = os.path.join(os.path.dirname(__file__), "..")
PASTA_FRONTEND = os.path.join(RAIZ_PROJETO, "frontend")
CAMINHO_PADRAO = os.path.join(RAIZ_PROJETO, "data", "reservas.json")


def _json_do_corpo() -> dict:
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise DadosInvalidos("Envie um corpo JSON válido.")
    return dados


def _inteiro(valor, nome: str) -> int:
    try:
        if isinstance(valor, bool):
            raise ValueError
        return int(valor)
    except (TypeError, ValueError):
        raise DadosInvalidos(f"O campo '{nome}' deve ser um número inteiro.")


def _datahora(valor, nome: str) -> datetime:
    try:
        return datetime.fromisoformat(str(valor))
    except (TypeError, ValueError):
        raise DadosInvalidos(
            f"O campo '{nome}' deve estar no formato AAAA-MM-DDTHH:MM (ex.: 2026-11-20T14:00)."
        )


def _dia(valor, nome: str = "dia") -> date:
    try:
        return date.fromisoformat(str(valor))
    except (TypeError, ValueError):
        raise DadosInvalidos(f"O parâmetro '{nome}' deve estar no formato AAAA-MM-DD.")


def _hhmm(momento: datetime) -> str:
    return momento.strftime("%H:%M")


def criar_app(caminho_dados: str = None, com_exemplo: bool = True) -> Flask:
    """
    Cria a aplicação. `caminho_dados` é o JSON de persistência; se não
    existir, é criado com salas (e, se `com_exemplo`, reservas de exemplo).
    """
    caminho = caminho_dados or os.getenv("RESERVAS_JSON") or CAMINHO_PADRAO

    agenda = carregar_agenda(caminho)
    if agenda is None:
        agenda = criar_agenda_de_exemplo() if com_exemplo else criar_agenda_basica()
        salvar_agenda(agenda, caminho)

    trava = threading.RLock()

    app = Flask(__name__, static_folder=None)
    app.config["AGENDA"] = agenda

    @app.errorhandler(ErroDeReserva)
    def tratar_erro_de_reserva(erro: ErroDeReserva):
        return jsonify(erro.para_resposta()), erro.status


    @app.get("/")
    def pagina_principal():
        return send_from_directory(PASTA_FRONTEND, "index.html")

    @app.get("/css/<path:nome>")
    def arquivos_css(nome):
        return send_from_directory(os.path.join(PASTA_FRONTEND, "css"), nome)

    @app.get("/js/<path:nome>")
    def arquivos_js(nome):
        return send_from_directory(os.path.join(PASTA_FRONTEND, "js"), nome)


    @app.get("/api/salas")
    def listar_salas():
        with trava:
            return jsonify({"salas": [vars(s) for s in agenda.listar_salas()]})

    @app.post("/api/salas")
    def criar_sala():
        dados = _json_do_corpo()
        with trava:
            sala = agenda.adicionar_sala(
                dados.get("nome", ""),
                _inteiro(dados.get("capacidade"), "capacidade"),
                dados.get("tipo", "sala"),
            )
            salvar_agenda(agenda, caminho)
        return jsonify({"sala": vars(sala)}), 201


    @app.get("/api/agenda")
    def agenda_do_dia():
        """Reservas de todas as salas em um dia (alimenta o mapa do dia)."""
        dia = _dia(request.args.get("dia"))
        with trava:
            salas = []
            for sala in agenda.listar_salas():
                salas.append(
                    {
                        **vars(sala),
                        "reservas": [r.para_dict() for r in agenda.reservas_do_dia(sala.id, dia)],
                    }
                )
        return jsonify(
            {
                "dia": dia.isoformat(),
                "abertura": ABERTURA.strftime("%H:%M"),
                "fechamento": FECHAMENTO.strftime("%H:%M"),
                "salas": salas,
            }
        )

    @app.get("/api/horarios-livres")
    def horarios_livres():
        sala_id = _inteiro(request.args.get("sala_id"), "sala_id")
        dia = _dia(request.args.get("dia"))
        duracao = _inteiro(request.args.get("duracao", 30), "duracao")
        with trava:
            livres = agenda.horarios_livres(sala_id, dia, duracao)
        return jsonify(
            {"livres": [{"inicio": i.isoformat(timespec="minutes"),
                         "fim": f.isoformat(timespec="minutes")} for i, f in livres]}
        )

    @app.get("/api/salas-livres")
    def salas_livres():
        inicio = _datahora(request.args.get("inicio"), "inicio")
        fim = _datahora(request.args.get("fim"), "fim")
        capacidade = _inteiro(request.args.get("capacidade", 0) or 0, "capacidade")
        tipo = request.args.get("tipo") or None
        if tipo is not None and tipo not in TIPOS_DE_SALA:
            raise DadosInvalidos(f"Tipo inválido. Use um destes: {', '.join(TIPOS_DE_SALA)}.")
        with trava:
            salas, custo = agenda.salas_livres(inicio, fim, capacidade, tipo)
        return jsonify({"salas": [vars(s) for s in salas], "custo": custo})


    @app.post("/api/reservas")
    def criar_reserva():
        dados = _json_do_corpo()
        with trava:
            reserva, custo = agenda.reservar(
                sala_id=_inteiro(dados.get("sala_id"), "sala_id"),
                titulo=dados.get("titulo", ""),
                responsavel=dados.get("responsavel", ""),
                inicio=_datahora(dados.get("inicio"), "inicio"),
                fim=_datahora(dados.get("fim"), "fim"),
            )
            salvar_agenda(agenda, caminho)
        return jsonify({"reserva": reserva.para_dict(), "custo": custo}), 201

    @app.delete("/api/reservas/<int:reserva_id>")
    def cancelar_reserva(reserva_id: int):
        with trava:
            reserva = agenda.cancelar(reserva_id)
            salvar_agenda(agenda, caminho)
        return jsonify({"reserva": reserva.para_dict()})

    # ------------------------ por dentro da árvore ------------------------

    @app.get("/api/estatisticas")
    def estatisticas():
        with trava:
            return jsonify({"salas": agenda.estatisticas()})

    @app.get("/api/arvore/<int:sala_id>")
    def desenho_da_arvore(sala_id: int):
        with trava:
            arvore = agenda._arvore(sala_id)  # levanta SalaNaoEncontrada se não existir
            svg = svg_da_arvore(
                arvore,
                rotulo=lambda chave: _hhmm(chave),
                dica=lambda chave, reserva: (
                    f"{reserva.titulo} · {chave:%d/%m/%Y} {_hhmm(reserva.inicio)}–{_hhmm(reserva.fim)}"
                ),
            )
        return Response(svg, mimetype="image/svg+xml")

    return app


if __name__ == "__main__":
    porta = int(os.getenv("PORT", 5000))
    print(f"Servindo em: http://127.0.0.1:{porta}")
    criar_app().run(port=porta, debug=False)
