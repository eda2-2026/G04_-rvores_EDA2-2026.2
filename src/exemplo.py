import random
from datetime import date, datetime, time, timedelta

from agenda import Agenda, ErroDeReserva

SALAS_PADRAO = [
    ("Sala 101", 40, "sala"),
    ("Sala 102", 30, "sala"),
    ("Sala 201", 60, "sala"),
    ("Laboratório de Informática", 25, "laboratorio"),
    ("Laboratório de Eletrônica", 20, "laboratorio"),
    ("Auditório", 120, "auditorio"),
]

EVENTOS = [
    ("Aula de Estruturas de Dados 2", "Prof. Almeida"),
    ("Aula de Cálculo 2", "Prof.ª Costa"),
    ("Monitoria de Programação", "Monitoria"),
    ("Reunião de grupo de pesquisa", "Prof.ª Ribeiro"),
    ("Oficina de Python", "Liga de Programação"),
    ("Prova de Física 1", "Prof. Martins"),
    ("Defesa de TCC", "Prof. Duarte"),
    ("Palestra de carreira", "Centro Acadêmico"),
    ("Ensaio de apresentação", "Empresa Júnior"),
]


def criar_agenda_basica() -> Agenda:
    agenda = Agenda()
    for nome, capacidade, tipo in SALAS_PADRAO:
        agenda.adicionar_sala(nome, capacidade, tipo)
    return agenda


def criar_agenda_de_exemplo(hoje: date = None, dias: int = 14, semente: int = 2026) -> Agenda:
    hoje = hoje or date.today()
    rng = random.Random(semente)
    agenda = criar_agenda_basica()

    for deslocamento in range(dias):
        dia = hoje + timedelta(days=deslocamento)
        if dia.weekday() >= 5:
            continue

        for sala in agenda.listar_salas():
            for _ in range(rng.randint(2, 5)):
                inicio_min = rng.randrange(7 * 60, 20 * 60, 30)
                duracao = rng.choice((60, 90, 120))
                inicio = datetime.combine(dia, time.min) + timedelta(minutes=inicio_min)
                fim = inicio + timedelta(minutes=duracao)
                titulo, responsavel = rng.choice(EVENTOS)
                try:
                    agenda.reservar(sala.id, titulo, responsavel, inicio, fim)
                except ErroDeReserva:
                    pass

    return agenda