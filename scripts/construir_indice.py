"""Construye el índice de enlaces que el Estado **ya determinó** fraudulentos (`T4.2`, `T4.7`).

## De dónde sale, y por qué cambió

| Fuente | Qué aporta |
|---|---|
| **API Pública de Ciberseguridad** (`/api/v1/alerts/`) | **1.052 alertas** con IoC en JSON |
| `github.com/csirtcl/Fraude` | 785 informes con la URL en texto plano |
| `corpus/alertas_csirt.json` | las URLs de las 342 alertas ya cosechadas |

**La API es mucho mejor que leer HTML**: entrega `ioc_type` y `value` ya separados, así que no hay
celdas que se cortan ni URLs con espacios adentro. Se encontró en `T4.7`, y es el endpoint que la
documentación escondía detrás de JavaScript.

## Lo que la API **no** trae

**El mensaje citado, no lo trae.** De 50 alertas revisadas, **cero** traían comillas tipográficas en
su descripción: da el *resumen* del incidente y los indicadores, no el texto del SMS. Por eso el
corpus de mensajes sigue saliendo de las páginas, y por eso **no se puede crecer a 1.500**: los
códigos que citan un mensaje están agotados.

## Qué guarda, y qué no

**Dominio registrable → códigos de alerta.** Nada más. Ni las URLs completas —que cambian de ruta y
no hacen falta para decidir— ni ningún dato de nadie.

Se descartan las **plataformas compartidas** y los **sufijos públicos** al construir, además de
filtrarlos en la consulta. El índice tiene que ser honesto: una URL en `bit.ly` no vuelve
fraudulento
a `bit.ly`, y `algo.com.br` no es `com.br`.

## Ética

Solo se **lee** lo publicado con TLP:CLEAR. Las URLs se guardan **reducidas a dominio** y **jamás se
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
API = "https://csirt.gob.cl/api/v1/alerts/"
API_IOC = "https://api.github.com/repos/csirtcl/Fraude/contents/"
CRUDO_IOC = "https://raw.githubusercontent.com/csirtcl/Fraude/main/"
AGENTE = "vigia/0.0.1 (medicion academica; lectura de alertas publicas TLP:CLEAR)"
TAMANO_PAGINA = 200
PAUSA_S = 1.0
"""La API **limita las peticiones** —devuelve 429— así que se pide de a mucho y se espera."""
TIPO_DE_ENLACE = ("url", "dominio")


def traer(url: str, intentos: int = 4) -> str:
    peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    for intento in range(intentos):
        try:
            with urllib.request.urlopen(peticion, timeout=45) as respuesta:
                return respuesta.read().decode("utf-8", errors="replace")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as error:
            if intento == intentos - 1:
                print(f"    (se rinde con {url[:60]}: {type(error).__name__})")
                return ""
            time.sleep(5 * (intento + 1))
    return ""


def desarmar(cruda: str) -> str:
    """El CSIRT publica algunos indicadores desactivados: `hxxp`, `[.]`, `[:]`, y con espacios."""
    limpia = cruda.replace("hxxp", "http").replace("[.]", ".").replace("[:]", ":")
    return re.sub(r"[\s\[\]]", "", limpia).rstrip(".,;:")


def anotar(indice: dict[str, set[str]], enlace: str, codigo: str) -> None:
    """Agrega el dominio registrable del enlace, si el enlace sirve para algo."""
    limpio = desarmar(enlace)
    if not limpio.lower().startswith(("http", "hxxp")):
        limpio = f"https://{limpio}"
    partes = limpio.split("/")
    if len(partes) < 3 or not partes[2]:
        return
    host = partes[2].split(":")[0].lower()
    if len(host.split(".")) < 2:
        return
    registrable = etiqueta_registrable(host)
    if not registrable or registrable in PLATAFORMAS_COMPARTIDAS or es_sufijo_publico(registrable):
        return
    indice.setdefault(registrable, set()).add(codigo)


def de_la_api(indice: dict[str, set[str]]) -> tuple[int, int]:
    """Las 1.052 alertas con sus indicadores ya separados. Devuelve (alertas, con enlace)."""
    alertas = con_enlace = 0
    pagina = 1
    while True:
        crudo = traer(f"{API}?page={pagina}&page_size={TAMANO_PAGINA}")
        if not crudo:
            break
        try:
            datos = json.loads(crudo)
        except json.JSONDecodeError:
            break
        items = datos.get("items", [])
        if not items:
            break
        for alerta in items:
            codigo = str(alerta.get("code", "")).lower()
            if not codigo:
                continue
            alertas += 1
            antes = len(indice)
            for ioc in alerta.get("iocs") or []:
                if str(ioc.get("ioc_type", "")).lower() in TIPO_DE_ENLACE:
                    anotar(indice, str(ioc.get("value", "")), codigo)
            if len(indice) > antes:
                con_enlace += 1
        print(f"  página {pagina}: {alertas} alertas, {len(indice)} dominios")
        pagina += 1
        time.sleep(PAUSA_S)
    return alertas, con_enlace


def del_repositorio(indice: dict[str, set[str]]) -> int:
    """Los 785 informes del repositorio, que cubren alertas viejas que la API no lista."""
    try:
        listado = json.loads(traer(API_IOC))
    except json.JSONDecodeError:
        return 0
    if not isinstance(listado, list):
        return 0
    leidos = 0
    for archivo in listado:
        nombre = str(archivo.get("name", ""))
        if not nombre.endswith(".txt") or "_" not in nombre:
            continue
        codigo = nombre.rsplit("_", 1)[-1].removesuffix(".txt").lower()
        for linea in traer(CRUDO_IOC + urllib.parse.quote(nombre)).splitlines():
            texto = linea.strip()
            if texto.lower().startswith(("http", "hxxp")):
                anotar(indice, texto, codigo)
        leidos += 1
        time.sleep(0.15)
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

    print("=== corpus ===")
    print(f"  {del_corpus(indice)} alertas, {len(indice)} dominios")

    print("=== API Pública de Ciberseguridad ===")
    alertas, con_enlace = de_la_api(indice)
    print(f"  {alertas} alertas, {con_enlace} con enlace, {len(indice)} dominios")

    print("=== repositorio de indicadores ===")
    print(f"  {del_repositorio(indice)} informes, {len(indice)} dominios")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(
        json.dumps(
            {
                "generado": time.strftime("%Y-%m-%d"),
                "fuente": "https://csirt.gob.cl/api/v1/alerts/ + https://github.com/csirtcl/Fraude",
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
