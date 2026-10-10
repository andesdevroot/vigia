"""Catálogo de instituciones chilenas (T1.3). Módulo puro: solo stdlib.

## Por qué una lista de confianza es lo más peligroso que hay acá

Todo lo demás que hace el motor es **conservador**: ante la duda, no concluye. Un dominio en este
catálogo hace lo contrario — convierte un enlace ajeno en un enlace oficial. Un error acá no produce
una falsa alarma, produce un **falso negativo**: el motor daría por bueno el enlace del atacante.

Por eso cada entrada se verificó **abriendo el sitio y leyendo su certificado**, y la evidencia está
en `doc/11-MARCAS.md` con su fecha. Acá no se escribió ningún dominio de memoria.

## Por qué hacen falta dominios fuera de `.gob.cl`

`gob.cl` es exclusivo del Estado (`T0.5`), pero **no todas sus instituciones lo usan**. Carabineros,
la PDI, el SERNAC, el Servel, Correos, Metro, TVN, Codelco y la TGR tienen dominios `.cl`
históricos. Medido: **`servel.gob.cl` no existe y `servel.cl` sí**, y `fonasa.cl` es solo un
redirector hacia `fonasa.gob.cl`.

Sin el catálogo, un mensaje legítimo del Servel se leería como falso. Es el peor error posible:
enseña a desconfiar de lo verdadero.

## Cómo crece

Una entrada nueva se verifica igual que estas: se abre el sitio, se lee el certificado, y se anota
la evidencia. El test `test_los_dominios_del_catalogo_siguen_vivos` —marcado `integracion`, se corre
con `VIGIA_INTEGRACION=1`— vuelve a medir la lista entera, que es lo que impide que una lista de
confianza se pudra en silencio.
"""

from __future__ import annotations

from collections.abc import Sequence

from vigia.suplantacion import Marca

MARCAS: tuple[Marca, ...] = (
    Marca(
        nombre="claveunica",
        etiqueta="ClaveÚnica",
        oficiales=frozenset({"claveunica.gob.cl", "claveunica.cl"}),
    ),
    Marca(nombre="sii", etiqueta="SII", oficiales=frozenset({"sii.gob.cl"})),
    Marca(
        nombre="chileatiende",
        etiqueta="ChileAtiende",
        oficiales=frozenset({"chileatiende.gob.cl"}),
    ),
    Marca(nombre="subtel", etiqueta="SUBTEL", oficiales=frozenset({"subtel.gob.cl"})),
    Marca(nombre="fonasa", etiqueta="FONASA", oficiales=frozenset({"fonasa.gob.cl"})),
    Marca(nombre="servel", etiqueta="Servel", oficiales=frozenset({"servel.cl"})),
    Marca(nombre="sernac", etiqueta="SERNAC", oficiales=frozenset({"sernac.cl"})),
    Marca(nombre="carabineros", etiqueta="Carabineros", oficiales=frozenset({"carabineros.cl"})),
    Marca(nombre="pdi", etiqueta="PDI", oficiales=frozenset({"pdichile.cl"})),
    Marca(nombre="correos", etiqueta="Correos de Chile", oficiales=frozenset({"correos.cl"})),
    Marca(nombre="metro", etiqueta="Metro", oficiales=frozenset({"metro.cl"})),
    Marca(nombre="tvn", etiqueta="TVN", oficiales=frozenset({"tvn.cl"})),
    Marca(nombre="codelco", etiqueta="Codelco", oficiales=frozenset({"codelco.cl", "codelco.com"})),
    Marca(nombre="tgr", etiqueta="TGR", oficiales=frozenset({"tgr.cl"})),
)

_POR_DOMINIO: dict[str, str] = {
    dominio: (marca.etiqueta or marca.nombre) for marca in MARCAS for dominio in marca.oficiales
}


def institucion_de(registrable: str, marcas: Sequence[Marca] = MARCAS) -> str | None:
    """El nombre de la institución dueña de un dominio registrable, o `None` si no está.

    Devuelve la etiqueta para mostrar —«SERNAC»— y no el nombre normalizado con el que se compara:
    la respuesta la lee una persona. Acepta el catálogo como parámetro para que quien use uno propio
    no reciba instituciones del de acá.
    """
    if marcas is MARCAS:
        return _POR_DOMINIO.get(registrable)
    for marca in marcas:
        if registrable in marca.oficiales:
            return marca.etiqueta or marca.nombre
    return None
