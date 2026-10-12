# vigia 0.1.0

**Verificador ciudadano de mensajes reenviados, por WhatsApp.**

El ciudadano reenvía un mensaje sospechoso y recibe, en **1–3 segundos**, un veredicto sobre su
enlace: si es o no el sitio de la institución que el mensaje dice ser.

## Los números, y de dónde salen

Medido contra **342 estafas reales** publicadas por el CSIRT Nacional de Chile:

| | |
|---|---|
| Cobertura sobre el mensaje completo | **99,7 %** (341 de 342) |
| Confirmadas contra la lista del propio Estado | **239** (69,9 %) |
| Falsas acusaciones, sobre un control invertido de 211 | **0** |
| Falsas alarmas del extractor, sobre 6 sondas | **0 de 6** (el extractor sin modelo: 3 de 6) |
| Latencia de punta a punta, por WhatsApp | **1–3 s** |
| Costo del modelo por mensaje | **≈ 0,13 CLP** (≈ 0,7 % de la respuesta de WhatsApp) |

## La IA propone, el determinismo decide

Un modelo de lenguaje llena un **formulario de vocabulario cerrado** —de quién dice ser el mensaje y
qué pide— y una **regla escrita** decide:

> Ninguna institución chilena pide su clave, sus datos personales ni una transferencia por mensaje.

**El modelo nunca emite un veredicto.** No puede inventar una categoría: lo que no esté en la lista
se descarta antes de llegar a la regla. Y la **abstención es un veredicto de primera clase**.

## El hallazgo que rehízo el diseño

**El Estado publica indicadores, no mensajes.** En el primer estudio de 45 alertas, el enlace
malicioso estaba **fuera del texto citado en 44 de 45 casos**.

Un ciudadano que reenvía exactamente lo que el Estado publicó no obtiene nada de un verificador de
enlaces en el **98 %** de los casos. Por eso el motor cubre además lo que el enlace no puede: **lo que
el mensaje pide**.

## Cómo correrlo

```bash
git clone https://github.com/andesdevroot/vigia
cd vigia
./gate.sh        # pytest + ruff + mypy. Debe decir "GATE EN VERDE"
```

**211 tests, sin red, en un segundo.** El núcleo de decisión usa **solo la stdlib**, y un test lo
impone: el veredicto tiene que ser reproducible en diez años.

## Lo que esto NO es

- **No es un clasificador de estafas.** Contesta una pregunta angosta sobre un enlace y una regla
  angosta sobre una petición, y se abstiene en todo lo demás.
- **No está entrenado.** No hay ningún modelo en el veredicto.
- **`99,7 % de cobertura` no es `99,7 % de exactitud`.** No existe un corpus público de mensajes
  legítimos chilenos, así que la exactitud contra tráfico legítimo **no está medida**.
- **No está desplegado a escala.** Cuatro mensajes reales, un canal, un país.

## Licencia

Código **Apache-2.0** · corpus, índice y documentación **CC BY 4.0**.
Los datos provienen del CSIRT Nacional de Chile, que los publica abiertamente.
