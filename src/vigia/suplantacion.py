"""Detector de suplantación de marcas chilenas (T0.2a). Módulo puro: solo stdlib.

## Qué es y qué no es

**Es un filtro, no un veredicto.** Reduce el universo de nombres a un puñado que valga la pena
mirar,
y por eso está sesgado a **recall**: prefiere marcar de más. `bancoestadobeneficios.cl` puede ser
del
propio banco y lo marca igual. Decidir si un candidato marcado es un ataque es de otra capa, y
confundir las dos convierte un detector en un generador de falsas alarmas.

## Por qué la normalización es agresiva, y por qué no demasiado

`banc0estado`, `banc-oestado` y `banc.oestado` tienen que caer en el mismo balde: el atacante elige
la forma que el ojo no distingue. Pero si se normaliza de más, todo se parece a todo y el filtro
deja
de filtrar — hay un test que fija que `banco` y `bancoestado` sigan siendo distintos.

## `gob.cl` no es un TLD

Es un segundo nivel de uso exclusivo del Estado, así que la unidad registrable de
`claveunica.gob.cl` es de **tres** etiquetas. Sin tratarlo aparte, el detector compararía `gob`
contra
la marca y no encontraría nada — y peor, marcaría dominios legítimos del Estado.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

# Grupos de caracteres que un ojo no distingue. **El primero es el representante.**
#
# Van por GRUPOS y no como un mapa letra→letra porque un homoglifo sirve para varias letras: `1`
# reemplaza a la `l` en `banc0estado` pero a la `i` en `claveun1ca`. Un mapa uno-a-uno perdía el
# segundo caso, y lo encontró el test.
GRUPOS_HOMOGLIFOS = ("o0", "il1", "e3", "a4", "s5", "t7", "b8")
HOMOGLIFOS = {falso: grupo[0] for grupo in GRUPOS_HOMOGLIFOS for falso in grupo}
SEPARADORES = ".-_ "
SEGUNDO_NIVEL_ESTADO = "gob.cl"

SUBCADENA_EXTRA_MAX = 12
"""Cuántos caracteres de más tolera la regla de subcadena.

Es la regla más ruidosa del detector: sin cota, `bancoestado` aparece dentro de cualquier nombre que
lo contenga y el filtro se llena de dominios legítimos. La cota es un control de **precisión** y
cuesta recall: una marca embebida en un nombre muy largo deja de marcarse.
"""


class TipoSuplantacion(StrEnum):
    """**Cómo** se parece el candidato a la marca, no cuánto. La técnica, no la magnitud."""

    HOMOGLIFO = "homoglifo"
    EDICION = "edicion"
    PUNTO_A_GUION = "punto_a_guion"
    SUBCADENA = "subcadena"
    TLD = "tld"


@dataclass(frozen=True, slots=True)
class Marca:
    """Una marca chilena y los dominios que **son** suyos.

    `oficiales` es lo que impide marcar al banco por llamarse como el banco: sin esa lista, el
    detector marcaría el dominio legítimo, que es el peor falso positivo posible.

    `etiqueta` es el nombre para mostrar en la respuesta —«SERNAC»— y no el `nombre`, que va
    normalizado porque es con el que se compara. Es opcional para que una marca de prueba no tenga
    que inventar uno.
    """

    nombre: str
    oficiales: frozenset[str]
    etiqueta: str = ""


@dataclass(frozen=True, slots=True)
class Coincidencia:
    """Un candidato que se parece a una marca. **No afirma que sea malicioso.**

    `etiqueta` es el nombre con el que se nombra la marca en la respuesta. Se copia acá y no se
    busca después porque el catálogo con el que se comparó puede no ser el de por defecto.
    """

    marca: str
    candidato: str
    tipo: TipoSuplantacion
    distancia: int
    etiqueta: str = ""


def normalizar(texto: str) -> str:
    """Minúsculas, homoglifos mapeados a su letra, y separadores fuera."""
    resultado = texto.lower()
    for falso, real in HOMOGLIFOS.items():
        resultado = resultado.replace(falso, real)
    for separador in SEPARADORES:
        resultado = resultado.replace(separador, "")
    return resultado


def distancia(a: str, b: str) -> int:
    """Distancia de Levenshtein. Implementada acá para no depender de nada externo."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        actual = [i]
        for j, cb in enumerate(b, start=1):
            actual.append(
                min(
                    anterior[j] + 1,  # borrar
                    actual[j - 1] + 1,  # insertar
                    anterior[j - 1] + (ca != cb),  # sustituir
                )
            )
        anterior = actual
    return anterior[-1]


