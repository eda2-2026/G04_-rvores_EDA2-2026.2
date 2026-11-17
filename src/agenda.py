from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple

from rubro_negra import ArvoreRubroNegra

ABERTURA = time(7, 0)
FECHAMENTO = time(22, 0)

TIPOS_DE_SALA = ("sala", "laboratorio", "auditorio")


class ErroDeReserva(Exception):

    status = 400

    def para_resposta(self) -> Dict[str, Any]:
        return {"erro": str(self)}


class DadosInvalidos(ErroDeReserva):
    status = 400


class HorarioInvalido(ErroDeReserva):
    status = 400


class SalaNaoEncontrada(ErroDeReserva):
    status = 404


class ReservaNaoEncontrada(ErroDeReserva):
    status = 404


class ConflitoDeHorario(ErroDeReserva):
    status = 409

    def __init__(self, conflito: "Reserva", custo: Dict[str, int]):
        super().__init__(
            f"Horário indisponível: conflita com \"{conflito.titulo}\" "
            f"({conflito.inicio:%H:%M}–{conflito.fim:%H:%M})."
        )
        self.conflito = conflito
        self.custo = custo

    def para_resposta(self) -> Dict[str, Any]:
        return {
            "erro": str(self),
            "conflito": self.conflito.para_dict(),
            "custo": self.custo,
        }


@dataclass
class Sala:
    id: int
    nome: str
    capacidade: int
    tipo: str = "sala"


@dataclass
class Reserva:
    id: int
    sala_id: int
    titulo: str
    responsavel: str
    inicio: datetime
    fim: datetime

    def para_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sala_id": self.sala_id,
            "titulo": self.titulo,
            "responsavel": self.responsavel,
            "inicio": self.inicio.isoformat(timespec="minutes"),
            "fim": self.fim.isoformat(timespec="minutes"),
        }

    @staticmethod
    def de_dict(dados: Dict[str, Any]) -> "Reserva":
        return Reserva(
            id=int(dados["id"]),
            sala_id=int(dados["sala_id"]),
            titulo=str(dados["titulo"]),
            responsavel=str(dados["responsavel"]),
            inicio=datetime.fromisoformat(dados["inicio"]),
            fim=datetime.fromisoformat(dados["fim"]),
        )


