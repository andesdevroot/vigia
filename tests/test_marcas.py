"""Tests del catálogo de instituciones (T1.3).

Los invariantes de acá son estructurales, y existen porque **este catálogo es la única pieza del
proyecto que amplía el camino permisivo**: un dominio de más no produce una falsa alarma, produce un
falso negativo — el motor daría por bueno el enlace del atacante.
"""

from __future__ import annotations

import socket
import urllib.error
import urllib.request

import pytest

from vigia.marcas import MARCAS, institucion_de
from vigia.suplantacion import SEPARADORES, etiqueta_registrable

NAVEGADOR = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

DOMINIOS = [dominio for marca in MARCAS for dominio in sorted(marca.oficiales)]


def test_hay_catalogo() -> None:
    assert len(MARCAS) >= 10


def test_toda_marca_tiene_al_menos_un_dominio() -> None:
    for marca in MARCAS:
        assert marca.oficiales, marca.nombre


def test_ningun_nombre_de_marca_se_repite() -> None:
    nombres = [marca.nombre for marca in MARCAS]
    assert len(nombres) == len(set(nombres))


def test_ningun_dominio_pertenece_a_dos_marcas() -> None:
    """Dos marcas con el mismo dominio harían que el nombre que se muestra dependa del orden."""
    assert len(DOMINIOS) == len(set(DOMINIOS))
    for marca in MARCAS:
        assert len(marca.oficiales) == len(set(marca.oficiales))


def test_los_dominios_ya_son_etiquetas_registrables() -> None:
    """Si no lo fueran, la comparación contra el dominio de un enlace nunca calzaría.

    `www.sernac.cl` se reduce a `sernac.cl` antes de comparar; el catálogo tiene que guardar la
    forma reducida, no la que se escribe en el navegador.
    """
    for dominio in DOMINIOS:
        assert etiqueta_registrable(dominio) == dominio, dominio


def test_los_nombres_estan_en_minusculas_y_sin_separadores() -> None:
    """El nombre se busca como palabra completa dentro del texto plegado.

    Plegado es minúsculas y sin tildes, nada más, así que el catálogo tiene que venir en minúsculas
    y sin separadores. **No** se le pide ser punto fijo de `normalizar`: esa función además confunde
    la `l` con la `i`, y `claveunica` se volvería `ciaveunica`.
    """
    for marca in MARCAS:
        assert marca.nombre == marca.nombre.lower(), marca.nombre
        assert not set(marca.nombre) & set(SEPARADORES), marca.nombre


def test_toda_marca_se_puede_mostrar_en_la_respuesta() -> None:
    """La respuesta le habla a una persona: «SERNAC», no «sernac»."""
    for marca in MARCAS:
        assert marca.etiqueta, marca.nombre
        assert marca.etiqueta != marca.nombre or marca.nombre.isupper() or marca.nombre.islower()


def test_institucion_de_encuentra_el_dominio_y_nada_mas() -> None:
    assert institucion_de("sernac.cl") == "SERNAC"
    assert institucion_de("sernac-cl.xyz") is None
    assert institucion_de("") is None


def _responde(dominio: str) -> bool:
    """Si el dominio existe y contesta.

    Tres respuestas posibles, y las tres importan:

    - **Un error HTTP cuenta como vivo.** `pdichile.cl` responde un 403 a quien no parece un
      navegador, y eso es una respuesta.
    - **Un fallo de certificado también cuenta como vivo.** `sii.gob.cl` sirve una cadena que
      Python no puede validar, pero el servidor está ahí y contesta. Lo que se busca es un dominio
      muerto o cambiado de dueño, no un sitio con el certificado impecable.
    - **Que el nombre no resuelva sí es estar muerto** — pero solo si falla en los dos hosts.

    Se prueban `www.` y la raíz porque no siempre coinciden: `fonasa.gob.cl` **no tiene registro
    DNS** y `www.fonasa.gob.cl` sí.
    """
    for host in (f"www.{dominio}", dominio):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(f"https://{host}", headers={"User-Agent": NAVEGADOR}),
                timeout=15,
            ):
                return True
        except urllib.error.HTTPError:
            return True
        except urllib.error.URLError as error:
            if isinstance(error.reason, socket.gaierror):
                continue
            return True
    return False


@pytest.mark.integracion
def test_los_dominios_del_catalogo_siguen_vivos() -> None:
    """El mecanismo contra la pudrición de una lista blanca: que alguien la vuelva a medir.

    Se salta por defecto (`-m 'not integracion'`); con `VIGIA_INTEGRACION=1` recorre el catálogo
    entero. Un dominio que dejó de existir, o que cambió de dueño, tiene que doler en un test y no
    en la cara de un ciudadano.

    Comprueba que **responda**, siguiendo redirecciones, y no que el certificado nombre a la
    institución: eso último se verificó a mano y está anotado en `doc/11-MARCAS.md`. Sigue
    redirecciones a propósito —`sii.gob.cl` manda a `homer.sii.cl` y `fonasa.gob.cl` a
    `www.fonasa.gob.cl`—, y la entrada guarda la etiqueta registrable, que es lo que se compara.
    """
    caidos = [dominio for dominio in DOMINIOS if not _responde(dominio)]
    assert not caidos, f"dominios del catálogo que no responden: {caidos}"
