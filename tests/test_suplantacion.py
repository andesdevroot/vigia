"""Detector de suplantación de marcas chilenas (T0.2a).

## Qué es y qué no es

**Es un filtro, no un veredicto.** Su trabajo es *reducir* el universo de certificados a un puñado
que valga la pena mirar, y por eso está sesgado a **recall**: prefiere marcar de más. Decidir si un
dominio marcado es malicioso es de otra capa, y confundir las dos convierte un detector en un
generador de falsas alarmas.

## La taxonomía

Describe **cómo** se parece, no cuánto. Es lo que después permite decir si una campaña reutiliza
técnicas de otra.

| tipo | ejemplo real |
|---|---|
| `homoglifo` | `banc0estado.com` — cambia un carácter por otro que se ve igual |
| `edicion` | `bancestado.com` — una edición de distancia ≤ umbral |
| `punto_a_guion` | `bancoestado--cl.xyz` — **encontrado de verdad en CT** |
| `subcadena` | `derivacionbancoestado.cl` — la marca aparece dentro |
| `tld` | `bancoestado.com` — el mismo nombre, otro TLD |

## El detalle que importa: qué es "el dominio"

En `.cl` la unidad registrable puede ser de dos o **tres** etiquetas: `gob.cl` es un segundo nivel
de
uso exclusivo del Estado, así que `claveunica.gob.cl` es la unidad y `claveunica` es el núcleo. Sin
tratar `gob.cl` aparte, el detector compararía `gob` contra la marca y no encontraría nada.
"""

from __future__ import annotations

import pytest

from vigia.suplantacion import (
    Coincidencia,
    Marca,
    TipoSuplantacion,
    detectar,
    distancia,
    etiqueta_registrable,
    normalizar,
)

MARCAS = (
    Marca(nombre="bancoestado", oficiales=frozenset({"bancoestado.cl"})),
    Marca(nombre="claveunica", oficiales=frozenset({"claveunica.gob.cl"})),
)


# --- 1. la unidad registrable ---


@pytest.mark.parametrize(
    ("nombre", "esperado"),
    [
        ("www.bancoestado.cl", "bancoestado.cl"),
        ("sub.bancoestado.cl", "bancoestado.cl"),
        ("BANCOESTADO.CL", "bancoestado.cl"),
        ("claveunica.gob.cl", "claveunica.gob.cl"),
        ("sub.claveunica.gob.cl", "claveunica.gob.cl"),
        ("a.b.c.cl", "c.cl"),
    ],
)
def test_la_unidad_registrable(nombre: str, esperado: str) -> None:
    """`gob.cl` es de tres etiquetas; el resto de `.cl`, de dos."""
    assert etiqueta_registrable(nombre) == esperado


# --- 2. la normalización ---


def test_la_normalizacion_iguala_homoglifos() -> None:
    """**Un homoglifo sirve para varias letras**, y por eso se canonicaliza por grupos.

    `0` reemplaza a la `o`; `1` reemplaza a la `l` *o* a la `i` según la palabra.
    """
    assert normalizar("banc0estado") == normalizar("bancoestado")
    assert normalizar("claveun1ca") == normalizar("claveunica")
    assert normalizar("c1aveunica") == normalizar("claveunica")


def test_la_normalizacion_saca_separadores() -> None:
    """Guiones y puntos no son información: `bancoestado--cl` y `bancoestadocl` son lo mismo."""
    assert normalizar("bancoestado--cl") == normalizar("bancoestadocl")
    assert normalizar("clave-unica") == normalizar("claveunica")
    # La salida es una CLAVE CANÓNICA, no el texto original: `bancoestadocl` sale como
    # `bancoestadoci` porque la `l` se canonicaliza a `i`. Comparar claves, no literales.


def test_la_normalizacion_no_inventa_igualdades() -> None:
    """Si normalizar de más, todo se parece a todo y el filtro deja de filtrar."""
    assert normalizar("santander") != normalizar("bancoestado")
    assert normalizar("banco") != normalizar("bancoestado")


# --- 3. distancia de edición ---


@pytest.mark.parametrize(
    ("a", "b", "esperado"),
    [
        ("bancoestado", "bancoestado", 0),
        ("bancoestado", "bancestado", 1),
        ("bancoestado", "bancoeestado", 1),
        ("bancoestado", "bancoesatdo", 2),
        ("casa", "caza", 1),
        ("", "abc", 3),
    ],
)
def test_la_distancia_de_edicion(a: str, b: str, esperado: int) -> None:
    assert distancia(a, b) == esperado