def etiqueta_registrable(nombre: str) -> str:
    """El dominio que alguien registró: dos etiquetas, o tres si termina en `gob.cl`."""
    partes = nombre.lower().strip().strip(".").split(".")
    if len(partes) >= 3 and partes[-2:] == SEGUNDO_NIVEL_ESTADO.split("."):
        return ".".join(partes[-3:])
    return ".".join(partes[-2:])


def partir(registrable: str) -> tuple[str, str]:
    """Separa el núcleo del sufijo: `bancoestado.cl` -> `('bancoestado', 'cl')`."""
    sufijo = f".{SEGUNDO_NIVEL_ESTADO}"
    if registrable.endswith(sufijo):
        return registrable[: -len(sufijo)], SEGUNDO_NIVEL_ESTADO
    nucleo, _, tld = registrable.rpartition(".")
    return nucleo, tld


def _umbral_efectivo(nombre_normalizado: str, umbral: int) -> int:
    """Cuántas erratas se le toleran a una marca, según su largo.

    Es el arreglo del defecto que midió `T0.2`: `sii` tiene tres letras y con umbral 2 se parece al
    66 % de la palabra. Volvió a aparecer al enchufar el catálogo, y de la peor forma: **`bit.ly`
    entraba como suplantación del SII**. Una marca de tres letras tolera una errata; una de seis,
    dos.

    `max(1, ...)` deja siempre lugar a la errata de tecleo, que es el caso que la regla existe para
    atrapar.
    """
    return min(umbral, max(1, len(nombre_normalizado) // 3))


def _clasificar(
    marca: Marca, candidato: str, umbral: int, extra_max: int
) -> Coincidencia | None:
    nucleo, _ = partir(candidato)
    nucleo_norm = normalizar(nucleo)
    marca_norm = normalizar(marca.nombre)
    separacion = distancia(nucleo_norm, marca_norm)

    if nucleo_norm == marca_norm:
        # El mismo nombre. Si además el texto es idéntico, lo que cambió fue el TLD; si no, alguien
        # escribió un carácter que se ve igual.
        tipo = (
            TipoSuplantacion.TLD
            if nucleo.lower() == marca.nombre.lower()
            else TipoSuplantacion.HOMOGLIFO
        )
    elif nucleo_norm == marca_norm + normalizar(partir(next(iter(marca.oficiales)))[1]):
        # `bancoestado.cl` reescrito como `bancoestado--cl`: el truco de cambiar el punto por guion.
        tipo = TipoSuplantacion.PUNTO_A_GUION
    elif marca_norm in nucleo_norm and len(nucleo_norm) - len(marca_norm) <= extra_max:
        tipo = TipoSuplantacion.SUBCADENA
    elif separacion <= _umbral_efectivo(marca_norm, umbral):
        tipo = TipoSuplantacion.EDICION
    else:
        return None
    return Coincidencia(
        marca=marca.nombre,
        candidato=candidato,
        tipo=tipo,
        distancia=separacion,
        etiqueta=marca.etiqueta or marca.nombre,
    )


def detectar(
    candidato: str,
    marcas: Sequence[Marca],
    umbral: int = 2,
    extra_max: int = SUBCADENA_EXTRA_MAX,
) -> Coincidencia | None:
    """La marca que mejor explica el candidato, o `None` si no se parece a ninguna.

    `umbral` es la distancia de edición tolerada: 2 por defecto —dos erratas de tecleo— y hay un
    test
    que muestra que con 1 el filtro se vuelve más estricto.
    """
    registrable = etiqueta_registrable(candidato)
    coincidencias = [
        c
        for marca in marcas
        if registrable not in marca.oficiales
        and (c := _clasificar(marca, registrable, umbral, extra_max)) is not None
    ]
    if not coincidencias:
        return None
    # Gana la marca que explica mejor el candidato. Empate: orden alfabético, para que dos corridas
    # sobre los mismos datos den el mismo resultado.
    return min(coincidencias, key=lambda c: (c.distancia, c.marca))
