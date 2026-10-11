"""Motor de respuesta (T1.1): de un texto a un veredicto sobre su enlace. Módulo puro: solo stdlib.

## La única pregunta que este programa contesta

**¿Este enlace es el sitio de la institución que el mensaje dice ser?**

Hasta `T1.9` la pregunta era «¿el enlace es del Estado?». **La cambió el corpus de `T1.7`**: en 45
estafas reales del CSIRT, el **47 % suplanta a Banco Ripley**, un banco privado. A esa persona,
«el enlace NO es del Estado» le dice algo cierto y **le deja la duda intacta**.

Ahora el motor busca **de quién dice ser** el mensaje en el catálogo, y compara con **de quién es**
el enlace. Eso da dos veredictos nuevos —`COINCIDE` y `NO_COINCIDE`— y deja los dos viejos
—`OFICIAL` y `AJENO`— para cuando no se reconoce ninguna institución reclamada, que es información
peor pero cierta.

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

_RE_URL_COMPLETA = re.compile(r"(?:https?://|www\.)[^\s<>\"'()\[\]]+", re.IGNORECASE)
"""Un enlace completo, con su ruta. Sirve para **quitarlo entero** del texto antes de buscar
hosts."""

_RE_AUTORIDAD = re.compile(r"^(?:https?://|www\.)(?P<host>[^/\s]+)", re.IGNORECASE)
"""De un enlace completo, **solo la autoridad**.

Sin separar esto, la ruta se leía como un dominio propio: `.../SantaIsabelws/tb.php` hacía que
`tb.php` apareciera como un enlace aparte, y el motor lo nombraba como si fuera un sitio del
atacante — una acusación falsa sobre un dato inventado. **Lo encontró la medición sobre el corpus,
no un test unitario**, y se ve en el ejemplo `8fph22-00674-01`.
"""

_RE_ETIQUETA_FINAL = re.compile(r"[^\W\d_]{2,}", re.UNICODE)
"""La última etiqueta tiene que ser alfabética y de dos letras o más.