# --- 4. el veredicto del filtro ---


def test_el_dominio_oficial_no_es_suplantacion() -> None:
    assert detectar("bancoestado.cl", MARCAS) is None
    assert detectar("www.bancoestado.cl", MARCAS) is None
    assert detectar("claveunica.gob.cl", MARCAS) is None


def test_otro_dominio_del_estado_no_es_suplantacion() -> None:
    """`gob.cl` entero no puede marcarse: si no, todo el Estado es un falso positivo."""
    assert detectar("registrocivil.gob.cl", MARCAS) is None
    assert detectar("sii.gob.cl", MARCAS) is None


def test_un_dominio_ajeno_no_se_marca() -> None:
    assert detectar("google.com", MARCAS) is None
    assert detectar("mercadolibre.cl", MARCAS) is None


def test_el_punto_cambiado_por_guion() -> None:
    """El hallazgo real de la verificación de CT."""
    c = detectar("bancoestado--cl.xyz", MARCAS)
    assert c is not None
    assert c.tipo is TipoSuplantacion.PUNTO_A_GUION
    assert c.marca == "bancoestado"


def test_el_homoglifo() -> None:
    c = detectar("banc0estado.com", MARCAS)
    assert c is not None
    assert c.tipo is TipoSuplantacion.HOMOGLIFO


def test_el_mismo_nombre_con_otro_tld() -> None:
    c = detectar("bancoestado.com", MARCAS)
    assert c is not None
    assert c.tipo is TipoSuplantacion.TLD


def test_la_marca_embebida() -> None:
    c = detectar("derivacionbancoestado.cl", MARCAS)
    assert c is not None
    assert c.tipo is TipoSuplantacion.SUBCADENA


def test_la_marca_con_sufijo_de_soporte() -> None:
    """El patrón social más común: la marca más una palabra que pide confianza."""
    c = detectar("claveunica-soporte.xyz", MARCAS)
    assert c is not None
    assert c.tipo is TipoSuplantacion.SUBCADENA
    assert c.marca == "claveunica"


def test_una_edicion_corta() -> None:
    c = detectar("bancestado.com", MARCAS)
    assert c is not None
    assert c.tipo is TipoSuplantacion.EDICION
    assert c.distancia == 1


def test_el_umbral_es_configurable() -> None:
    """Con umbral 1, `bancestado` (distancia 1) entra y `bancoestadxy` (2) no."""
    assert detectar("bancestado.com", MARCAS, umbral=1) is not None
    assert detectar("bancoestadxy.com", MARCAS, umbral=1) is None


def test_gana_la_marca_mas_parecida() -> None:
    """Si dos marcas se parecen, se reporta la que explica mejor el candidato."""
    c = detectar("claveunica-soporte.xyz", MARCAS)
    assert c is not None
    assert c.marca == "claveunica"


# --- 5. lo que el filtro NO decide ---


def test_una_coincidencia_no_afirma_que_sea_malicioso() -> None:
    """El filtro devuelve **cómo se parece**, no si es un ataque.

    `bancoestadobeneficios.cl` puede ser del propio banco y el filtro lo marca igual: su trabajo es
    reducir el universo, y quien decide es la capa siguiente. Un test que exigiera lo contrario
    convertiría el filtro en un veredicto que no puede dar.
    """
    c = detectar("bancoestadobeneficios.cl", MARCAS)
    assert isinstance(c, Coincidencia)
    assert c.tipo is TipoSuplantacion.SUBCADENA


def test_la_regla_de_subcadena_tiene_cota() -> None:
    """Sin cota, la marca aparece dentro de cualquier nombre y el filtro se llena de legítimos.

    La cota es un control de **precisión** y cuesta recall a propósito: la subcadena es la regla más
    ruidosa del detector, y por eso es la única con parámetro propio.
    """
    assert detectar("claveunica-soporte.xyz", MARCAS) is not None
    assert detectar("asociacionchilenadeusuariosdeclaveunicaparatodos.cl", MARCAS) is None
    assert detectar("asociacionchilenadeusuariosdeclaveunicaparatodos.cl", MARCAS, extra_max=100)
