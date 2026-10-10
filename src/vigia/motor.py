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

**Con una excepción medida (`T1.3`):** no todas las instituciones del Estado usan `.gob.cl`. El
Servel, el SERNAC, Carabineros, la PDI, Correos, Metro, TVN, Codelco y la TGR tienen dominios `.cl`
históricos, y **`servel.gob.cl` no existe**. Para eso está el catálogo de `marcas.py`: una lista
mantenida a mano y verificada, no una regla. Sin ella, un mensaje legítimo del Servel se leería como
falso — el peor error posible, porque enseña a desconfiar de lo verdadero.

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

from vigia.marcas import MARCAS, institucion_de
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
    institucion: str | None = None

    @property
    def es_oficial(self) -> bool:
        """Del Estado por `.gob.cl`, o de una institución que el catálogo conoce.

        Las dos cosas se mantienen separadas a propósito: `es_del_estado` es el ancla que el Estado
        controla por política de registro (`T0.5`) y no puede fallar; `institucion` viene de una
        lista blanca escrita a mano, que es el tipo de dato que se pudre si nadie la vuelve a medir.
        """
        return self.es_del_estado or self.institucion is not None


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


def extraer_enlaces(texto: str, marcas: Sequence[Marca] = MARCAS) -> tuple[Enlace, ...]:
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
            institucion=institucion_de(registrable, marcas),
        )
    return tuple(vistos.values())


def _detalle(enlaces: tuple[Enlace, ...]) -> str:
    """Cómo se nombran los enlaces en la respuesta: con su institución cuando se conoce."""
    return ", ".join(
        f"{e.registrable} ({e.institucion})" if e.institucion else e.registrable for e in enlaces
    )


def _dice_ser_del_estado(texto: str, marcas: Sequence[Marca]) -> bool:
    """Si el mensaje **dice ser** de una institución.

    Dos señales. La primera es el discurso del Estado —«ClaveÚnica», «gob.cl», «Gobierno de
    Chile»—. La segunda es el nombre de una institución del catálogo **como palabra completa**, que
    es lo que hace que «SERVEL: tiene una multa» no pase por un mensaje cualquiera.

    Se compara palabra completa y no subcadena porque `sii` está en el catálogo y no puede
    dispararse dentro de otra palabra.
    """
    plegado = _plegar(texto)
    if any(termino in plegado for termino in TERMINOS_ESTADO):
        return True
    return any(
        re.search(rf"\b{re.escape(marca.nombre)}\b", plegado) is not None for marca in marcas
    )


def _explicar(
    veredicto: Veredicto,
    enlaces: tuple[Enlace, ...],
    suplantaciones: tuple[Coincidencia, ...],
    dice_ser_del_estado: bool,
) -> str:
    """La respuesta en castellano, para reenviar tal cual."""
    if veredicto is Veredicto.OFICIAL:
        encabezado = (
            "El enlace es del Estado"
            if all(e.es_del_estado for e in enlaces)
            else "El enlace es de una institución oficial"
        )
        return (
            f"{encabezado}: {_detalle(enlaces)}. "
            "Eso dice del enlace, no del mensaje: si le piden su ClaveUnica, su clave o sus datos "
            "personales, no los entregue."
        )

    if veredicto is Veredicto.SIN_ENLACES:
        aviso = "El mensaje no trae ningún enlace, así que no se puede verificar."
        if dice_ser_del_estado:
            aviso += " Dice ser del Estado, y decirlo no lo hace cierto."
        return aviso + " Un aviso del Estado no pide claves ni datos por mensaje."

    partes = [
        (
            f"El enlace {e.registrable} es de {e.institucion}."
            if e.institucion
            else f"El enlace {e.registrable} NO es del Estado."
        )
        for e in enlaces
        # Un enlace del Estado no se nombra acá: el mensaje puede mezclar uno bueno con uno malo, y
        # lo que hay que mirar es el malo. Nombrar el bueno como si fuera el problema sería peor que
        # no decir nada.
        if not e.es_del_estado
    ]
    if any(not e.ascii for e in enlaces):
        partes.append(
            "Además usa letras que no son latinas: es un truco para que se vea igual al dominio "
            "verdadero."
        )
    if suplantaciones:
        nombres = ", ".join(dict.fromkeys(s.etiqueta or s.marca for s in suplantaciones))
        partes.append(f"El enlace se parece a {nombres}.")
    if dice_ser_del_estado:
        partes.append("El mensaje dice ser del Estado y el enlace no lo es.")
    return " ".join(partes)


def evaluar(texto: str, marcas: Sequence[Marca] = MARCAS) -> Evaluacion:
    """Evalúa un mensaje reenviado y devuelve el veredicto sobre sus enlaces.

    El catálogo viene por defecto: sin él, un mensaje legítimo del Servel o del SERNAC se leería
    como falso. Se puede pasar otro, y entonces el catálogo de acá no se usa en ninguna parte.
    """
    enlaces = extraer_enlaces(texto, marcas)
    suplantaciones = tuple(
        coincidencia
        for enlace in enlaces
        if not enlace.es_oficial
        and (coincidencia := detectar(enlace.registrable, marcas)) is not None
    )
    dice_ser_del_estado = _dice_ser_del_estado(texto, marcas)

    if not enlaces:
        veredicto = Veredicto.SIN_ENLACES
    elif all(e.es_oficial for e in enlaces):
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
