"""Invariantes del motor sobre el corpus real: un guardián, no solo una medición (`T4.2`, `T4.6`).

El corpus de estafas que el CSIRT publicó no sirve solo para sacar un número. Sirve para que
**cualquier cambio en el motor que haga que una estafa real reciba un veredicto favorable se caiga
acá**, antes de llegar a un teléfono.

Esto es la parte de «algoritmo avanzado» que este proyecto necesita de verdad: **invariantes sobre
datos reales**, no un clasificador. Un modelo entrenado con ejemplos **de una sola clase** no se
puede entrenar — y no haría falta: la cobertura ya es del 99,7 %.

Estos tests no tocan la red: el corpus y el índice están versionados en el repositorio.
"""

from __future__ import annotations

import json
from pathlib import Path

from vigia.motor import Veredicto, evaluar

RAIZ = Path(__file__).resolve().parents[1]
CORPUS = json.loads((RAIZ / "corpus" / "alertas_csirt.json").read_text(encoding="utf-8"))

FAVORABLES = (Veredicto.COINCIDE, Veredicto.OFICIAL)
"""Los dos veredictos que le dicen a alguien que el enlace está bien. Sobre una estafa, son el fallo
que este proyecto no puede permitirse."""

GRAVES_CONOCIDOS = {
    "fph24-00951": "el enlace malo no está en la cita: lo único que queda es el señuelo",
    "8fph23-00745-01": "el enlace malo no está en la cita: lo único que queda es el señuelo",
    "8fph23-00755-01": "el enlace malo no está en la cita: lo único que queda es el señuelo",
}
"""Los casos donde juzgar **la cita recortada** da un veredicto favorable, y por qué.

Se declaran a propósito: **un fallo conocido y escrito es un fallo vigilado; uno sin escribir parece
nuevo cada vez.** Si aparece uno nuevo, el test falla.
"""

SUELO_DE_RESPUESTA_UTIL = 0.99
"""Con un punto de holgura sobre lo medido. Es un **trinquete**: si un cambio la baja, falla acá y
no en la cara de alguien."""


def _veredictos(campo: str) -> dict[str, Veredicto]:
    """Un veredicto por mensaje, calculado **una sola vez** para todo el módulo.

    Con 342 mensajes y cuatro recorridos el gate tardaba un segundo de más; con 1.500 serían veinte.
    **Un gate lento es un gate que se deja de correr**, y ahí se pierde la disciplina entera. Se
    paga una vez al importar y no una vez por test.
    """
    return {str(ejemplo["codigo"]): evaluar(str(ejemplo[campo])).veredicto for ejemplo in CORPUS}


VEREDICTOS_COMPLETO = _veredictos("texto_reconstruido")
VEREDICTOS_CITA = _veredictos("texto_citado")


def test_el_corpus_esta_completo() -> None:
    assert len(CORPUS) >= 300, "el corpus se encogió"
    for ejemplo in CORPUS:
        for campo in (
            "codigo",
            "texto_citado",
            "texto_reconstruido",
            "url_maliciosa",
            "fuente_alerta",
        ):
            assert ejemplo[campo], f"falta {campo} en {ejemplo.get('codigo')}"


def test_ninguna_estafa_del_corpus_recibe_un_veredicto_favorable() -> None:
    """**El invariante.** Sobre el mensaje completo —lo que un ciudadano reenviaría— el motor no
    puede decir nunca que el enlace está bien.

    Es el test que más vale de todo el proyecto: recorre las estafas reales que publicó el Estado y
    exige **cero indulgencias**.
    """
    indulgentes = sorted(
        codigo for codigo, veredicto in VEREDICTOS_COMPLETO.items() if veredicto in FAVORABLES
    )
    assert not indulgentes, f"estafas reales con veredicto favorable: {indulgentes}"


def test_los_graves_sobre_la_cita_estan_declarados() -> None:
    """Sobre la cita recortada sí hay indulgencias, y están escritas una por una.

    Esos casos nombran un dominio legítimo y el enlace malo está en otra parte; en la cita recortada
    el malo no está y lo único que queda es el señuelo. **Uno nuevo sin declarar hace fallar este
    test**, que es exactamente lo que se quiere.
    """
    graves = {codigo for codigo, v in VEREDICTOS_CITA.items() if v in FAVORABLES}
    nuevos = sorted(graves - set(GRAVES_CONOCIDOS))
    resueltos = sorted(set(GRAVES_CONOCIDOS) - graves)
    assert not nuevos, f"graves nuevos sin declarar: {nuevos}"
    assert not resueltos, f"declarados que ya no ocurren (se pueden sacar de la lista): {resueltos}"


def test_la_respuesta_util_no_baja_del_suelo() -> None:
    """El trinquete: la cobertura de hoy es el piso de mañana."""
    utiles = sum(
        1 for veredicto in VEREDICTOS_COMPLETO.values() if veredicto is not Veredicto.SIN_ENLACES
    )
    proporcion = utiles / len(CORPUS)
    assert proporcion >= SUELO_DE_RESPUESTA_UTIL, f"la respuesta útil cayó a {proporcion:.1%}"


def test_el_corpus_solo_tiene_una_clase_y_por_eso_no_se_entrena() -> None:
    """Todos los mensajes son fraudulentos: **no hay un solo legítimo**.

    Con una sola clase no se entrena un clasificador, y sin legítimos no se puede medir una falsa
    acusación. Está escrito como test para que el día que alguien agregue negativos, se entere de
    que esta limitación cambió.
    """
    etiquetas = {str(ejemplo.get("etiqueta", "estafa")) for ejemplo in CORPUS}
    assert etiquetas == {"estafa"}, f"aparecieron etiquetas nuevas: {etiquetas}"
