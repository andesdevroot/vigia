"""Cosecha alertas de fraude del CSIRT para medir el motor contra estafas reales (T1.7).

## De dónde salen los ejemplos

Del **propio Estado**, y de dos lugares que se complementan:

| Fuente | Qué aporta |
|---|---|
| `github.com/csirtcl/Fraude` | 785 informes con la **URL maliciosa** y el dominio |
| `csirt.gob.cl/alertas/{codigo}/` | el **texto del mensaje**, citado entre comillas tipográficas |

Un corpus **etiquetado por la autoridad**, con fuente citable y sin inventar nada. Es exactamente el
insumo que el proyecto anterior no tenía, y por el que murió.

## Dos decisiones de fidelidad

1. **El texto se toma tal cual lo citó el CSIRT**, sin retocar. Se guarda en `texto_citado`.
2. Cuando la cita **no trae el enlace** —el CSIRT suele reportarlo aparte—, se agrega el enlace que
   el propio informe declara, y la entrada queda marcada con `url_agregada: true`. Así la medición
   puede informar **los dos números**: con la cita sola y con la reconstrucción. Inventar sin marcar
   sería lo único imperdonable acá.

## Ética

Solo se **lee** lo que el CSIRT publicó para el público, con TLP:CLEAR. Sin datos personales, sin
interactuar con los sitios maliciosos —**la URL se guarda como texto y jamás se visita**— y con
pausa entre consultas.
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
API_IOC = "https://api.github.com/repos/csirtcl/Fraude/contents/"
CRUDO_IOC = "https://raw.githubusercontent.com/csirtcl/Fraude/main/"
ALERTA = "https://csirt.gob.cl/alertas/{}/"
AGENTE = "vigia/0.0.1 (medicion academica; lectura de alertas publicas TLP:CLEAR)"
PAUSA_S = 0.4
TOPE = int(sys.argv[1]) if len(sys.argv) > 1 else 80

CITA = re.compile(r"“([^”]{25,600})”", re.S)
RUIDO_IOC = ("csirt-cl", "ioc", "informe", "tlp", "nivel", "urls y", "dominios")


class _Texto(HTMLParser):
    """El texto visible de la página, sin etiquetas."""

    def __init__(self) -> None:
        super().__init__()
        self.partes: list[str] = []
        self._saltar = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._saltar += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._saltar:
            self._saltar -= 1

    def handle_data(self, dato: str) -> None:
        if not self._saltar:
            self.partes.append(dato)

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
    """El CSIRT publica los indicadores desactivados: `hxxp`, `[.]`, `[:]`."""
    limpia = cruda.replace("hxxp", "http").replace("[.]", ".").replace("[:]", ":")
    return re.sub(r"[\s\[\]]", "", limpia).rstrip(".,;:")


def leer_ioc(contenido: str) -> tuple[list[str], list[str]]:
    """Las URLs y los dominios que el informe declara maliciosos."""
    urls: list[str] = []
    dominios: list[str] = []
    seccion = ""
    for linea in contenido.splitlines():
        texto = linea.strip()
        if texto.lower().startswith("urls y direcciones"):
            seccion = "urls"
        elif texto.lower().startswith("dominios"):
            seccion = "dominios"
        elif texto and not texto.startswith("---") and not texto.lower().startswith(RUIDO_IOC):
            if seccion == "urls" and texto.lower().startswith(("http", "hxxp")):
                urls.append(desarmar(texto))
            elif seccion == "dominios":
                dominios.append(texto.split()[0].strip())
    return urls, dominios


def texto_del_mensaje(html: str) -> str | None:
    """La cita más larga de la alerta: es el mensaje de la estafa, y el CSIRT lo cita literal."""
    analizador = _Texto()
    analizador.feed(html)
    citas = [re.sub(r"\s+", " ", c).strip() for c in CITA.findall(analizador.texto())]
    return max(citas, key=len) if citas else None


def archivos_del_repositorio() -> list[dict[str, str]]:
    crudo = traer(API_IOC)
    try:
        lista = json.loads(crudo)
    except json.JSONDecodeError:
        return []
    if not isinstance(lista, list):
        return []
    return [
        {"nombre": str(a["name"]), "descarga": str(a["download_url"])}
        for a in lista
        if isinstance(a, dict) and str(a.get("name", "")).endswith(".txt")
    ]


def main() -> None:
    # Solo los informes que citan un mensaje: de los 785 del repositorio, 499 son de
    # «Falsificación de Registros o Identidad» y **no citan ninguno**. Ir por ellos primero fue el
    # primer intento, y devolvió cero ejemplos después de cuarenta consultas.
    archivos = [
        archivo
        for archivo in archivos_del_repositorio()
        if any(t in archivo["nombre"] for t in ("Phishing", "Smishing", "Sextorsión"))
    ]
    print(f"informes de phishing o smishing disponibles: {len(archivos)}")
    if not archivos:
        raise SystemExit("No se pudo leer el repositorio de indicadores del CSIRT.")

    ejemplos: list[dict[str, object]] = []
    for archivo in archivos:
        codigo = archivo["nombre"].rsplit("_", 1)[-1].removesuffix(".txt").lower()
        # Primero la alerta: si no cita mensaje, bajar su IoC sería una consulta perdida.
        cita = texto_del_mensaje(traer(ALERTA.format(codigo)))
        if not cita:
            continue
        nombre_citado = urllib.parse.quote(archivo["nombre"])
        urls, dominios = leer_ioc(traer(CRUDO_IOC + nombre_citado))
        if not (urls or dominios):
            continue

        enlace = urls[0] if urls else f"https://{dominios[0]}/"
        agregada = enlace not in cita
        ejemplos.append(
            {
                "codigo": codigo,
                "texto_citado": cita,
                "texto_reconstruido": f"{cita} {enlace}" if agregada else cita,
                "url_agregada": agregada,
                "url_maliciosa": enlace,
                "dominios": dominios,
                "fuente_alerta": ALERTA.format(codigo),
                "fuente_ioc": CRUDO_IOC + nombre_citado,
            }
        )
        print(f"  [{len(ejemplos)}] {codigo}: {cita[:70]}...")
        if len(ejemplos) >= TOPE:
            break
        time.sleep(PAUSA_S)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(ejemplos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    con_enlace = sum(1 for e in ejemplos if not e["url_agregada"])
    print(f"\n{len(ejemplos)} ejemplos en {SALIDA.relative_to(RAIZ)}")
    print(f"  el enlace venía dentro de la cita: {con_enlace}")
    print(f"  hubo que agregarlo desde el informe: {len(ejemplos) - con_enlace}")


if __name__ == "__main__":
    main()
