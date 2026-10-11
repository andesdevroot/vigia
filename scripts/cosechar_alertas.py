"""Cosecha alertas de fraude del CSIRT para medir el motor contra estafas reales (`T1.7`, `T4.1`).

## De dónde salen los ejemplos

Del **propio Estado**, y de dos lugares que se complementan:

| Fuente | Qué aporta |
|---|---|
| `csirt.gob.cl/sitemap.xml` | **5.179 alertas**, con su código |
| `csirt.gob.cl/alertas/{codigo}/` | el **texto del mensaje** citado, y la URL en su tabla |
| `github.com/csirtcl/Fraude` | respaldo: 785 informes con la URL en texto limpio |

## Por qué el sitemap y no el repositorio de indicadores

El repositorio de IoC tiene 785 archivos, pero **solo cubre los códigos viejos** (`8fph*`, `8ffr*`).
Las campañas recientes se publican como `fph*` y `acf*` y **no están ahí**. El sitemap las tiene
todas.

## Por qué la URL se saca de las celdas de la tabla

El CSIRT publica algunas URLs **con espacios adentro** —`https: //sitio. vip/gob/home. html`— y una
expresión regular se corta en el primer espacio: la primera versión de esto devolvía
`https://mnhsmstado` en vez del dominio completo. La tabla se lee **celda por celda** y se le quitan
los espacios al contenido de cada una, que sí da la URL entera.

## Fidelidad, otra vez

El texto se toma **tal cual lo citó el CSIRT**. Cuando la cita no trae el enlace —lo normal: el
CSIRT reporta la URL aparte—, se agrega el que el propio informe declara y la entrada queda marcada
`url_agregada: true`, para que la medición pueda informar los dos números.

## Ética

Solo se **lee** lo publicado con TLP:CLEAR. Sin datos personales, sin interactuar con los sitios
maliciosos —**la URL se guarda como texto y jamás se visita**— y con pausa entre consultas.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

RAIZ = pathlib.Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "corpus" / "alertas_csirt.json"
SITEMAP = "https://csirt.gob.cl/sitemap.xml"
API_IOC = "https://api.github.com/repos/csirtcl/Fraude/contents/"
CRUDO_IOC = "https://raw.githubusercontent.com/csirtcl/Fraude/main/"
ALERTA = "https://csirt.gob.cl/alertas/{}/"
AGENTE = "vigia/0.0.1 (medicion academica; lectura de alertas publicas TLP:CLEAR)"
PAUSA_S = 0.3
OBJETIVO = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 400

PREFERENCIA = ("fph", "acf", "8fph")
"""Los códigos que citan un mensaje, primero. `fph` y `acf` son los recientes; `8fph`, los viejos.

