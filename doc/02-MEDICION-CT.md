# 02 — T0.2: la medición de CT, y por qué cierra esta vía

**2026-10-04 · Spike terminado. Decisión tomada.**

## El número

28 consultas a Certificate Transparency, 4 marcas chilenas, 1.521 dominios registrables vistos:

```
COINCIDENCIAS: 76
  por marca:    sii 74 · bancoestado 2
```

**74 de las 76 son basura**, y el ruido tiene una causa identificable.

## Los dos defectos del detector que la medición destapó

**1. El umbral de edición no escala con el largo de la marca.** `sii` tiene tres letras, y con umbral
2 se parece al 66 % de la palabra. Resultado: `kis.si`, `cci.fr`, `asi.is`, `hki.si`. La regla tiene
que ser **proporcional al largo**, no un número fijo.

**2. No hay filtro de TLD relevante.** `.si` es el ccTLD de **Eslovenia**: entra el mundo entero. Un
dominio `.si` o `.fr` no puede suplantar a un servicio chileno, y sin ese filtro la medición no mide
lo que dice medir.

Los dos son corregibles. **Y no cambiarían la conclusión.**

## La señal real

Descontado el ruido, de 1.521 dominios:

```
bancoestado--cl.xyz        punto_a_guion
derivacionbancoestado.cl   subcadena
1 homoglifo
bancochile:  0
claveunica:  0
```

**Dos o tres dominios. Ese es el volumen.**

## La decisión, y el porqué

> **El canal de Certificate Transparency no tiene volumen para sostener este proyecto.**

Y la razón es más profunda que el ruido:

> **La suplantación no vive en el nombre del dominio.**

El phishing moderno usa **dominios desechables que no se parecen a nada**: el nombre es aleatorio o
neutro, y la marca aparece **en el contenido de la página**. Buscar parecidos de dominio es buscar
donde la suplantación no está. Además, esos sitios usan hosting gratuito y el certificado lo emite el
host, así que ni siquiera aparecen con el nombre de la marca en CT.

**Un spike de una hora mató la hipótesis antes de que costara tres semanas de construcción.** Es
exactamente para lo que existe.

## Lo que queda en pie

| | |
|---|---|
| **El detector** | Rescatable (umbral proporcional + filtro de TLD), pero encontraría ~3 dominios. **No es un paper** |
| **La detección por contenido** | Sí tiene señal —la marca está en la página— pero exige crawlear un flujo de dominios nuevos. Eso es **infraestructura**, no un proyecto de semanas |
| **El aviso antes del uso** | La parte sólida de la idea original **no depende del nombre del dominio**: depende del **mensaje** que llega al teléfono. Ahí la marca sí aparece, y es texto |

## Lo que se conserva de T0.2a

`src/vigia/suplantacion.py` queda en el repositorio con sus 30 tests: la taxonomía
(`homoglifo`/`edicion`/`punto_a_guion`/`subcadena`/`tld`) es correcta y reutilizable, y los dos
defectos están documentados acá para no volver a cometerlos. **No se borra: se deja de usar.**
