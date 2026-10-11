"""Mide la regla de la petición (`T4.4`): cuánto cubre, y qué no se puede medir todavía.

## Lo que sí se mide

**Cuánto gana la cobertura.** De las 342 estafas del CSIRT, cuántas pasan de `mudo` —el motor no
dice nada— a `PIDE_LO_INDEBIDO`, que es el veredicto nuevo.

## Lo que **no** se puede medir, y hay que decirlo

**La precisión de esta regla.** Haría falta un corpus de mensajes **legítimos**, y no existe: es el
mismo hueco que bloqueó la calibración del motor de enlaces, y ahora bloquea esta regla por segunda
vez.

Por eso acá no se informa una tasa de falsas acusaciones de la petición. Informarla con estos datos
sería inventarla.

## Lo que sí se puede probar, construido y declarado

Un puñado de **frases legítimas armadas a mano** —las que una institución sí escribiría— para ver si
la regla las marca. El extractor de referencia **no entiende la negación**, así que «nunca le
pediremos su clave» lo marca. Eso es su defecto conocido, y es exactamente lo que un modelo tendría
que superar para justificarse.
"""

from __future__ import annotations

import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from vigia.motor import Veredicto, evaluar  # noqa: E402
from vigia.peticion import es_peticion_indebida, extraer_por_palabras  # noqa: E402

CORPUS = RAIZ / "corpus" / "alertas_csirt.json"
CONTROL = RAIZ / "corpus" / "control_invertido.json"

FRASES_LEGITIMAS = (
    "Recuerde: nunca le pediremos su clave por mensaje ni por teléfono.",
    "Su clave es personal. No la comparta con nadie.",
    "Para su seguridad, no entregue sus datos personales por mensaje.",
    "Su trámite fue recibido. Revise el estado en nuestro sitio oficial.",
    "Le informamos que su solicitud fue aprobada. No es necesario hacer nada más.",
    "Este es un aviso informativo. No responda a este mensaje.",
)
"""Frases que **una institución sí escribiría**. Armadas a mano y declaradas como tales.

No son un corpus: son sondas. Sirven para ver si la regla se dispara donde no debe.
"""


def cobertura(ejemplos: list[dict[str, object]]) -> tuple[int, int]:
    """Cuántas pasan de `mudo` a `PIDE_LO_INDEBIDO` con el extractor de referencia."""
    mudos = ganadas = 0
    for ejemplo in ejemplos:
        texto = str(ejemplo["texto_reconstruido"])
        antes = evaluar(texto)
        if antes.veredicto is not Veredicto.SIN_ENLACES:
            continue
        mudos += 1
        dice_ser = antes.reclamadas[0] if antes.reclamadas else None
        despues = evaluar(texto, peticion=extraer_por_palabras(texto, dice_ser))
        if despues.veredicto is Veredicto.PIDE_LO_INDEBIDO:
            ganadas += 1
    return mudos, ganadas


def main() -> None:
    ejemplos = json.loads(CORPUS.read_text(encoding="utf-8"))
    controles = json.loads(CONTROL.read_text(encoding="utf-8"))

    print(f"=== cobertura sobre las {len(ejemplos)} estafas del corpus ===")
    mudos, ganadas = cobertura(ejemplos)
    print(f"  mudos sin la regla:        {mudos}")
    print(f"  recuperados por la regla:  {ganadas}")
    print(f"  quedan mudos:              {mudos - ganadas}")

    print(f"\n=== lo que la regla marca sobre los {len(controles)} controles ===")
    print("  (el texto sigue siendo de estafa, así que marcarlo es CORRECTO)")
    marcados = sum(
        1
        for control in controles
        if es_peticion_indebida(
            extraer_por_palabras(str(control["texto_de_control"]), str(control["institucion"]))
        )
    )
    print(f"  marcados: {marcados} de {len(controles)}")

    print("\n=== sondas: frases que una institución SÍ escribiría ===")
    print("  (construidas a mano, no recogidas, y se declara)")
    falsos = 0
    for frase in FRASES_LEGITIMAS:
        peticion = extraer_por_palabras(frase, "BancoEstado")
        marcada = es_peticion_indebida(peticion)
        falsos += int(marcada)
        print(f"  {'MARCA ' if marcada else 'ok    '} {frase}")
    print(f"\n  falsas alarmas en las sondas: {falsos} de {len(FRASES_LEGITIMAS)}")

    print(
        "\n=== lo que NO se puede medir ===\n"
        "  La precisión de esta regla necesita un corpus de mensajes LEGÍTIMOS, y no existe.\n"
        "  Es el mismo hueco que bloqueó la calibración del motor de enlaces, por segunda vez.\n"
        "  No se informa una tasa: informarla con estos datos sería inventarla."
    )


if __name__ == "__main__":
    main()
