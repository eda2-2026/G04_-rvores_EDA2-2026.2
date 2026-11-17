
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from armazenamento import salvar_agenda
from exemplo import criar_agenda_de_exemplo

CAMINHO = os.path.join(os.path.dirname(__file__), "..", "data", "reservas.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dias", type=int, default=14, help="Quantos dias à frente popular")
    args = parser.parse_args()

    agenda = criar_agenda_de_exemplo(dias=args.dias)
    salvar_agenda(agenda, CAMINHO)
    print(f"{len(agenda.salas)} salas e {len(agenda.reservas)} reservas salvas em data/reservas.json")


if __name__ == "__main__":
    main()
