"""Punto de entrada de TuneBox."""

from __future__ import annotations

import argparse

from scenario import ejecutar_simulacion
from ui import lanzar_gui


def main():
    parser = argparse.ArgumentParser(
        description="TuneBox - Simulador y herramienta educativa de control de acceso"
    )
    parser.add_argument(
        "--modo",
        choices=["gui", "cli"],
        default="gui",
        help="Modo de ejecucion: gui (interfaz educativa) o cli (simulacion en consola)",
    )
    args = parser.parse_args()

    if args.modo == "cli":
        ejecutar_simulacion()
    else:
        lanzar_gui()


if __name__ == "__main__":
    main()
