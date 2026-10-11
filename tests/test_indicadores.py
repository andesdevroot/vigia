"""Tests del índice de indicadores del Estado (`T4.2`)."""

from __future__ import annotations

import json
from pathlib import Path

from vigia.indicadores import INDICE, Indice, cargar


def test_un_dominio_del_indice_esta_reportado() -> None:
    indice = Indice({"nhmwcotitostado.info": ["8fph22-00664-01"]})
    assert indice.reportado("nhmwcotitostado.info") == ("8fph22-00664-01",)


def test_un_dominio_que_no_esta_no_esta_reportado() -> None:
    indice = Indice({"nhmwcotitostado.info": ["8fph22-00664-01"]})
    assert indice.reportado("sernac.cl") == ()


def test_un_indice_vacio_no_reporta_nada() -> None:
    assert Indice({}).reportado("cualquier-cosa.xyz") == ()
    assert len(Indice({})) == 0


def test_la_consulta_usa_el_dominio_registrable() -> None:
    """Se consulta por dominio registrable, que es la unidad con la que el motor compara todo.

    El índice guarda `nhmwcotitostado.info`; el mensaje puede traer `www.nhmwcotitostado.info` o
    `nhmwcotitostado.info/activacion/cuenta/`. Los tres son el mismo dominio y tienen que calzar.
    """
    indice = Indice({"nhmwcotitostado.info": ["8fph22-00664-01"]})
    for candidato in (
        "www.nhmwcotitostado.info",
        "nhmwcotitostado.info",
        "sub.nhmwcotitostado.info",
    ):
        assert indice.reportado(candidato) == ("8fph22-00664-01",), candidato


def test_una_plataforma_compartida_nunca_se_confirma() -> None:
    """Aunque el índice la traiga, `bit.ly` **no** se confirma.

    El CSIRT reporta una URL en `bit.ly`; eso no vuelve fraudulento a `bit.ly`, que aloja los
    enlaces de todo el mundo. Medido: **70 alertas** del índice reportan un `bit.ly`. Sin esto, el
    motor habría condenado a medio internet, y lo encontraron los tests al romperse cuatro.
    """
    indice = Indice({"bit.ly": ["8ffr22-01148-01"], "web.app": ["X"], "myshopify.com": ["Y"]})
    for plataforma in ("bit.ly", "web.app", "myshopify.com", "www.bit.ly", "algo.web.app"):
        assert indice.reportado(plataforma) == (), plataforma


def test_un_sufijo_publico_nunca_se_confirma() -> None:
    """`com.br` no es un dominio: es un sufijo de registro. Confirmarlo condenaría a todo Brasil.

    Medido en el índice: `com.br` con 14 alertas, `com.au` con 10, `com.np` con 8.
    """
    indice = Indice({"com.br": ["X"], "com.au": ["Y"]})
    assert indice.reportado("com.br") == ()
    assert indice.reportado("algo.com.br") == ()


def test_un_dominio_normal_si_se_confirma() -> None:
    """El filtro no puede pasarse de listo: un dominio de verdad sigue confirmándose."""
    indice = Indice({"ucmstudio.info": ["X"], "malo.cl": ["Y"]})
    assert indice.reportado("ucmstudio.info") == ("X",)
    assert indice.reportado("malo.cl") == ("Y",)


def test_la_alerta_se_puede_citar() -> None:
    """El ciudadano tiene que poder ir a leer la fuente."""
    alerta = Indice({}).alerta("8fph22-00664-01")
    assert alerta == "https://csirt.gob.cl/alertas/8fph22-00664-01/"


def test_el_indice_se_carga_de_un_archivo(tmp_path: Path) -> None:
    ruta = tmp_path / "indice.json"
    ruta.write_text(
        json.dumps({"dominios": {"malo.xyz": ["ABC-01"]}}), encoding="utf-8"
    )
    assert cargar(ruta).reportado("malo.xyz") == ("ABC-01",)


def test_un_archivo_inexistente_da_un_indice_vacio(tmp_path: Path) -> None:
    """Sin índice el motor degrada a lo que era antes. **No arranca mal: arranca sin confirmar.**"""
    assert len(cargar(tmp_path / "no-existe.json")) == 0


def test_un_archivo_corrupto_da_un_indice_vacio(tmp_path: Path) -> None:
    ruta = tmp_path / "indice.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    assert len(cargar(ruta)) == 0


def test_un_archivo_sin_la_clave_dominios_da_un_indice_vacio(tmp_path: Path) -> None:
    ruta = tmp_path / "indice.json"
    ruta.write_text(json.dumps({"otra_cosa": 1}), encoding="utf-8")
    assert len(cargar(ruta)) == 0


def test_el_indice_del_paquete_tiene_dominios() -> None:
    """El índice que se construye con `scripts/construir_indice.py` tiene que venir con datos."""
    assert len(INDICE) > 500, "el índice del paquete quedó vacío o casi vacío"
    assert INDICE.reportado("nhmwcotitostado.info"), "un dominio del corpus no está en el índice"