Descarta versiones (`1.2.3`), abreviaturas (`S.A.`) y RUTs (`22.345.678-9`), que si no llenarían la
respuesta de enlaces que nadie puede apretar.
"""


class Veredicto(StrEnum):
    """Sobre el enlace y su coherencia con lo que el mensaje dice ser. Nunca sobre el mensaje."""

    COINCIDE = "coincide"
    NO_COINCIDE = "no_coincide"
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
    reclamadas: tuple[str, ...]
    dice_ser_del_estado: bool
    explicacion: str


def _plegar(texto: str) -> str:
    """Minúsculas y sin tildes: «ClaveÚnica» y «claveunica» tienen que caer en el mismo balde."""
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def extraer_enlaces(texto: str, marcas: Sequence[Marca] = MARCAS) -> tuple[Enlace, ...]:
    """Los enlaces del texto, sin repetir, en orden de aparición y ya reducidos a lo registrable."""
    vistos: dict[str, Enlace] = {}
    candidatos: list[str] = []
    for completo in _RE_URL_COMPLETA.findall(texto):
        autoridad = _RE_AUTORIDAD.match(completo)
        if autoridad:
            candidatos.append(autoridad.group("host"))
    # Los dominios que no traen esquema se buscan en lo que queda, para que una ruta no cuente.
    candidatos.extend(_RE_HOST.findall(_RE_URL_COMPLETA.sub(" ", texto)))

    for bruto in candidatos:
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


def _sin_enlaces(texto: str, enlaces: tuple[Enlace, ...]) -> str:
    """El texto con los enlaces borrados, para buscar de quién dice ser **sin contar la URL**.

    Sin esto, `... ingrese a claveunica.gob.cl` «diría ser» de ClaveÚnica por el solo hecho de
    enlazarla. Y peor: un mensaje que dice ser del Banco Ripley y enlaza a un dominio del Estado
    daría `COINCIDE`, porque la URL inflaba la lista de reclamadas y escondía la incoherencia —
    justo la que el motor existe para encontrar.

    «Dice ser» es lo que está escrito en la prosa. Enlazar a alguien no es decir ser él.
    """
    limpio = texto
    for enlace in enlaces:
        limpio = re.sub(re.escape(enlace.host), " ", limpio, flags=re.IGNORECASE)
    return limpio


def _sin_redundantes(mencionadas: Sequence[Marca]) -> tuple[Marca, ...]:
    """Quita las instituciones cuyo nombre ya está contenido en el de otra reclamada.

    «Banco Ripley» y «Ripley» son la misma cosa para quien lee, y nombrar las dos produce
    **«El mensaje dice ser de Banco Ripley, Ripley»** — la frase que más importa, mal escrita. Lo
    encontró el armado de los mensajes de `T3.1`, no un test unitario.
    """
    resultado: list[Marca] = []
    for marca in mencionadas:
        formas_ajenas = " ".join(
            f"{otra.nombre} {' '.join(otra.alias)}" for otra in mencionadas if otra is not marca
        )
        if re.search(rf"\b{re.escape(marca.nombre)}\b", formas_ajenas):
            continue
        resultado.append(marca)
    return tuple(resultado)


def _mencionadas(texto: str, marcas: Sequence[Marca]) -> tuple[Marca, ...]:
    """Las instituciones del catálogo que el mensaje **dice ser**, en orden del catálogo.

    Se busca el nombre normalizado y **todos sus alias**, cada uno como **palabra completa**. La
    palabra completa no es un detalle: `sii` está en el catálogo con tres letras y no puede
    dispararse dentro de otra palabra.

    El costo aceptado es que una palabra ambigua como `metro` —que es el Metro y también una unidad
    de largo— marca de más. Va en la dirección segura: dice de más, no calla de menos.
    """
    plegado = _plegar(texto)
    encontradas: list[Marca] = []
    for marca in marcas:
        formas = (marca.nombre, *marca.alias)
        if any(re.search(rf"\b{re.escape(forma)}\b", plegado) for forma in formas):
            encontradas.append(marca)
    return tuple(encontradas)


def _dice_ser_del_estado(texto: str, marcas: Sequence[Marca]) -> bool:
    """Si el mensaje **dice ser** de una institución, del catálogo o del Estado en general."""
    if _mencionadas(texto, marcas):
        return True
    plegado = _plegar(texto)
    return any(termino in plegado for termino in TERMINOS_ESTADO)


def _sospechas(
    enlaces: tuple[Enlace, ...], suplantaciones: tuple[Coincidencia, ...]
) -> list[str]:
    """Los agravantes de una respuesta que ya dice que hay algo mal.

    Van aparte porque los comparten los dos veredictos que avisan, y tenerlos duplicados era pedir
    que uno de los dos se olvidara de uno.
    """
    partes: list[str] = []
    if any(not e.ascii for e in enlaces):
        partes.append(
            "Además usa letras que no son latinas: es un truco para que se vea igual al dominio "
            "verdadero."
        )
    if suplantaciones:
        nombres = ", ".join(dict.fromkeys(s.etiqueta or s.marca for s in suplantaciones))
        partes.append(f"El enlace se parece a {nombres}.")
    return partes


def _explicar(
    veredicto: Veredicto,
    enlaces: tuple[Enlace, ...],
    suplantaciones: tuple[Coincidencia, ...],
    reclamadas: tuple[str, ...],
    dice_ser_del_estado: bool,
) -> str:
    """La respuesta en castellano, para reenviar tal cual."""
    advertencia = (
        " Eso dice del enlace, no del mensaje: si le piden su clave o sus datos personales,"
        " no los entregue."
    )

    if veredicto is Veredicto.COINCIDE:
        dominios = ", ".join(e.registrable for e in enlaces)
        return f"El enlace {dominios} es el sitio de {', '.join(reclamadas)}.{advertencia}"

    if veredicto is Veredicto.NO_COINCIDE:
        quienes = ", ".join(reclamadas)
        ajenos = ", ".join(e.registrable for e in enlaces if e.institucion not in reclamadas)
        partes = [f"El mensaje dice ser de {quienes} y el enlace {ajenos} no es de {quienes}."]
        return " ".join(partes + _sospechas(enlaces, suplantaciones))

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
    partes.extend(_sospechas(enlaces, suplantaciones))
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
    mencionadas = _sin_redundantes(_mencionadas(_sin_enlaces(texto, enlaces), marcas))
    reclamadas = tuple(marca.etiqueta or marca.nombre for marca in mencionadas)
    dice_ser_del_estado = _dice_ser_del_estado(texto, marcas)

    if not enlaces:
        veredicto = Veredicto.SIN_ENLACES
    elif reclamadas:
        # La pregunta de T1.9: ¿todos los enlaces son de la institución que el mensaje dice ser?
        # Basta uno que no lo sea para romper la coincidencia: es el ataque mezclado.
        coincide = all(enlace.institucion in reclamadas for enlace in enlaces)
        veredicto = Veredicto.COINCIDE if coincide else Veredicto.NO_COINCIDE
    elif all(e.es_oficial for e in enlaces):
        veredicto = Veredicto.OFICIAL
    else:
        veredicto = Veredicto.AJENO

    return Evaluacion(
        veredicto=veredicto,
        enlaces=enlaces,
        suplantaciones=suplantaciones,
        reclamadas=reclamadas,
        dice_ser_del_estado=dice_ser_del_estado,
        explicacion=_explicar(veredicto, enlaces, suplantaciones, reclamadas, dice_ser_del_estado),
    )
