"""Motor de respuesta (T1.1): de un texto a un veredicto sobre su enlace. Módulo puro: solo stdlib.

## La única pregunta que este programa contesta

**¿El enlace del mensaje es del Estado?**

No contesta si el mensaje es convincente, si el sitio es bonito ni si quien escribe es funcionario.
Nada de eso se puede saber leyendo un texto, y afirmarlo sería el peor servicio posible: el ataque
mejor construido pone un enlace bueno **y** uno malo en el mismo mensaje, para que el bueno preste
confianza al malo.

## El invariante

> `OFICIAL` exige que **todos** los enlaces sean del Estado, y que haya al menos uno.

Sin eso, un ataque que agregue `claveunica.gob.cl` de adorno recibiría el visto bueno. Hay un test
que fija el invariante sobre varios textos, porque es la única propiedad del motor cuya violación
convierte la herramienta en parte del problema.

## Por qué mirar el enlace alcanza, en Chile

`gob.cl` no es un TLD: es un segundo nivel de registro exclusivo del Estado (`T0.5`). Entonces
«¿termina en `.gob.cl`?» **es** la pregunta completa, y no hace falta lista ni certificado. Es el
ancla de confianza que el Estado ya puso, y este módulo la usa en vez de reconstruirla.

## Lo que este módulo NO sabe

Quién escribe. Un mensaje con un enlace legítimo puede ser una estafa de todas formas, y por eso la
explicación de `OFICIAL` dice explícitamente de qué habla y de qué no.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from vigia.suplantacion import (
    SEGUNDO_NIVEL_ESTADO,
    Coincidencia,
    Marca,
    detectar,
    etiqueta_registrable,
)

SUFIJO_ESTADO = f".{SEGUNDO_NIVEL_ESTADO}"

TERMINOS_ESTADO = ("claveunica", "gob.cl", "gobierno de chile", "estado de chile")
"""Palabras que hacen que un mensaje **diga ser** del Estado.

Es una lista corta a propósito: marca el discurso, no el catálogo de instituciones. El catálogo de
marcas chilenas es otra tarea, y meterlo acá convertiría este módulo en un corpus.
"""

_RE_HOST = re.compile(r"(?<![\w@-])[\w-]+(?:\.[\w-]+)+(?![\w-])", re.UNICODE)
"""Un nombre de host, con esquema o sin él.

Dos detalles que no son cosméticos:

- `(?<![\\w@-])` y `(?![\\w-])` son las fronteras. Sin la primera, `contacto@bancoestado.cl` se
  leería como un enlace —una falsa alarma con el correo del propio banco— y sin la segunda, un
  dominio dentro de un nombre más largo se leería cortado.
- `\\w` en Python 3 es Unicode, así que un homoglifo cirílico **entra** como parte del host. Es
  justo lo que se quiere: que entre y que se vea que no es ASCII, en vez de que se escape del
  análisis por no ser una letra latina.
"""

_RE_ETIQUETA_FINAL = re.compile(r"[^\W\d_]{2,}", re.UNICODE)
"""La última etiqueta tiene que ser alfabética y de dos letras o más.

