"""El índice de enlaces que el Estado **ya determinó** fraudulentos (`T4.2`). Solo stdlib.

## Qué cambia

Hasta acá el motor juzgaba un enlace **por su forma**: si termina en `.gob.cl`, si es de una
institución del catálogo, si se parece a una marca. Nada de eso usa la **historia** del dominio.

Este módulo agrega lo único que el Estado ya sabe y nosotros no: **qué dominios publicó como
fraudulentos**. Y no lo deduce: lo **cita**.

## Por qué el veredicto que produce es el más fuerte

`AJENO` dice «no es de nadie que yo conozca», que es débil. `CONFIRMADO` dice «el CSIRT publicó que
este dominio es fraudulento, en la alerta tal». Lo segundo no es una inferencia: es un hecho con
fuente, y el ciudadano puede ir a leerla.

## Lo que no hace

No descarga nada en tiempo de ejecución, no decide sin fuente, y no guarda el contenido de ningún
mensaje. El índice es un archivo del paquete y la consulta es un `dict.get`.
"""

from __future__ import annotations

import json
import pathlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from vigia.suplantacion import etiqueta_registrable

RUTA_POR_DEFECTO = pathlib.Path(__file__).parent / "datos" / "indice_ioc.json"

PLANTILLA_ALERTA = "https://csirt.gob.cl/alertas/{}/"
"""La fuente que el ciudadano puede abrir. Que la respuesta la cite es la mitad del valor."""

PLATAFORMAS_COMPARTIDAS = frozenset(
    {
        # Acortadores: el enlace es corto y el destino está en otra parte.
        "bit.ly", "t.co", "tinyurl.com", "is.gd", "cutt.ly", "rb.gy", "ow.ly", "goo.gl",
        "shorturl.at", "rebrand.ly", "surl.li", "acortar.link", "buff.ly", "tiny.cc", "clck.ru",
        # Hosting gratuito y constructores de sitios.
        "web.app", "firebaseapp.com", "pages.dev", "workers.dev", "vercel.app", "netlify.app",
        "github.io", "glitch.me", "herokuapp.com", "blogspot.com", "wordpress.com",
        "wixsite.com", "weebly.com", "godaddysites.com", "myshopify.com", "duckdns.org",
        "no-ip.org", "ngrok.io",
        # Pasarelas de IPFS y nubes de archivos.
        "cloudflare-ipfs.com", "cf-ipfs.com", "ipfs.io", "googleapis.com", "drive.google.com",
        "docs.google.com", "dropbox.com", "mega.nz", "mediafire.com", "forms.gle",
        "sites.google.com",
    }
)
"""Dominios donde vive contenido de mucha gente distinta.

El CSIRT reporta **una URL** en `bit.ly`, y eso no convierte a `bit.ly` en fraudulento: aloja los
enlaces de todo el mundo. Confirmar el dominio entero condenaría a medio internet.

Medido en el índice: **70 alertas reportan un `bit.ly`**, 21 un `web.app`, 12 un `myshopify.com`.
Los acortadores y el hosting gratuito son **dónde vive** el phishing, no **qué es** — y es la misma
lección de `T0.2`, cuando el canal de Certificate Transparency resultó no tener volumen.

Se filtra **en la consulta y no solo al construir el índice**, a propósito: aunque el archivo traiga
un `bit.ly`, la respuesta nunca puede confirmarlo.
"""

SUFIJOS_PUBLICOS = ("com", "net", "org", "gov", "edu", "co", "gob")
"""Cuando el índice guarda `com.br`, no guardó un dominio: guardó un **sufijo público**.

`etiqueta_registrable` reduce por etiquetas contadas —dos, o tres para `.gob.cl`— y no conoce la
lista de sufijos públicos. Entonces `algo.com.br` se reduce a `com.br`, y confirmarlo condenaría a
**todo Brasil**. Medido: había `com.br` con 14 alertas, `com.au` con 10 y `com.np` con 8.
"""


def es_sufijo_publico(registrable: str) -> bool:
    """Si el «dominio» es en realidad un sufijo de registro: `com.br`, `com.au`, `co.uk`."""
    etiquetas = registrable.split(".")
    return len(etiquetas) == 2 and etiquetas[0] in SUFIJOS_PUBLICOS and len(etiquetas[1]) == 2


@dataclass(frozen=True, slots=True)
class Indice:
    """Los dominios que el Estado publicó como fraudulentos, con las alertas que lo dicen."""

    dominios: Mapping[str, Sequence[str]]

    def reportado(self, dominio: str) -> tuple[str, ...]:
        """Las alertas que reportan este dominio, o una tupla vacía.

        Se consulta por **dominio registrable**, que es la misma unidad con la que el motor compara
        todo lo demás: si el índice guardara la URL entera y el mensaje trajera otra ruta del mismo
        dominio, no calzarían.

        Y hay dos cosas que **nunca** se confirman, haga lo que haga el archivo: una plataforma
        compartida y un sufijo público. Ver `PLATAFORMAS_COMPARTIDAS`.
        """
        registrable = etiqueta_registrable(dominio)
        if registrable in PLATAFORMAS_COMPARTIDAS or es_sufijo_publico(registrable):
            return ()
        return tuple(self.dominios.get(registrable, ()))

    def alerta(self, codigo: str) -> str:
        """La URL pública de la alerta, para citarla."""
        return PLANTILLA_ALERTA.format(codigo)

    def __len__(self) -> int:
        return len(self.dominios)


def cargar(ruta: pathlib.Path = RUTA_POR_DEFECTO) -> Indice:
    """El índice del archivo. Si no está o está roto, devuelve uno **vacío**.

    Vacío y no una excepción: quedarse sin índice degrada el motor a lo que era antes —juzgar por la
    forma—, y eso es mucho mejor que no arrancar. Pero **no se inventa**: sin índice no hay
    confirmaciones, y el veredicto vuelve a ser el de siempre.
    """
    if not ruta.exists():
        return Indice({})
    try:
        crudo = json.loads(ruta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return Indice({})
    dominios = crudo.get("dominios") if isinstance(crudo, dict) else None
    return Indice(dominios if isinstance(dominios, dict) else {})


INDICE = cargar()
"""El índice del paquete. Se carga una vez, al importar."""
