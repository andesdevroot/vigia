"""Enfrenta los extractores y dice **cuál gana** (`T4.5`).

## Qué compara, y contra qué vara

| | |
|---|---|
| **La vara** | `peticion.SONDAS`: 6 frases que una institución **sí** escribiría. El extractor
de referencia **marca 3 mal**, y las tres son consejos contra el phishing |
| **La sensibilidad** | una muestra del corpus: cuántos mensajes de estafa reciben el veredicto |

**No se elige un modelo por gusto.** Se mide, y gana el que acierte las 6 sondas sin perder
sensibilidad. Un modelo que no le gane al extractor de referencia no justifica su costo ni mandar el
mensaje de un ciudadano —redactado— a un tercero.

## Cómo se corre

```bash
cp .env.example .env      # y pega ahí las claves
python3 -u scripts/comparar_extractores.py
```

Cada modelo se salta si le falta la clave, así que se puede probar uno solo. **Las claves no se
imprimen.**

## Lo que cuesta

Una muestra de 40 mensajes son 40 llamadas cortas por modelo. Con DeepSeek a USD 0,32 por millón de
tokens de entrada, es **menos de un centavo**. Se puede subir con `VIGIA_MUESTRA_EXTRACTORES`.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from vigia.extractor import CacheDeExtraccion, Extractor, ExtractorLLM  # noqa: E402
from vigia.motor import Veredicto, evaluar  # noqa: E402
from vigia.peticion import (  # noqa: E402
    SONDAS,
    Peticion,
    es_peticion_indebida,
    extraer_por_palabras,
)

CORPUS = RAIZ / "corpus" / "alertas_csirt.json"


class ExtractorDeReferencia:
    """Adapta la función del baseline a la interfaz `Extractor`, para poder enfrentarlos igual.

    Que el baseline tenga que cumplir **la misma interfaz** que un modelo es parte del punto: se
    comparan como iguales, y gana el que acierte.
    """

    def extraer(self, texto: str, dice_ser: str | None) -> Peticion:
        return extraer_por_palabras(texto, dice_ser)


def leer_env() -> dict[str, str]:
    ruta = RAIZ / ".env"
    valores: dict[str, str] = {}
    if not ruta.exists():
        return valores
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if "=" in linea and not linea.lstrip().startswith("#"):
            clave, _, valor = linea.partition("=")
            valores[clave.strip()] = valor.strip()
    return valores


def modelos(env: dict[str, str]) -> list[tuple[str, Extractor]]:
    """Los extractores disponibles, según las claves que haya. **Sin claves, la lista va vacía.**"""
    disponibles: list[tuple[str, Extractor]] = [
        ("referencia (sin modelo)", ExtractorDeReferencia())
    ]
    if env.get("DEEPSEEK_API_KEY"):
        disponibles.append(
            (
                f"DeepSeek {env.get('DEEPSEEK_MODELO', 'deepseek-chat')}",
                ExtractorLLM(
                    base=env.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                    api_key=env["DEEPSEEK_API_KEY"],
                    modelo=env.get("DEEPSEEK_MODELO", "deepseek-chat"),
                ),
            )
        )
    if env.get("OPENROUTER_API_KEY"):
        disponibles.append(
            (
                f"JEV {env.get('JEV_MODELO', 'typesafe/jev-router')}",
                ExtractorLLM(
                    base=env.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                    api_key=env["OPENROUTER_API_KEY"],
                    modelo=env.get("JEV_MODELO", "typesafe/jev-router"),
                ),
            )
        )
    return disponibles


def probar_sondas(extractor: Extractor) -> tuple[int, list[str]]:
    """Cuántas de las 6 frases legítimas marca **mal**. Cuanto menos, mejor."""
    marcadas = [
        frase
        for frase in SONDAS
        if es_peticion_indebida(extractor.extraer(frase, "BancoEstado"))
    ]
    return len(marcadas), marcadas


def probar_corpus(extractor: Extractor, muestra: int) -> tuple[int, int]:
    """Cuántas estafas reciben el veredicto, de la muestra."""
    ejemplos = json.loads(CORPUS.read_text(encoding="utf-8"))[:muestra]
    acertadas = 0
    for ejemplo in ejemplos:
        texto = str(ejemplo["texto_reconstruido"])
        base = evaluar(texto)
        dice_ser = base.reclamadas[0] if base.reclamadas else None
        if evaluar(texto, peticion=extractor.extraer(texto, dice_ser)).veredicto is (
            Veredicto.PIDE_LO_INDEBIDO
        ):
            acertadas += 1
    return acertadas, len(ejemplos)


def main() -> None:
    env = leer_env()
    muestra = int(env.get("VIGIA_MUESTRA_EXTRACTORES", "40"))
    candidatos = modelos(env)

    if len(candidatos) == 1:
        print("Solo está el extractor de referencia.")
        print("Pega DEEPSEEK_API_KEY y/u OPENROUTER_API_KEY en .env y vuelve a correr.")
        print("El formato exacto está en .env.example.\n")

    print(f"VARA: {len(SONDAS)} frases que una institución sí escribiría (menos es mejor)")
    print(f"SENSIBILIDAD: {muestra} estafas del corpus (más es mejor)\n")
    print(f"{'extractor':34} {'falsas alarmas':15} {'aciertos':10} veredicto")
    print("-" * 78)

    for nombre, extractor in candidatos:
        envuelto = CacheDeExtraccion(extractor)
        falso, _ = probar_sondas(envuelto)
        aciertos, total = probar_corpus(envuelto, muestra)
        juicio = "PASA" if falso == 0 else "no sirve"
        print(f"{nombre:34} {falso} de {len(SONDAS):<12} {aciertos}/{total:<8} {juicio}")
        if falso:
            for frase in probar_sondas(envuelto)[1]:
                print(f"    marca: {frase[:70]}")
        time.sleep(0.5)

    print(
        "\nUn modelo que no deje las falsas alarmas en 0 sobre estas 6 frases no se usa:\n"
        "marcaría los mensajes que enseñan a la gente a cuidarse."
    )


if __name__ == "__main__":
    main()
