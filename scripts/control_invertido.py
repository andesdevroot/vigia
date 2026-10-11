"""El control invertido (`T4.3`): el mismo texto, con el enlace de la institución **real**.

## El problema que resuelve

El corpus son 342 estafas: **una sola clase**. Sin mensajes legítimos no hay denominador, y sin
denominador no se puede decir una tasa de **falsas acusaciones** — que es el error que este proyecto
no puede permitirse, porque enseña a desconfiar de lo verdadero.

## El diseño

A cada estafa del corpus se le **cambia solo el enlace**: el malicioso se reemplaza por el dominio
oficial de la institución que el propio mensaje dice ser. **El texto queda idéntico.**

Eso aísla **una sola variable**. Si el motor acusa al mensaje de control, la causa no puede ser el
texto: es que no está leyendo bien el enlace ni el reclamo.

## Qué mide, y qué NO

**Mide** la falsa acusación que induce **el texto** cuando el enlace es correcto.

**No mide** la falsa acusación sobre mensajes legítimos de verdad: la redacción, el tono y lo que
piden son distintos. Es un control **construido**, no un corpus recogido, y se declara como tal.

## Las categorías

| | Qué significa |
|---|---|
| `coincide` | el motor reconoce que el mensaje dice ser de X y el enlace es de X. **Lo correcto** |
| `oficial` | el enlace es oficial y no se reconoció el reclamo. Aceptable |
| `mudo` | no encontró enlace. No acusa, pero no ayuda |
| **`acusa`** | `NO_COINCIDE`, `AJENO` o `CONFIRMADO` sobre un enlace legítimo. **El fallo** |
"""

from __future__ import annotations

import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from vigia.marcas import MARCAS  # noqa: E402
from vigia.motor import Veredicto, evaluar  # noqa: E402

CORPUS = RAIZ / "corpus" / "alertas_csirt.json"
SALIDA = RAIZ / "corpus" / "control_invertido.json"

ACUSA = (Veredicto.NO_COINCIDE, Veredicto.AJENO, Veredicto.CONFIRMADO)
CATEGORIA = {
    Veredicto.COINCIDE: "coincide",
    Veredicto.OFICIAL: "oficial",
    Veredicto.SIN_ENLACES: "mudo",
    Veredicto.NO_COINCIDE: "acusa",
    Veredicto.AJENO: "acusa",
    Veredicto.CONFIRMADO: "acusa",
}
ORDEN = ("coincide", "oficial", "mudo", "acusa")


def dominio_oficial(etiqueta: str) -> str | None:
    """El dominio oficial de la institución, buscado por su etiqueta para mostrar."""
    for marca in MARCAS:
        if (marca.etiqueta or marca.nombre) == etiqueta and marca.oficiales:
            return sorted(marca.oficiales)[0]
    return None


def invertir(ejemplo: dict[str, object]) -> dict[str, object] | None:
    """El mensaje con el enlace legítimo, o `None` si no se reconoce a quién suplanta."""
    original = str(ejemplo["texto_reconstruido"])
    reclamadas = evaluar(original).reclamadas
    if not reclamadas:
        return None
    dominio = dominio_oficial(reclamadas[0])
    if not dominio:
        return None
    de_control = original.replace(str(ejemplo["url_maliciosa"]), f"https://{dominio}/")
    if de_control == original:
        return None
    return {
        "codigo": ejemplo["codigo"],
        "institucion": reclamadas[0],
        "dominio_oficial": dominio,
        "url_maliciosa": ejemplo["url_maliciosa"],
        "texto_de_control": de_control,
        "fuente_alerta": ejemplo["fuente_alerta"],
    }


def main() -> None:
    ejemplos = json.loads(CORPUS.read_text(encoding="utf-8"))
    controles = [c for e in ejemplos if (c := invertir(e)) is not None]

    cuenta = dict.fromkeys(ORDEN, 0)
    acusados: list[dict[str, object]] = []
    for control in controles:
        veredicto = evaluar(str(control["texto_de_control"])).veredicto
        categoria = CATEGORIA[veredicto]
        cuenta[categoria] += 1
        if veredicto in ACUSA:
            control["veredicto"] = veredicto.value
            control["explicacion"] = evaluar(str(control["texto_de_control"])).explicacion
            acusados.append(control)

    SALIDA.write_text(json.dumps(controles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    total = len(controles)
    print(f"CONTROL INVERTIDO: {total} mensajes de {len(ejemplos)}")
    print(f"  (los otros {len(ejemplos) - total} no dicen ser de una institución del catálogo)\n")
    for clave in ORDEN:
        print(f"  {clave:9} {cuenta[clave]:3}  ({cuenta[clave] / total:.0%})")
    print(f"\n  FALSAS ACUSACIONES: {cuenta['acusa']} de {total} = {cuenta['acusa'] / total:.1%}")
    print(f"\n  guardado en {SALIDA.relative_to(RAIZ)}")
    for acusado in acusados[:10]:
        print(f"\n  [{acusado['codigo']}] {acusado['veredicto']}"
              f" — dice ser de {acusado['institucion']}")
        print(f"    enlace: {acusado['dominio_oficial']}")
        print(f"    {str(acusado['explicacion'])[:150]}")


if __name__ == "__main__":
    main()
