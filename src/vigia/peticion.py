"""La **petición** del mensaje (`T4.4`): qué pide, y no qué enlace trae. Solo stdlib.

## La brecha que cierra

El motor juzga **enlaces**. Pero buena parte del fraude chileno no trae enlace: pide una llamada,
una transferencia, o directamente la clave. Ahí el motor se queda mudo — medido: **338 de 342** en
la columna de la cita del CSIRT.

## La regla, y por qué es determinista

**El modelo extrae; la regla decide.** Y la regla es una frase que las instituciones publican:

> **Ninguna institución pide su clave, sus datos personales ni una transferencia por mensaje.**

Es citable, es verificable y no la decide un modelo.

## Por qué el esquema es **cerrado**

`pide` y `urgencia` son listas fijas de valores. Un campo cerrado se audita, se mide y se
compara; uno abierto, no. **Es lo que permite enfrentar dos extractores y decir cuál gana**.

## Por qué hay un extractor de referencia **sin modelo**

Para tener contra qué comparar. Un modelo que no le gane a buscar señales en el texto **no
justifica su costo, ni su latencia, ni mandar el mensaje de un ciudadano a un tercero**. Eso hay
que medirlo, no suponerlo — y es la razón de que este archivo exista antes que cualquier API.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PeticionDe(StrEnum):
    """Lo que un mensaje puede pedir. **Lista cerrada**, y a propósito."""

    CLAVE = "clave"
    DATOS_PERSONALES = "datos_personales"
    TRANSFERENCIA = "transferencia"
    LLAMAR = "llamar_telefono"
    PINCHAR = "pinchar_enlace"
    RESPONDER = "responder_mensaje"


PIDE_LO_INDEBIDO = frozenset(
    {PeticionDe.CLAVE, PeticionDe.DATOS_PERSONALES, PeticionDe.TRANSFERENCIA}
)
"""Las tres que **ninguna institución pide por mensaje**, y que lo dicen ellas mismas.

Las otras tres no son indebidas: pedir que alguien pinche un enlace o llame a un teléfono es lo
normal en un aviso legítimo. **Marcarlas sería convertir la herramienta en una alarma.**
"""


COMO_SE_DICE: dict[PeticionDe, str] = {
    PeticionDe.CLAVE: "su clave",
    PeticionDe.DATOS_PERSONALES: "sus datos personales",
    PeticionDe.TRANSFERENCIA: "una transferencia",
    PeticionDe.LLAMAR: "que llame a un teléfono",
    PeticionDe.PINCHAR: "que pinche un enlace",
    PeticionDe.RESPONDER: "que responda el mensaje",
}


def _enumerar(cosas: list[str]) -> str:
    """`[a]` → `a`; `[a, b]` → `a y b`; `[a, b, c]` → `a, b y c`. Sin coma de Oxford, en Chile."""
    if not cosas:
        return ""
    if len(cosas) == 1:
        return cosas[0]
    return ", ".join(cosas[:-1]) + " y " + cosas[-1]


@dataclass(frozen=True, slots=True)
class Peticion:
    """Lo que el mensaje pide, extraído. **No es un veredicto**: es la entrada de la regla."""

    dice_ser: str | None
    pide: tuple[PeticionDe, ...]
    urgencia: str | None = None

    def lo_indebido(self) -> tuple[PeticionDe, ...]:
        """De lo que pide, lo que ninguna institución pediría."""
        return tuple(que for que in self.pide if que in PIDE_LO_INDEBIDO)

    def lo_indebido_en_castellano(self) -> str:
        """Lo mismo, como se le dice a una persona. **El vocabulario es para el modelo, no para
        el ciudadano**: `datos_personales` no es una frase que alguien lea."""
        return _enumerar([COMO_SE_DICE[que] for que in self.lo_indebido()])


def es_peticion_indebida(peticion: Peticion | None) -> bool:
    """La regla entera, y son **dos** condiciones.

    Dice ser de una institución **y** pide algo que ninguna pide. Las dos hacen falta: sin el
    reclamo no se sabe de quién dice ser, y pedir la clave no es fraude si lo pide alguien que no
    dice ser un banco —una charla entre conocidos, por ejemplo—.
    """
    return bool(peticion and peticion.dice_ser and peticion.lo_indebido())


SEÑALES: dict[PeticionDe, tuple[str, ...]] = {
    PeticionDe.CLAVE: ("clave", "contraseña", "contrasena", "password", "pin de", "su pin"),
    PeticionDe.DATOS_PERSONALES: (
        "datos personales",
        "datos de su tarjeta",
        "numero de tarjeta",
        "datos de seguridad",
        "cvv",
        "fecha de vencimiento",
        "su rut",
    ),
    PeticionDe.TRANSFERENCIA: (
        "transferencia",
        "transferir",
        "deposite",
        "deposito",
        "abone",
        "pague en la cuenta",
        "cuenta corriente",
    ),
    PeticionDe.LLAMAR: ("llame", "llamar", "comuniquese", "contacte al", "marque el"),
    PeticionDe.PINCHAR: ("ingrese", "haga clic", "click", "visite", "acceda", "abra el enlace"),
    PeticionDe.RESPONDER: ("responda", "conteste", "responder este"),
}
"""Las señales del extractor de referencia, en minúsculas y sin tildes porque el texto se pliega.

**Es un punto de partida, no la respuesta.** Su virtud es ser determinista y gratis; su defecto, que
una señal encontrada no distingue «pida» de «mencione».
"""


SONDAS = (
    "Recuerde: nunca le pediremos su clave por mensaje ni por teléfono.",
    "Su clave es personal. No la comparta con nadie.",
    "Para su seguridad, no entregue sus datos personales por mensaje.",
    "Su trámite fue recibido. Revise el estado en nuestro sitio oficial.",
    "Le informamos que su solicitud fue aprobada. No es necesario hacer nada más.",
    "Este es un aviso informativo. No responda a este mensaje.",
)
"""Frases que **una institución sí escribiría**, para comparar extractores. Armadas a mano.

Son el **conjunto de conformidad** de la extracción: las tres primeras son consejos contra el
phishing —lo más legítimo que hay— y llevan **negación**, que es justo lo que buscar señales no
entiende.

Medido con el extractor de referencia: **marca 3 de 6**, y las tres son las de negación. Marca
precisamente los mensajes que enseñan a la gente a cuidarse. Sirven para exigirle a un extractor
con modelo que las entienda antes de aceptarlo.
"""


def plegar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar señales."""
    import unicodedata

    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def extraer_por_palabras(texto: str, dice_ser: str | None = None) -> Peticion:
    """El extractor **de referencia**: busca señales en el texto. Sin modelo, determinista y gratis.

    Existe para tener contra qué medir un extractor con LLM. **Un modelo que no le gane a esto no
    justifica su costo, su latencia ni mandar el mensaje de un ciudadano a un tercero.**
    """
    plegado = plegar(texto)
    encontradas = tuple(
        que for que, señales in SEÑALES.items() if any(s in plegado for s in señales)
    )
    return Peticion(dice_ser=dice_ser, pide=encontradas)