Los de vulnerabilidades —`vsa`, `cmv`, `avc`— no citan ningún mensaje de estafa, y recorrerlos
primero costaría cientos de consultas para nada. Ya pasó con los informes de «Falsificación de
Registros»: **499 archivos para cero ejemplos**.
"""

DOMINIOS_PROPIOS = ("gob.cl", "github.com", "githubusercontent.com", "w3.org", "schema.org")
CITA = re.compile(r"“([^”]{25,600})”", re.S)
RUIDO_IOC = ("csirt-cl", "ioc", "informe", "tlp", "nivel", "urls y", "dominios")


class _Pagina(HTMLParser):
    """El texto visible y las celdas de tabla de una página."""

    def __init__(self) -> None:
        super().__init__()
        self.partes: list[str] = []
        self.celdas: list[str] = []
        self._saltar = 0
        self._celda: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._saltar += 1
        elif tag == "td":
            self._celda = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._saltar:
            self._saltar -= 1
        elif tag == "td" and self._celda is not None:
            self.celdas.append(re.sub(r"\s+", " ", "".join(self._celda)).strip())
            self._celda = None

    def handle_data(self, dato: str) -> None:
        if self._saltar:
            return
        self.partes.append(dato)
        if self._celda is not None:
            self._celda.append(dato)

    def texto(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.partes))


def traer(url: str) -> str:
    peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    try:
        with urllib.request.urlopen(peticion, timeout=30) as respuesta:
            return respuesta.read().decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        return ""


def desarmar(cruda: str) -> str:
    """El CSIRT publica los indicadores desactivados: `hxxp`, `[.]`, `[:]`, y con espacios."""
    limpia = cruda.replace("hxxp", "http").replace("[.]", ".").replace("[:]", ":")
    return re.sub(r"[\s\[\]]", "", limpia).rstrip(".,;:")


def urls_de_la_pagina(celdas: list[str]) -> list[str]:
    """Las URLs de la tabla de indicadores, leídas celda por celda.

    Leer la tabla y no el texto corrido es lo que evita el corte en el primer espacio de una URL
    publicada con espacios adentro.
    """
    encontradas: list[str] = []
    for celda in celdas:
        limpia = desarmar(celda)
        if not limpia.lower().startswith(("http", "hxxp")):
            continue
        host = limpia.split("/")[2] if "/" in limpia else ""
        if any(propio in host for propio in DOMINIOS_PROPIOS):
            continue
        encontradas.append(limpia)
    return encontradas


def leer_ioc(contenido: str) -> list[str]:
    """Respaldo para los códigos que sí están en el repositorio de indicadores."""
    urls: list[str] = []
    seccion = ""
    for linea in contenido.splitlines():
        texto = linea.strip()
        if texto.lower().startswith("urls y direcciones"):
            seccion = "urls"
        elif texto.lower().startswith("dominios"):
            seccion = ""
        elif seccion and texto.lower().startswith(("http", "hxxp")):
            urls.append(desarmar(texto))
    return urls


def texto_del_mensaje(html: str, pagina: _Pagina) -> str | None:
    citas = [re.sub(r"\s+", " ", c).strip() for c in CITA.findall(pagina.texto())]
    return max(citas, key=len) if citas else None


def codigos_del_sitemap() -> list[str]:
    xml = traer(SITEMAP)
    codigos = set(re.findall(r"csirt\.gob\.cl/alertas/([a-z0-9-]+)/", xml))

    def peso(codigo: str) -> tuple[int, str]:
        for i, prefijo in enumerate(PREFERENCIA):
            if codigo.startswith(prefijo):
                return (i, codigo)
        return (len(PREFERENCIA), codigo)

    return sorted(codigos, key=peso)


def interpretar(codigo: str, html: str) -> dict[str, object] | None:
    pagina = _Pagina()
    pagina.feed(html)
    cita = texto_del_mensaje(html, pagina)

    # Cuando el informe está en el repositorio de indicadores, **manda el informe**: trae la URL en
    # texto limpio. La tabla de la página publica algunas partidas en dos celdas y se leen cortadas
    # —`operativos.sin` en vez del dominio entero—, y un dominio inventado produce una acusación
    # falsa en la respuesta al ciudadano.
    urls: list[str] = []
    if codigo in _ARCHIVOS_IOC:
        urls = leer_ioc(traer(CRUDO_IOC + urllib.parse.quote(_ARCHIVOS_IOC[codigo])))
    if not urls:
        urls = urls_de_la_pagina(pagina.celdas)
    if not cita or not urls:
        return None

    enlace = urls[0]
    agregada = enlace not in cita
    return {
        "codigo": codigo,
        "texto_citado": cita,
        "texto_reconstruido": f"{cita} {enlace}" if agregada else cita,
        "url_agregada": agregada,
        "url_maliciosa": enlace,
        "dominios": [],
        "fuente_alerta": ALERTA.format(codigo),
        "fuente_ioc": CRUDO_IOC + urllib.parse.quote(_ARCHIVOS_IOC.get(codigo, "")),
    }


_ARCHIVOS_IOC: dict[str, str] = {}


def cargar_indice_ioc() -> None:
    crudo = traer(API_IOC)
    try:
        lista = json.loads(crudo)
    except json.JSONDecodeError:
        return
    if not isinstance(lista, list):
        return
    for archivo in lista:
        nombre = str(archivo.get("name", ""))
        if nombre.endswith(".txt") and "_" in nombre:
            codigo = nombre.rsplit("_", 1)[-1].removesuffix(".txt").lower()
            _ARCHIVOS_IOC[codigo] = nombre


def reparar(ejemplos: list[dict[str, object]]) -> int:
    """Vuelve a bajar la URL de los códigos que están en el repositorio de indicadores.

    Existe porque una primera versión leyó la URL de la tabla de la página, y algunas páginas la
    publican partida en dos celdas: quedó `operativos.sin` en vez del dominio entero, y el motor
    **nombraba un dominio inventado**. El repositorio las tiene enteras.
    """
    cambiados = 0
    for i, entrada in enumerate(ejemplos, start=1):
        codigo = str(entrada["codigo"])
        if codigo not in _ARCHIVOS_IOC:
            continue
        urls = leer_ioc(traer(CRUDO_IOC + urllib.parse.quote(_ARCHIVOS_IOC[codigo])))
        if urls and urls[0] != entrada["url_maliciosa"]:
            entrada["url_maliciosa"] = urls[0]
            if entrada["url_agregada"]:
                entrada["texto_reconstruido"] = f"{entrada['texto_citado']} {urls[0]}"
            entrada["fuente_ioc"] = CRUDO_IOC + urllib.parse.quote(_ARCHIVOS_IOC[codigo])
            cambiados += 1
        if i % 50 == 0:
            print(f"  {i} revisadas, {cambiados} corregidas")
        time.sleep(PAUSA_S)
    return cambiados


def main() -> None:
    ya: list[dict[str, object]] = []
    if SALIDA.exists():
        ya = json.loads(SALIDA.read_text(encoding="utf-8"))

    cargar_indice_ioc()

    if "--reparar" in sys.argv:
        print(f"reparando URLs de {len(ya)} entradas...")
        cambiados = reparar(ya)
        SALIDA.write_text(json.dumps(ya, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n{cambiados} URLs corregidas")
        return

    hechos = {str(e["codigo"]) for e in ya}
    print(f"ya cosechadas: {len(ya)}")
    print(f"informes en el repositorio de indicadores: {len(_ARCHIVOS_IOC)}")
    codigos = [c for c in codigos_del_sitemap() if c not in hechos]
    print(f"alertas en el sitemap por revisar: {len(codigos)}")
    print(f"objetivo: {OBJETIVO} en total\n")

    ejemplos = list(ya)
    for i, codigo in enumerate(codigos, start=1):
        if len(ejemplos) >= OBJETIVO:
            break
        entrada = interpretar(codigo, traer(ALERTA.format(codigo)))
        if entrada:
            ejemplos.append(entrada)
            SALIDA.write_text(
                json.dumps(ejemplos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print(f"  [{len(ejemplos)}] {codigo}: {str(entrada['texto_citado'])[:60]}...")
        if i % 50 == 0:
            print(f"  ... {i} revisadas, {len(ejemplos)} cosechadas")
        time.sleep(PAUSA_S)

    con_enlace = sum(1 for e in ejemplos if not e["url_agregada"])
    print(f"\n{len(ejemplos)} ejemplos en {SALIDA.relative_to(RAIZ)}")
    print(f"  el enlace venía dentro de la cita: {con_enlace}")
    print(f"  hubo que agregarlo desde el informe: {len(ejemplos) - con_enlace}")


if __name__ == "__main__":
    main()
