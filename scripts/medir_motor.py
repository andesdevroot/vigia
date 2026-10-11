"""Mide el motor contra el corpus de estafas reales del CSIRT (T1.7).

## Qué mide, y qué no

Mide **si el motor ayuda** con estafas que el Estado ya identificó como tales. No mide si el
veredicto es «correcto» en abstracto: para eso haría falta también un corpus de mensajes legítimos
—que no existe— y la cuenta de falsas acusaciones quedaría sin denominador.

Cuatro resultados posibles sobre un mensaje de estafa, y **no valen lo mismo**:

| | Qué significa |
|---|---|
| **confirmado** | `CONFIRMADO`: el Estado ya publicó que ese dominio es fraude |
| **nombra** | `NO_COINCIDE`: dice de quién dice ser y que el enlace no es suyo |
| **avisa** | `AJENO`: nombra el enlace que no es del Estado, sin saber de quién dice ser |
| **mudo** | `SIN_ENLACES`: no hay enlace que revisar. Honesto, pero no recibe nada |
| **GRAVE** | `COINCIDE` u `OFICIAL`: le dijo que el enlace es el correcto. **Tiene que ser cero** |

Desde `T1.9` la pregunta es «¿este enlace es el sitio de la institución que el mensaje dice ser?»,
así que `nombra` solo es alcanzable con las instituciones **que estén en el catálogo**. Si el
catálogo no las tiene, el motor no reconoce el reclamo y cae a `avisa`.
"""

from __future__ import annotations

import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from vigia.motor import Veredicto, evaluar  # noqa: E402

CORPUS = RAIZ / "corpus" / "alertas_csirt.json"

CATEGORIA = {
    Veredicto.CONFIRMADO: "confirmado",
    Veredicto.NO_COINCIDE: "nombra",
    Veredicto.AJENO: "avisa",
    Veredicto.SIN_ENLACES: "mudo",
    Veredicto.COINCIDE: "GRAVE",
    Veredicto.OFICIAL: "GRAVE",
}
ORDEN = ("confirmado", "nombra", "avisa", "mudo", "GRAVE")


def clasificar(texto: str) -> tuple[str, str, bool]:
    """Devuelve (categoría, explicación, si reconoció de quién dice ser)."""
    evaluacion = evaluar(texto)
    return CATEGORIA[evaluacion.veredicto], evaluacion.explicacion, bool(evaluacion.reclamadas)


def medir(
    ejemplos: list[dict[str, object]], campo: str
) -> tuple[dict[str, int], dict[str, list[str]]]:
    cuenta = dict.fromkeys(ORDEN, 0)
    cuenta["con_reclamo"] = 0
    ejemplos_de = {}
    for ejemplo in ejemplos:
        categoria, explicacion, con_reclamo = clasificar(str(ejemplo[campo]))
        cuenta[categoria] += 1
        cuenta["con_reclamo"] += int(con_reclamo)
        ejemplos_de.setdefault(categoria, []).append(
            f"[{ejemplo['codigo']}] {explicacion}"
        )
    return cuenta, ejemplos_de


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
        cuenta, por_categoria = medir(ejemplos, campo)
        print(f"--- {titulo} ---")
        for clave in ORDEN:
            print(f"  {clave:7} {cuenta[clave]:3}  ({cuenta[clave] / total:.0%})")
        print(f"  reconoció de quién dice ser: {cuenta['con_reclamo']}")
        for linea in por_categoria.get("nombra", [])[:6]:
            print(f"    {linea[:100]}")
        print()

    _, por_categoria = medir(ejemplos, "texto_reconstruido")
    print("--- los graves: darían por bueno el enlace de una estafa ---")
    graves = por_categoria.get("GRAVE", [])
    print("  ninguno" if not graves else "\n".join(f"  {g[:110]}" for g in graves))


if __name__ == "__main__":
    main()
