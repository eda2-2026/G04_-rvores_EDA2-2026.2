import json
import os
from typing import Optional

from agenda import Agenda


def salvar_agenda(agenda: Agenda, caminho: str) -> None:
    caminho = os.path.abspath(caminho)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    temporario = caminho + ".tmp"
    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(agenda.para_dict(), arquivo, ensure_ascii=False, indent=2)
    os.replace(temporario, caminho)


def carregar_agenda(caminho: str) -> Optional[Agenda]:
    caminho = os.path.abspath(caminho)
    if not os.path.exists(caminho):
        return None

    with open(caminho, "r", encoding="utf-8") as arquivo:
        return Agenda.de_dict(json.load(arquivo))