Descarta versiones (`1.2.3`), abreviaturas (`S.A.`) y RUTs (`22.345.678-9`), que si no llenarían la
respuesta de enlaces que nadie puede apretar.
"""


class Veredicto(StrEnum):
    """Sobre el enlace, no sobre el mensaje. La distinción es todo el producto."""

    OFICIAL = "oficial"
    AJENO = "ajeno"
    SIN_ENLACES = "sin_enlaces"


@dataclass(frozen=True, slots=True)
class Enlace:
    """Un enlace encontrado en el texto."""

    host: str
    registrable: str
    es_del_estado: bool
    ascii: bool


@dataclass(frozen=True, slots=True)
class Evaluacion:
    """La respuesta completa: el veredicto, la evidencia, y la explicación para la persona."""

    veredicto: Veredicto
    enlaces: tuple[Enlace, ...]
    suplantaciones: tuple[Coincidencia, ...]
    dice_ser_del_estado: bool
    explicacion: str


def _plegar(texto: str) -> str:
    """Minúsculas y sin tildes: «ClaveÚnica» y «claveunica» tienen que caer en el mismo balde."""
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def extraer_enlaces(texto: str) -> tuple[Enlace, ...]:
    """Los enlaces del texto, sin repetir, en orden de aparición y ya reducidos a lo registrable."""
    vistos: dict[str, Enlace] = {}
    for bruto in _RE_HOST.findall(texto):
        host = bruto.strip(".-").lower()
        if not _RE_ETIQUETA_FINAL.fullmatch(host.rsplit(".", 1)[-1]):
            continue
        registrable = etiqueta_registrable(host)
        if registrable in vistos:
            continue
        vistos[registrable] = Enlace(
            host=host,
            registrable=registrable,
            # `isascii` no es paranoia: `claveunica.gоb.cl` con la `o` cirílica se ve idéntico y no
            # termina en `.gob.cl`, así que sin este control la comparación sola ya lo salva — pero
            # el ciudadano merece saber *por qué*.
            es_del_estado=host.isascii() and registrable.endswith(SUFIJO_ESTADO),
            ascii=host.isascii(),
        )
    return tuple(vistos.values())


def _explicar(
    veredicto: Veredicto,
    enlaces: tuple[Enlace, ...],
    suplantaciones: tuple[Coincidencia, ...],
    dice_ser_del_estado: bool,
) -> str:
    """La respuesta en castellano, para reenviar tal cual."""
    if veredicto is Veredicto.OFICIAL:
        dominios = ", ".join(e.registrable for e in enlaces)
        return (
            f"El enlace es del Estado: {dominios}. "
            "Eso dice del enlace, no del mensaje: si le piden su ClaveUnica, su clave o sus datos "
            "personales, no los entregue."
        )

    if veredicto is Veredicto.SIN_ENLACES:
        aviso = "El mensaje no trae ningún enlace, así que no se puede verificar."
        if dice_ser_del_estado:
            aviso += " Dice ser del Estado, y decirlo no lo hace cierto."
        return aviso + " Un aviso del Estado no pide claves ni datos por mensaje."

    partes = [
        f"El enlace {e.registrable} NO es del Estado."
        for e in enlaces
        if not e.es_del_estado
    ]
    if any(not e.ascii for e in enlaces):
        partes.append(
            "Además usa letras que no son latinas: es un truco para que se vea igual al dominio "
            "verdadero."
        )
    if suplantaciones:
        nombres = ", ".join(dict.fromkeys(s.marca for s in suplantaciones))
        partes.append(f"El enlace se parece a {nombres}.")
    if dice_ser_del_estado:
        partes.append("El mensaje dice ser del Estado y el enlace no lo es.")
    return " ".join(partes)


def evaluar(texto: str, marcas: Sequence[Marca] = ()) -> Evaluacion:
    """Evalúa un mensaje reenviado y devuelve el veredicto sobre sus enlaces.

    `marcas` es opcional: sin ella se sigue sabiendo si el enlace es del Estado, que es la pregunta
    que importa. Lo que agrega es el nombre de la marca imitada, para que la respuesta sea más
    fácil de creer.
    """
    enlaces = extraer_enlaces(texto)
    suplantaciones = tuple(
        coincidencia
        for enlace in enlaces
        if not enlace.es_del_estado
        and (coincidencia := detectar(enlace.registrable, marcas)) is not None
    )
    dice_ser_del_estado = any(t in _plegar(texto) for t in TERMINOS_ESTADO)

    if not enlaces:
        veredicto = Veredicto.SIN_ENLACES
    elif all(e.es_del_estado for e in enlaces):
        veredicto = Veredicto.OFICIAL
    else:
        veredicto = Veredicto.AJENO

    return Evaluacion(
        veredicto=veredicto,
        enlaces=enlaces,
        suplantaciones=suplantaciones,
        dice_ser_del_estado=dice_ser_del_estado,
        explicacion=_explicar(veredicto, enlaces, suplantaciones, dice_ser_del_estado),
    )
