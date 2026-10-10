"""Guardián de arquitectura (T0.1).

Los invariantes estructurales se verifican sobre el **código fuente**, no sobre la convención. Igual
que el proyecto anterior comprobaba que el intérprete del corpus no usara `eval`, acá se comprueba
que importar el paquete **no arrastre red**: el descubrimiento y la consulta son cosas distintas, y
mezclarlas hace que un test unitario necesite internet.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_importar_vigia_no_arrastra_httpx() -> None:
    """`import vigia` no puede importar la librería de red.

    Se corre en un proceso limpio a propósito: en el proceso de pytest ya puede estar importada por
    otro test, y entonces la comprobación no probaría nada.
    """
    codigo = (
        "import sys, vigia; "
        "print('httpx' in sys.modules)"
    )
    salida = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=RAIZ,
        env={"PYTHONPATH": str(RAIZ / "src"), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=True,
    )
    assert salida.stdout.strip() == "False"


def test_el_paquete_no_depende_de_nada_externo_todavia() -> None:
    """T0.1 no agrega dependencias. Si aparece una, que sea una decisión y no un accidente."""
    pyproject = (RAIZ / "pyproject.toml").read_text(encoding="utf-8")
    dependencias = pyproject.split("dependencies = [", 1)[1].split("]", 1)[0]
    assert dependencias.strip() == "", f"dependencias inesperadas en T0.1: {dependencias!r}"
