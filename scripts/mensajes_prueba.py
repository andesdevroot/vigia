"""Arma los tres mensajes de prueba de `T3.1`, sanos y trazables.

## Qué hace

Toma tres estafas **reales y publicadas por el CSIRT**, les reemplaza **solo el TLD** por `.example`
y deja el resultado en `corpus/prueba_t31.json`, listo para mandar por WhatsApp.

## Por qué solo el TLD

El **nombre** del dominio es lo que la persona lee y lo que hay que conservar para que el mensaje
sea realista; el TLD es lo que casi nadie mira. Cambiar solo `bit.ly` → `bit.example` deja la forma
intacta y garantiza que **no resuelva**: `.example` es de uso reservado (RFC 2606) y no puede
existir.

Nadie puede pinchar y llegar a algo, y el motor juzga el enlace igual que si fuera el de verdad.

## Por qué estos tres

No son los tres más frecuentes: son tres **formas distintas de enlace**, que es lo que el
experimento mide.

| | Institución | Forma del enlace |
|---|---|---|
| **A** | Banco Ripley | **acortador** con código opaco |
| **B** | BancoEstado | dominio directo con ruta larga |
| **C** | CorreosChile | empresa del Estado, con dominio propio |

La **C** sale de una alerta que no está en el corpus de 45 —se cosechó después— y se baja acá con la
misma maquinaria, para no escribir nada a mano.

> **Y un hallazgo del propio corpus:** ninguna de las 45 alertas suplanta a un organismo del
> Estado. Todas son bancos y empresas. Eso no invalida el ancla `.gob.cl`: dice que **el fraude
> ciudadano que el Estado alcanzó a documentar es bancario**, y refuerza por qué `T1.9` cambió la
> pregunta.
"""

from __future__ import annotations

import json
import pathlib
import sys
from urllib.parse import urlsplit, urlunsplit

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "src"))

import cosechar_alertas as cs  # noqa: E402

SALIDA = RAIZ / "corpus" / "prueba_t31.json"
TEXTO_CONSULTA_MAX = 40
"""Sobre esto, la consulta se descarta: la alerta de Correos trae un `cep=` de 400 caracteres que en
un SMS real no existiría, y dejarlo haría del enlace la mitad del mensaje."""

ELEGIDOS = (
    ("8fph22-00663-01", "Banco Ripley", "acortador con codigo opaco"),
    ("8fph22-00680-01", "BancoEstado", "dominio directo con ruta larga"),
    ("8fph23-00734-01", "CorreosChile", "empresa del Estado, con dominio propio"),
)


def sanear(url: str) -> tuple[str, bool]:
    """Reemplaza el TLD por `.example`. Devuelve (url, si_se_recorto_la_consulta)."""
    partes = urlsplit(url)
    etiquetas = partes.netloc.split(".")
    seguro = ".".join([*etiquetas[:-1], "example"]) if len(etiquetas) > 1 else "sitio.example"
    consulta = partes.query if len(partes.query) <= TEXTO_CONSULTA_MAX else ""
    return urlunsplit((partes.scheme or "https", seguro, partes.path, consulta, "")), bool(
        partes.query and not consulta
    )


def traer_del_corpus(codigo: str, corpus: dict[str, dict[str, object]]) -> dict[str, object] | None:
    return corpus.get(codigo)


def traer_de_la_alerta(codigo: str) -> dict[str, object] | None:
    """Para una alerta que no está en el corpus de 45, con la misma maquinaria del cosechador."""
    listado = {a["nombre"].rsplit("_", 1)[-1].removesuffix(".txt").lower(): a for a in
               cs.archivos_del_repositorio()}
    archivo = listado.get(codigo)
    if archivo is None:
        return None
    cita = cs.texto_del_mensaje(cs.traer(cs.ALERTA.format(codigo)))
    urls, dominios = cs.leer_ioc(cs.traer(cs.CRUDO_IOC + cs.urllib.parse.quote(archivo["nombre"])))
    if not cita or not (urls or dominios):
        return None
    return {
        "texto_citado": cita,
        "url_maliciosa": urls[0] if urls else f"https://{dominios[0]}/",
        "fuente_alerta": cs.ALERTA.format(codigo),
        "fuente_ioc": cs.CRUDO_IOC + cs.urllib.parse.quote(archivo["nombre"]),
    }


def main() -> None:
    corpus = {
        str(e["codigo"]): e
        for e in json.loads((RAIZ / "corpus" / "alertas_csirt.json").read_text(encoding="utf-8"))
    }

    letras = "ABC"
    mensajes: list[dict[str, object]] = []
    for letra, (codigo, institucion, por_que) in zip(letras, ELEGIDOS, strict=True):
        fuente = traer_del_corpus(codigo, corpus) or traer_de_la_alerta(codigo)
        if fuente is None:
            print(f"  !! no se pudo traer {codigo}")
            continue
        original = str(fuente["url_maliciosa"])
        de_prueba, recortada = sanear(original)
        texto = str(fuente["texto_citado"]).strip()
        mensajes.append(
            {
                "letra": letra,
                "codigo_csirt": codigo,
                "institucion": institucion,
                "por_que": por_que,
                "texto_citado": texto,
                "url_original": original,
                "url_de_prueba": de_prueba,
                "consulta_recortada": recortada,
                "mensaje_para_enviar": f"{texto} {de_prueba}",
                "fuente_alerta": fuente["fuente_alerta"],
                "fuente_ioc": fuente.get("fuente_ioc", ""),
            }
        )

    SALIDA.write_text(
        json.dumps(mensajes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"{len(mensajes)} mensajes en {SALIDA.relative_to(RAIZ)}\n")
    for m in mensajes:
        print(f"--- {m['letra']} · {m['institucion']} · {m['por_que']}")
        print(f"    original: {m['url_original']}")
        print(f"    prueba:   {m['url_de_prueba']}"
              f"{'  (consulta recortada)' if m['consulta_recortada'] else ''}")
        print(f"    fuente:   {m['fuente_alerta']}")
        print(f"\n    MENSAJE:\n    {m['mensaje_para_enviar']}\n")


if __name__ == "__main__":
    main()
