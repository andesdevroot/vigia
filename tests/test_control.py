"""El control invertido (`T4.3`): el mismo texto de la estafa, con el enlace **legítimo**.

Da el **denominador** que faltaba. El corpus son 342 estafas —una sola clase—, así que sin esto
no se podía decir una tasa de falsas acusaciones, que es el error que este proyecto no puede
permitirse: **enseña a desconfiar de lo verdadero.**

**Es un control construido, no un corpus recogido**, y se declara: el texto es idéntico al de una
estafa real y **solo cambia el enlace**, así que mide la acusación que induce el texto. No mide la
falsa acusación sobre mensajes legítimos de verdad, cuya redacción y petición son distintas.
"""

from __future__ import annotations

import json
from pathlib import Path

from vigia.marcas import MARCAS
from vigia.motor import Veredicto, evaluar

RAIZ = Path(__file__).resolve().parents[1]
CONTROLES = json.loads((RAIZ / "corpus" / "control_invertido.json").read_text(encoding="utf-8"))
CORPUS = {
    str(e["codigo"]): e
    for e in json.loads((RAIZ / "corpus" / "alertas_csirt.json").read_text(encoding="utf-8"))
}

ACUSA = (Veredicto.NO_COINCIDE, Veredicto.AJENO, Veredicto.CONFIRMADO)
"""Los tres veredictos que, sobre un enlace legítimo, son una acusación falsa."""

VEREDICTOS = {
    str(c["codigo"]): evaluar(str(c["texto_de_control"])).veredicto for c in CONTROLES
}

ACUSADOS_CONOCIDOS: dict[str, str] = {}
"""Falsas acusaciones conocidas, con su razón. Hoy no hay ninguna, y esa es la noticia.

Se declaran igual que los `GRAVES_CONOCIDOS` del corpus: **un fallo escrito es un fallo
vigilado.** Si aparece uno, este test falla y hay que decidir si es un bug o una excepción.
"""

SUELO_DE_COINCIDENCIA = 0.88
"""El 90 % de hoy con holgura. Es un **trinquete**: un cambio que lo baje falla acá."""


def test_el_control_tiene_suficientes_casos() -> None:
    assert len(CONTROLES) >= 180, "el control se encogió"


def test_el_control_solo_cambia_el_enlace() -> None:
    """La garantía del diseño: **el texto queda idéntico**.

    Si alguien tocara algo más que el enlace, el control dejaría de aislar una sola variable y el
    número que produce no significaría nada.
    """
    for control in CONTROLES:
        original = str(CORPUS[str(control["codigo"])]["texto_reconstruido"])
        sin_enlace_original = original.replace(str(control["url_maliciosa"]), "")
        sin_enlace_control = str(control["texto_de_control"]).replace(
            f"https://{control['dominio_oficial']}/", ""
        )
        assert sin_enlace_control == sin_enlace_original, control["codigo"]


def test_los_enlaces_de_control_son_los_oficiales_del_catalogo() -> None:
    """El enlace legítimo sale del catálogo, no de una lista escrita aparte."""
    for control in CONTROLES:
        institucion = str(control["institucion"])
        oficiales = {
            dominio
            for marca in MARCAS
            if (marca.etiqueta or marca.nombre) == institucion
            for dominio in marca.oficiales
        }
        assert str(control["dominio_oficial"]) in oficiales, control["codigo"]


def test_ningun_mensaje_de_control_es_acusado() -> None:
    """**El invariante del control.** Decir ser de X y enlazar a X no puede ser una acusación.

    Es el otro lado del invariante del corpus: aquel exige no perdonar una estafa; este, no
    condenar un enlace correcto. Los dos juntos son la herramienta.
    """
    acusados = sorted(codigo for codigo, v in VEREDICTOS.items() if v in ACUSA)
    nuevos = sorted(set(acusados) - set(ACUSADOS_CONOCIDOS))
    assert not nuevos, f"falsas acusaciones sin declarar: {nuevos}"


def test_los_acusados_declarados_siguen_ocurriendo() -> None:
    """Una excepción declarada que ya no ocurre se saca de la lista: si no, la lista miente."""
    acusados = {codigo for codigo, v in VEREDICTOS.items() if v in ACUSA}
    resueltos = sorted(set(ACUSADOS_CONOCIDOS) - acusados)
    assert not resueltos, f"acusados declarados que ya no ocurren: {resueltos}"


def test_la_coincidencia_no_baja_del_suelo() -> None:
    """El trinquete: reconocer que el enlace es el correcto es el resultado que se espera."""
    coinciden = sum(1 for v in VEREDICTOS.values() if v is Veredicto.COINCIDE)
    proporcion = coinciden / len(VEREDICTOS)
    assert proporcion >= SUELO_DE_COINCIDENCIA, f"la coincidencia cayó a {proporcion:.1%}"
