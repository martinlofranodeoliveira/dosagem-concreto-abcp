"""Ponto de entrada para execução via `python -m dosagem_concreto_abcp`."""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