class Agenda:
    def __init__(self) -> None:
        self.salas: Dict[int, Sala] = {}
        self.arvores: Dict[int, ArvoreRubroNegra] = {}
        self.reservas: Dict[int, Reserva] = {}  # índice por id
        self._proximo_id_sala = 1
        self._proximo_id_reserva = 1


    def adicionar_sala(self, nome: str, capacidade: int, tipo: str = "sala") -> Sala:
        nome = (nome or "").strip()
        if not nome:
            raise DadosInvalidos("Informe o nome da sala.")
        if not isinstance(capacidade, int) or isinstance(capacidade, bool) or capacidade <= 0:
            raise DadosInvalidos("A capacidade deve ser um número inteiro maior que zero.")
        if tipo not in TIPOS_DE_SALA:
            raise DadosInvalidos(f"Tipo inválido. Use um destes: {', '.join(TIPOS_DE_SALA)}.")
        if any(s.nome.lower() == nome.lower() for s in self.salas.values()):
            raise DadosInvalidos(f"Já existe uma sala chamada \"{nome}\".")

        sala = Sala(self._proximo_id_sala, nome, capacidade, tipo)
        self._proximo_id_sala += 1
        self.salas[sala.id] = sala
        self.arvores[sala.id] = ArvoreRubroNegra()
        return sala

    def _arvore(self, sala_id: int) -> ArvoreRubroNegra:
        if sala_id not in self.arvores:
            raise SalaNaoEncontrada(f"Sala {sala_id} não encontrada.")
        return self.arvores[sala_id]

    def listar_salas(self) -> List[Sala]:
        return sorted(self.salas.values(), key=lambda s: s.id)

    @staticmethod
    def _validar_horario(inicio: datetime, fim: datetime) -> None:
        if fim <= inicio:
            raise HorarioInvalido("O horário de término deve ser depois do início.")
        if inicio.date() != fim.date():
            raise HorarioInvalido("A reserva deve começar e terminar no mesmo dia.")
        if inicio.time() < ABERTURA or fim.time() > FECHAMENTO:
            raise HorarioInvalido(
                f"Reservas só entre {ABERTURA:%H:%M} e {FECHAMENTO:%H:%M}."
            )


    def _achar_conflito(
        self, sala_id: int, inicio: datetime, fim: datetime
    ) -> Tuple[Optional[Reserva], int]:
        """
        Retorna (reserva_em_conflito_ou_None, nós_visitados).
        Duas descidas na árvore: piso(inicio) e sucessor(inicio).
        """
        arvore = self._arvore(sala_id)
        visitas_antes = arvore.visitas

        conflito: Optional[Reserva] = None

        anterior = arvore.piso(inicio)
        if anterior is not None and anterior[1].fim > inicio:
            conflito = anterior[1]
        else:
            proxima = arvore.sucessor(inicio)
            if proxima is not None and proxima[1].inicio < fim:
                conflito = proxima[1]

        return conflito, arvore.visitas - visitas_antes

    def _custo(self, sala_id: int, comparacoes: int) -> Dict[str, int]:
        arvore = self.arvores[sala_id]
        return {
            "comparacoes": comparacoes,
            "reservas_na_sala": len(arvore),
            "altura_arvore": arvore.altura(),
        }


    def reservar(
        self,
        sala_id: int,
        titulo: str,
        responsavel: str,
        inicio: datetime,
        fim: datetime,
    ) -> Tuple[Reserva, Dict[str, int]]:
    
        titulo = (titulo or "").strip()
        responsavel = (responsavel or "").strip()
        if not titulo:
            raise DadosInvalidos("Informe o título da reserva.")
        if not responsavel:
            raise DadosInvalidos("Informe o responsável pela reserva.")

        arvore = self._arvore(sala_id)
        self._validar_horario(inicio, fim)

        conflito, comparacoes = self._achar_conflito(sala_id, inicio, fim)

        custo = self._custo(sala_id, comparacoes)
        if conflito is not None:
            raise ConflitoDeHorario(conflito, custo)

        reserva = Reserva(self._proximo_id_reserva, sala_id, titulo, responsavel, inicio, fim)
        self._proximo_id_reserva += 1

        arvore.inserir(inicio, reserva)
        self.reservas[reserva.id] = reserva

        return reserva, custo

    def cancelar(self, reserva_id: int) -> Reserva:
        reserva = self.reservas.get(reserva_id)
        if reserva is None:
            raise ReservaNaoEncontrada(f"Reserva {reserva_id} não encontrada.")

        self.arvores[reserva.sala_id].remover(reserva.inicio)
        del self.reservas[reserva_id]
        return reserva


    def reservas_do_dia(self, sala_id: int, dia: date) -> List[Reserva]:

        arvore = self._arvore(sala_id)
        comeco = datetime.combine(dia, time.min)
        itens = arvore.faixa(comeco, comeco + timedelta(days=1))
        return [reserva for _, reserva in itens]

    def horarios_livres(
        self, sala_id: int, dia: date, duracao_minutos: int = 30
    ) -> List[Tuple[datetime, datetime]]:

        if duracao_minutos <= 0:
            raise DadosInvalidos("A duração deve ser maior que zero.")

        minimo = timedelta(minutes=duracao_minutos)
        cursor = datetime.combine(dia, ABERTURA)
        limite = datetime.combine(dia, FECHAMENTO)
        livres: List[Tuple[datetime, datetime]] = []

        for reserva in self.reservas_do_dia(sala_id, dia):
            if reserva.inicio - cursor >= minimo:
                livres.append((cursor, reserva.inicio))
            cursor = max(cursor, reserva.fim)

        if limite - cursor >= minimo:
            livres.append((cursor, limite))

        return livres

    def salas_livres(
        self,
        inicio: datetime,
        fim: datetime,
        capacidade_minima: int = 0,
        tipo: Optional[str] = None,
    ) -> Tuple[List[Sala], Dict[str, int]]:

        self._validar_horario(inicio, fim)

        total_comparacoes = 0
        livres: List[Sala] = []
        candidatas = 0

        for sala in self.listar_salas():
            if sala.capacidade < capacidade_minima:
                continue
            if tipo and sala.tipo != tipo:
                continue

            candidatas += 1
            conflito, comparacoes = self._achar_conflito(sala.id, inicio, fim)
            total_comparacoes += comparacoes
            if conflito is None:
                livres.append(sala)

        livres.sort(key=lambda s: (s.capacidade, s.nome))
        return livres, {"comparacoes": total_comparacoes, "salas_verificadas": candidatas}

    def proxima_reserva(self, sala_id: int, a_partir_de: datetime) -> Optional[Reserva]:
        proxima = self._arvore(sala_id).sucessor(a_partir_de)
        return None if proxima is None else proxima[1]

    def estatisticas(self) -> List[Dict[str, Any]]:
        resultado = []
        for sala in self.listar_salas():
            arvore = self.arvores[sala.id]
            resultado.append(
                {
                    "sala_id": sala.id,
                    "sala": sala.nome,
                    "reservas": len(arvore),
                    "altura": arvore.altura(),
                    "altura_negra": arvore.altura_negra(),
                    "rotacoes": arvore.rotacoes,
                    "valida": arvore.validar() == [],
                }
            )
        return resultado


    def para_dict(self) -> Dict[str, Any]:
        return {
            "proximo_id_sala": self._proximo_id_sala,
            "proximo_id_reserva": self._proximo_id_reserva,
            "salas": [asdict(sala) for sala in self.listar_salas()],
            "reservas": [
                reserva.para_dict()
                for reserva in sorted(self.reservas.values(), key=lambda r: r.id)
            ],
        }

    @classmethod
    def de_dict(cls, dados: Dict[str, Any]) -> "Agenda":
        agenda = cls()

        for item in dados.get("salas", []):
            sala = Sala(int(item["id"]), str(item["nome"]), int(item["capacidade"]),
                        str(item.get("tipo", "sala")))
            agenda.salas[sala.id] = sala
            agenda.arvores[sala.id] = ArvoreRubroNegra()

        for item in dados.get("reservas", []):
            reserva = Reserva.de_dict(item)
            if reserva.sala_id not in agenda.arvores:
                raise ValueError(f"Reserva {reserva.id} aponta para sala inexistente.")
            conflito, _ = agenda._achar_conflito(reserva.sala_id, reserva.inicio, reserva.fim)
            if conflito is not None:
                raise ValueError(
                    f"Dados inconsistentes: reservas {reserva.id} e {conflito.id} se sobrepõem."
                )
            agenda.arvores[reserva.sala_id].inserir(reserva.inicio, reserva)
            agenda.reservas[reserva.id] = reserva

        maior_sala = max(agenda.salas, default=0)
        maior_reserva = max(agenda.reservas, default=0)
        agenda._proximo_id_sala = max(int(dados.get("proximo_id_sala", 1)), maior_sala + 1)
        agenda._proximo_id_reserva = max(int(dados.get("proximo_id_reserva", 1)), maior_reserva + 1)
        return agenda
