# vigia

[![gate](https://github.com/andesdevroot/vigia/actions/workflows/gate.yml/badge.svg)](https://github.com/andesdevroot/vigia/actions/workflows/gate.yml)

**Verificador ciudadano de mensajes reenviados, por WhatsApp.**

El ciudadano reenvía un mensaje sospechoso y recibe, en **1–3 segundos**, un veredicto sobre su
enlace: si es o no el sitio de la institución que el mensaje dice ser. Medido contra **342 estafas
reales** publicadas por el CSIRT: **99,7 % de cobertura**, **0 falsas acusaciones de 211**.

**La IA propone, el determinismo decide.** Un modelo llena un formulario de vocabulario cerrado —de
quién dice ser el mensaje y qué pide— y una **regla escrita** decide. El modelo nunca emite un
veredicto. La abstención es un veredicto de primera clase.

```bash
git clone https://github.com/andesdevroot/vigia
cd vigia
./gate.sh          # pytest + ruff + mypy. Debe decir "GATE EN VERDE"
```

**211 tests, sin red, en un segundo.** El núcleo de decisión usa **solo la stdlib**, y un test lo
impone.

## Cómo citar

Hay un [`CITATION.cff`](CITATION.cff) en la raíz, así que GitHub muestra el botón **Cite this
repository**. El DOI de Zenodo se agrega acá cuando el primer release esté publicado.

```bibtex
@software{vigia,
  author  = {Rivas, Cesar},
  title   = {vigia: verificador ciudadano de mensajes reenviados},
  year    = {2026},
  version = {0.1.0},
  license = {Apache-2.0},
  url     = {https://github.com/andesdevroot/vigia}
}
```

## Licencia

Código **Apache-2.0** · corpus, índice y documentación **CC BY 4.0**.

Los datos de alertas provienen del CSIRT Nacional de Chile, que los publica abiertamente.

| | |
|---|---|
| **Paper** | *The scam is in the ask, not the link* — preprint en preparación, cs.SE. **No está en este repositorio a propósito**: el paper vive en arXiv, y acá va el artefacto |
| **Requisitos** | [`spec.md`](spec.md) — 138 numerados, cada uno con el test que lo verifica |
| **Medición** | [`doc/12-MEDICION.md`](doc/12-MEDICION.md) |
| **Handoff** | [`doc/07-HANDOFF.md`](doc/07-HANDOFF.md) |
| **Publicar** | [`doc/16-PUBLICAR.md`](doc/16-PUBLICAR.md) — dónde vive cada cosa, y **el orden que no se puede invertir** |
| **Desplegar** | [`doc/17-DESPLEGAR.md`](doc/17-DESPLEGAR.md) — el `Dockerfile`, las variables y los pasos |

`doc/` es la fuente de verdad · `task.md` es la cola de trabajo · `./gate.sh` es el gate.
