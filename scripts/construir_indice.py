"""Construye el índice de enlaces que el Estado **ya determinó** fraudulentos (`T4.2`).
## De dónde sale
| Fuente | Qué aporta |
|---|---|
| `github.com/csirtcl/Fraude` | 785 informes, cada uno con sus URLs y sus dominios |
| `corpus/alertas_csirt.json` | las URLs ya cosechadas de las 342 alertas |
## Qué guarda, y qué no
**Dominio registrable → códigos de alerta.** Nada más. Ni las URLs completas —que cambian de path y
no hacen falta para decidir— ni ningún dato de nadie.
La reducción a **dominio registrable** se hace con la misma función que usa el motor
(`etiqueta_registrable`), y eso no es un detalle: si el índice guardara la URL entera y el mensaje
trajera otra ruta del mismo dominio, no calzarían.
## Por qué esto es determinista y por qué importa
**No predice nada: cita.** Si un enlace está en el índice es porque el Estado publicó que es
fraudulento, y la respuesta puede decir **cuál alerta lo dice**. Es la diferencia entre «creo que
esto es malo» y «el CSIRT lo publicó el 16 de abril de 2025».
## Ética
Solo se **lee** lo publicado con TLP:CLEAR. Las URLs se guardan reducidas a dominio y **jamás se
visitan**.
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

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from vigia.indicadores import PLATAFORMAS_COMPARTIDAS, es_sufijo_publico  # noqa: E402
from vigia.suplantacion import etiqueta_registrable  # noqa: E402

SALIDA = RAIZ / "src" / "vigia" / "datos" / "indice_ioc.json"
CORPUS = RAIZ / "corpus" / "alertas_csirt.json"
API_IOC = "https://api.github.com/repos/csirtcl/Fraude/contents/"
CRUDO_IOC = "https://raw.githubusercontent.com/csirtcl/Fraude/main/"
AGENTE = "vigia/0.0.1 (medicion academica; lectura de informes publicos TLP:CLEAR)"
PAUSA_S = 0.15
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
def anotar(indice: dict[str, set[str]], enlace: str, codigo: str) -> None:
    """Agrega el dominio registrable del enlace, si el enlace sirve para algo.
    Se descartan las **plataformas compartidas** y los **sufijos públicos** en el momento de
    construir, además de filtrarlos en la consulta. El índice tiene que ser honesto sobre lo que
    sabe: una URL en `bit.ly` no vuelve fraudulento a `bit.ly`, y `algo.com.br` no es `com.br`.
    """
    limpio = desarmar(enlace)
    if not limpio.lower().startswith(("http", "hxxp")):
        return
    partes = limpio.split("/")
    if len(partes) < 3 or not partes[2]:
        return
    host = partes[2].split(":")[0].lower()
    if len(host.split(".")) < 2:
        return
    registrable = etiqueta_registrable(host)
    if registrable in PLATAFORMAS_COMPARTIDAS or es_sufijo_publico(registrable):
        return
    indice.setdefault(registrable, set()).add(codigo)
def del_repositorio(indice: dict[str, set[str]], codigos: dict[str, str]) -> int:
    """Los 785 informes del repositorio de indicadores, uno por uno."""
    archivos = traer(API_IOC)
    try:
        listado = json.loads(archivos)
    except json.JSONDecodeError:
        return 0
    if not isinstance(listado, list):
        return 0
    leidos = 0
    for i, archivo in enumerate(listado, start=1):
        nombre = str(archivo.get("name", ""))
        if not nombre.endswith(".txt") or "_" not in nombre:
            continue
        codigo = nombre.rsplit("_", 1)[-1].removesuffix(".txt").lower()
        codigos[codigo] = nombre
        for linea in traer(CRUDO_IOC + urllib.parse.quote(nombre)).splitlines():
            texto = linea.strip()
            if texto.lower().startswith(("http", "hxxp")):
                anotar(indice, texto, codigo)
        leidos += 1
        if i % 100 == 0:
            print(f"  {i} informes leídos, {len(indice)} dominios")
        time.sleep(PAUSA_S)
    return leidos
def del_corpus(indice: dict[str, set[str]]) -> int:
    """Las URLs ya cosechadas de las alertas, que cubren los códigos que no están en el repo."""
    if not CORPUS.exists():
        return 0
    ejemplos = json.loads(CORPUS.read_text(encoding="utf-8"))
    for ejemplo in ejemplos:
        anotar(indice, str(ejemplo["url_maliciosa"]), str(ejemplo["codigo"]))
    return len(ejemplos)
def main() -> None:
    indice: dict[str, set[str]] = {}
    codigos: dict[str, str] = {}
    del_corpus(indice)
    print(f"después del corpus: {len(indice)} dominios")
    leidos = del_repositorio(indice, codigos)
    print(f"informes del repositorio leídos: {leidos}")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(
        json.dumps(
            {
                "generado": time.strftime("%Y-%m-%d"),
                "fuente": "https://github.com/csirtcl/Fraude",
                "total_dominios": len(indice),
                "dominios": {d: sorted(c) for d, c in sorted(indice.items())},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\n{len(indice)} dominios en {SALIDA.relative_to(RAIZ)}")
if __name__ == "__main__":
    main()
