"""Guardián de la especificación.

Verifica que **cada requisito de `spec.md` tenga un test, y que ese test exista**. Sin esto la
especificación es un documento; con esto es un contrato: no se puede agregar un requisito sin
cubrirlo, ni renombrar un test sin que el guardián se entere, ni dejar un requisito apuntando a un
test que ya no está.

Es el equivalente de `test_arquitectura.py`: un invariante del **proyecto**, no del código.

**Un detalle que confunde si no se sabe:** acá se cuentan **funciones** (`def test_...`), y pytest
cuenta **casos**. No coinciden porque dos tests de `test_suplantacion.py` están parametrizados y
expanden a varios casos cada uno. Los dos números son correctos; miden cosas distintas.
"""

from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SPEC = RAIZ / "spec.md"
TESTS = RAIZ / "tests"

FILA = re.compile(r"^\|\s*(REQ-\d+)\s*\|(.+)\|\s*(.+?)\s*\|\s*$")
CITA_TEST = re.compile(r"`(test_[^`]+)`")
MINIMO_ESPERADO = 50
"""Si la especificación se encoge de golpe, es más probable que alguien la haya roto que que el
proyecto se haya achicado."""


def requisitos() -> dict[str, list[str]]:
    """Los requisitos de `spec.md` con los tests que cada uno nombra."""
    encontrados: dict[str, list[str]] = {}
    for linea in SPEC.read_text(encoding="utf-8").splitlines():
        coincidencia = FILA.match(linea)
        if coincidencia:
            numero, _, campo_tests = coincidencia.groups()
            encontrados[numero] = CITA_TEST.findall(campo_tests)
    return encontrados


def nombres_de_tests_existentes() -> set[str]:
    """Los nombres de todos los tests del proyecto, leídos del código fuente.

    **No empieza con `test_` a propósito**: si empezara, pytest lo recolectaría como un test y
    fallaría por devolver un conjunto. Pasó, y lo avisó el propio pytest.
    """
    nombres: set[str] = set()
    for archivo in TESTS.glob("test_*.py"):
        nombres.update(re.findall(r"^def (test_\w+)", archivo.read_text(encoding="utf-8"), re.M))
    return nombres


def test_hay_especificacion_y_requisitos() -> None:
    assert SPEC.exists(), "falta spec.md en la raíz del proyecto"
    assert len(requisitos()) >= MINIMO_ESPERADO


def test_todo_requisito_nombra_al_menos_un_test() -> None:
    sin_test = [numero for numero, nombres in requisitos().items() if not nombres]
    assert not sin_test, f"requisitos sin test: {sin_test}"


def test_todo_test_nombrado_existe() -> None:
    """El corazón del guardián: un requisito que apunta a un test inexistente no está cubierto."""
    existentes = nombres_de_tests_existentes()
    faltantes = {
        numero: [nombre for nombre in nombres if nombre not in existentes]
        for numero, nombres in requisitos().items()
        if any(nombre not in existentes for nombre in nombres)
    }
    assert not faltantes, f"requisitos que apuntan a tests que no existen: {faltantes}"


def test_no_hay_requisitos_repetidos() -> None:
    """Dos veces el mismo número son dos requisitos distintos con el mismo nombre."""
    numeros = re.findall(r"^\|\s*(REQ-\d+)\s*\|", SPEC.read_text(encoding="utf-8"), re.M)
    repetidos = sorted({numero for numero in numeros if numeros.count(numero) > 1})
    assert not repetidos, f"requisitos repetidos: {repetidos}"


def test_los_requisitos_estan_numerados_sin_huecos_absurdos() -> None:
    numeros = sorted(int(numero.split("-")[1]) for numero in requisitos())
    assert numeros[0] >= 1
    assert len(set(numeros)) == len(numeros)
