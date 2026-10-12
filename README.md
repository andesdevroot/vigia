# vigia

**Verificador ciudadano de mensajes reenviados, por WhatsApp.**

El ciudadano reenvía un mensaje sospechoso y recibe, en **1–3 segundos**, un veredicto sobre su
enlace: si es o no el sitio de la institución que el mensaje dice ser. Medido contra **342 estafas
reales** publicadas por el CSIRT: **99,7 % de cobertura**, **0 falsas acusaciones de 211**.

**La IA propone, el determinismo decide.** Un modelo llena un formulario de vocabulario cerrado —de
quién dice ser el mensaje y qué pide— y una **regla escrita** decide. El modelo nunca emite un
veredicto. La abstención es un veredicto de primera clase.

```bash
./gate.sh          # pytest + ruff + mypy. Debe decir "GATE EN VERDE"
```

| | |
|---|---|
| **Paper** | [`paper/vigia-draft.md`](paper/vigia-draft.md) — borrador, cs.SE |
| **Requisitos** | [`spec.md`](spec.md) — 138 numerados, cada uno con el test que lo verifica |
| **Medición** | [`doc/12-MEDICION.md`](doc/12-MEDICION.md) |
| **Handoff** | [`doc/07-HANDOFF.md`](doc/07-HANDOFF.md) |

`doc/` es la fuente de verdad · `task.md` es la cola de trabajo · `./gate.sh` es el gate.
