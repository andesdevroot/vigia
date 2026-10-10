"""Spike T0.2b: cuánta superficie de suplantación existe de verdad.

NO es un test: es una medición. Consulta Certificate Transparency, junta los nombres que se parecen
a
marcas chilenas, y cuenta. El número decide si el proyecto sigue.

## Por qué variantes y no solo la marca

`crt.sh` busca por **subcadena**, así que una consulta por `bancoestado` ya devuelve todo lo que
*contiene* la marca (subcadena, punto_a_guion, tld). Pero un homoglifo (`banc0estado`) o una elisión
(`bancestado`) **no contienen la marca literal**, así que hay que consultarlos aparte. Esa asimetría
es la que hace que una sola consulta no alcance y veinte sí.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

sys.path.insert(0, "src")
from vigia.suplantacion import Coincidencia, Marca, detectar, etiqueta_registrable  # noqa: E402

OFICIALES = {
    "bancoestado": "bancoestado.cl",
    "bancochile": "bancochile.cl",
    "claveunica": "claveunica.gob.cl",
    "sii": "sii.cl",
}
MARCAS = tuple(Marca(n, frozenset({d})) for n, d in sorted(OFICIALES.items()))

# La marca literal, más las ofuscaciones que NO la contienen y por eso exigen consulta propia.
def variantes(marca: str) -> list[str]:
    return [
        marca,
        marca.replace("o", "0"),
        marca.replace("i", "1"),
        marca.replace("l", "1"),
        marca[:-1],
        marca + "cl",
        f"{marca}-cl",
    ]


def consultar(termino: str, intentos: int = 3) -> list[str]:
    url = "https://crt.sh/?" + urllib.parse.urlencode({"q": termino, "output": "json"})
    for intento in range(intentos):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                datos = json.loads(r.read().decode("utf-8", "replace"))
            nombres: list[str] = []
            for c in datos:
                for n in str(c.get("name_value", "")).splitlines():
                    n = n.strip().lower().lstrip("*.")
                    if n and " " not in n and "." in n:
                        nombres.append(n)
            return nombres
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return []          # crt.sh responde 404 cuando no hay coincidencias
            time.sleep(2 * (intento + 1))
        except Exception:
            time.sleep(2 * (intento + 1))
    return []


def main() -> None:
    vistos: set[str] = set()
    hallazgos: dict[str, Coincidencia] = {}
    consultas = 0
    for marca in MARCAS:
        for termino in variantes(marca.nombre):
            consultas += 1
            for nombre in consultar(termino):
                registrable = etiqueta_registrable(nombre)
                if registrable in vistos:
                    continue
                vistos.add(registrable)
                c = detectar(registrable, MARCAS)
                if c is not None:
                    hallazgos[registrable] = c
        print(f"  {marca.nombre}: {len(hallazgos)} acumulados", flush=True)

    print(f"\nconsultas: {consultas} | dominios registrables vistos: {len(vistos)}")
    print(f"COINCIDENCIAS: {len(hallazgos)}")
    print("\npor técnica:")
    for tipo, n in Counter(c.tipo.value for c in hallazgos.values()).most_common():
        print(f"  {tipo:16} {n}")
    print("\npor marca:")
    for marca, n in Counter(c.marca for c in hallazgos.values()).most_common():
        print(f"  {marca:16} {n}")
    print("\nmuestra:")
    for d, c in sorted(hallazgos.items())[:25]:
        print(f"  {d:44} {c.tipo.value:14} {c.marca}")


if __name__ == "__main__":
    main()
