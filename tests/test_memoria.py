"""Tests de la memoria del servidor, y del dinero que protege.

**Cada mensaje que el robot contesta cuesta ≈ 19 CLP.** No es un detalle de rendimiento: es la
diferencia entre un servicio que aguanta y uno que se deja drenar por cualquiera que encuentre el
número. Los tests de acá fijan las tres cosas que la memoria tiene que hacer, y las tres son
promesas:

1. **No dejarse drenar** — un límite por persona y por ventana.
2. **No quedarse en silencio** — al que cruza el límite se le dice una vez, y después no se le
   contesta. Callar sin avisar es el modo de fallo que este proyecto persigue.
3. **Decir la verdad sobre la privacidad** — la primera vez que alguien escribe, se le avisa que su
   mensaje se analiza con un modelo. La decisión está en `doc/14-GAP.md` §5.1 y hasta ahora no
   estaba implementada: era una promesa escrita y no cumplida.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import fields

from vigia.memoria import Memoria


def _reloj(falso: list[float]) -> Callable[[], float]:
    """Un reloj que se mueve solo cuando el test se lo pide."""

    def ahora() -> float:
        return falso[0]

    return ahora


def test_la_primera_vez_avisa_de_la_privacidad() -> None:
    memoria = Memoria(maximo=5, ventana_s=3600, ahora=_reloj([0.0]))
    decision = memoria.decidir("56911111111")
    assert decision.responder
    assert decision.avisar_privacidad


def test_la_privacidad_se_avisa_una_sola_vez() -> None:
    memoria = Memoria(maximo=5, ventana_s=3600, ahora=_reloj([0.0]))
    memoria.decidir("56911111111")
    for _ in range(3):
        assert not memoria.decidir("56911111111").avisar_privacidad


def test_a_cada_persona_se_le_avisa_por_separado() -> None:
    """El aviso es de quien escribe, no del servidor: si no, el segundo no se entera."""
    memoria = Memoria(maximo=5, ventana_s=3600, ahora=_reloj([0.0]))
    memoria.decidir("56911111111")
    assert memoria.decidir("56922222222").avisar_privacidad


def test_bajo_el_limite_se_contesta_siempre() -> None:
    memoria = Memoria(maximo=3, ventana_s=3600, ahora=_reloj([0.0]))
    for _ in range(3):
        assert memoria.decidir("56911111111").responder


def test_al_cruzar_el_limite_se_avisa_una_vez_y_despues_no_se_contesta() -> None:
    """**No se calla de golpe.** El que se pasó recibe un aviso, y recién después silencio."""
    memoria = Memoria(maximo=3, ventana_s=3600, ahora=_reloj([0.0]))
    for _ in range(3):
        memoria.decidir("56911111111")

    cuarta = memoria.decidir("56911111111")
    assert cuarta.responder, "al cruzar el límite todavía se contesta, para poder avisar"
    assert cuarta.avisar_limite

    quinta = memoria.decidir("56911111111")
    assert not quinta.responder, "ya avisado: cada mensaje de más costaría 19 CLP"
    assert not quinta.avisar_limite


def test_el_limite_es_por_persona_y_no_global() -> None:
    """Que un spammer no deje sin servicio a todo el resto."""
    memoria = Memoria(maximo=2, ventana_s=3600, ahora=_reloj([0.0]))
    memoria.decidir("56911111111")
    memoria.decidir("56911111111")
    memoria.decidir("56911111111")
    assert memoria.decidir("56922222222").responder


def test_la_ventana_se_renueva() -> None:
    reloj = [0.0]
    memoria = Memoria(maximo=2, ventana_s=3600, ahora=_reloj(reloj))
    memoria.decidir("56911111111")
    memoria.decidir("56911111111")
    memoria.decidir("56911111111")
    assert not memoria.decidir("56911111111").responder

    reloj[0] = 3600.0
    renovada = memoria.decidir("56911111111")
    assert renovada.responder
    assert renovada.avisar_limite is False


def test_la_memoria_no_guarda_el_mensaje() -> None:
    """Solo lleva cuenta y ventana. **No hay dónde meter el texto**, y eso es a propósito."""
    memoria = Memoria(maximo=5, ventana_s=3600, ahora=_reloj([0.0]))
    memoria.decidir("56911111111")

    assert "56911111111" in memoria._estados, "la clave sí se guarda: permite contar por persona"

    # Se recorre el estado real, campo por campo. Si alguien agrega dónde meter texto, falla.
    for estado in memoria._estados.values():
        for campo in fields(estado):
            valor = getattr(estado, campo.name)
            assert isinstance(valor, (int, float, bool)), (
                f"{campo.name} guarda {type(valor).__name__}: la memoria lleva números y banderas,"
                " nunca texto de nadie"
            )


def test_no_crece_sin_limite() -> None:
    """Una memoria que crece con cada número que escribe es una fuga en un servicio público."""
    memoria = Memoria(maximo=1, ventana_s=3600, ahora=_reloj([0.0]))
    for i in range(5000):
        memoria.decidir(f"569{i:08d}")
    assert memoria.cuantos() <= memoria.tope_de_numeros
