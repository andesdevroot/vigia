"""Mide el motor contra el corpus de estafas reales del CSIRT (T1.7).

## Qué mide, y qué no

Mide **si el motor ayuda** con estafas que el Estado ya identificó como tales. No mide si el
veredicto es "correcto" en abstracto, porque para eso haría falta también un corpus de mensajes
legítimos —que no existe— y la cuenta de falsas acusaciones quedaría sin denominador.

Tres resultados posibles sobre un mensaje de estafa, y **no valen lo mismo**:

| | Qué significa |
|---|---|
| **avisa** | `AJENO`: nombra el enlace que no es del Estado. Es el resultado útil |
| **mudo** | `SIN_ENCLACES`: no hay enlace que revisar. Honesto, pero el ciudadano no recibe nada |
| **grave** | `OFICIAL`: daría por bueno el enlace de una estafa. **Tiene que ser cero** |

El número que importa no es el porcentaje de acierto: es **cuántos quedan mudos**, porque esos son
estafas reales contra las que hoy no hacemos nada.
"""

from __future__ import annotations

import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from vigia.motor import Veredicto, evaluar  # noqa: E402

CORPUS = RAIZ / "corpus" / "alertas_csirt.json"


def clasificar(texto: str) -> tuple[str, str, bool]:
    """Devuelve (categoría, explicación, si nombra la marca imitada)."""
    evaluacion = evaluar(texto)
    categorias = {
        Veredicto.AJENO: "avisa",
        Veredicto.SIN_ENLACES: "mudo",
        Veredicto.OFICIAL: "GRAVE",
    }
    return categorias[evaluacion.veredicto], evaluacion.explicacion, bool(evaluacion.suplantaciones)


def medir(ejemplos: list[dict[str, object]], campo: str) -> dict[str, int]:
    cuenta = {"avisa": 0, "mudo": 0, "GRAVE": 0, "con_marca": 0}
    for ejemplo in ejemplos:
        categoria, _, con_marca = clasificar(str(ejemplo[campo]))
        cuenta[categoria] += 1
        cuenta["con_marca"] += int(con_marca)
    return cuenta


def main() -> None:
    if not CORPUS.exists():
        raise SystemExit(
            f"Falta el corpus: {CORPUS.relative_to(RAIZ)}. Corre antes cosechar_alertas.py"
        )
    ejemplos = json.loads(CORPUS.read_text(encoding="utf-8"))
    total = len(ejemplos)
    print(f"CORPUS: {total} estafas citadas por el CSIRT\n")

    for campo, titulo in (
        ("texto_citado", "La cita del CSIRT, tal cual"),
        ("texto_reconstruido", "La cita con el enlace que el informe declara"),
    ):
        cuenta = medir(ejemplos, campo)
        print(f"--- {titulo} ---")
        for clave, etiqueta in (
            ("avisa", "avisa"),
            ("mudo", "mudo"),
            ("GRAVE", "GRAVE"),
        ):
            n = cuenta[clave]
            print(f"  {etiqueta:6} {n:3}  ({n / total:.0%})")
        print(f"  de los que avisan, nombran la marca imitada: {cuenta['con_marca']}")
        print()

    print("--- los mudos: estafas reales contra las que no hacemos nada ---")
    for ejemplo in ejemplos:
        if clasificar(str(ejemplo["texto_reconstruido"]))[0] == "mudo":
            print(f"  [{ejemplo['codigo']}] {str(ejemplo['texto_reconstruido'])[:110]}")

    print("\n--- los graves: darían por bueno el enlace de una estafa ---")
    for ejemplo in ejemplos:
        if clasificar(str(ejemplo["texto_reconstruido"]))[0] == "GRAVE":
            print(f"  [{ejemplo['codigo']}] {str(ejemplo['texto_reconstruido'])[:110]}")


if __name__ == "__main__":
    main()
