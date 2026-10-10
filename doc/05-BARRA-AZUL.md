# 05 — T0.6: la barra azul no verifica nada

**2026-10-04.** Primera medición, y el resultado es concluyente.

## Qué es la barra

La ANCI entrega una **barra azul** con el texto *"Sitio oficial del Gobierno de Chile"* para que
cualquier sitio gubernamental la incorpore. Es su control de **identificabilidad** — el mecanismo con
el que dicen que se combate la ingeniería social.

## El hallazgo, en una línea

> **La barra es una imagen pública, sin control de acceso y sin nada que la ate al dominio.**

No hay que deducirlo: se ve en las cabeceras.

```
$ curl -I https://media.anci.gob.cl/images/ANCI_Icono_Blanco.original.svg
HTTP/2 200
content-type: image/svg+xml
access-control-allow-origin: *
access-control-allow-methods: *
```

Lo mismo para `static.anci.gob.cl` (CSS y JS). **`access-control-allow-origin: *`** significa que
cualquier sitio del mundo puede cargar esos recursos. Y no hay `Referer`, ni `X-Frame-Options`, ni
ninguna comprobación de origen.

**Y nada ata la barra a `.gob.cl`.** Buscando en la propia página de la barra no aparece ninguna
verificación de dominio, ni DNSSEC, ni un token firmado, ni un script que compruebe que el sitio
actual termina en `.gob.cl`. El único resultado de buscar `verific|DNSSEC|certificad` es texto de
navegación.

## Qué significa

**La barra es una imagen que cualquiera copia.** Un sitio falso la pega y queda **visualmente
idéntico** a uno oficial. El control de identificabilidad que la ANCI declara como su defensa contra
la ingeniería social **no aporta ninguna garantía**.

Y si la barra no sirve, **la única señal fiable que le queda al ciudadano es el dominio**: que
termine en `.gob.cl`. Esa parte **sí es sólida** — depende de una restricción de registro que el
Estado controla (T0.5).

> **El ancla está bien puesta y el letrero está suelto.**

## Lo que hay que medir

| # | pregunta | cómo | costo |
|---|---|---|---|
| 1 | **¿La barra está en sitios que no son `.gob.cl`?** | rastrear la web chilena buscando el recurso de la barra incrustado, y contar por dominio | medio |
| 2 | **¿Cuánta gente confía en la barra?** | estudio con usuarios: mostrar un sitio falso con la barra y ver si lo aprueban | alto |
| 3 | **¿El ciudadano sabe mirar el dominio?** | encuesta: pedir que distingan una URL oficial de una parecida | bajo |
| 4 | **¿Cuánto `.gob.cl` hay y cumple sus reglas?** | censo contra las reglas de ANCI (nombres de empresa, genéricos reservados) | bajo |

**La 1 es la medición del paper**: convierte "la barra es falsificable en teoría" en **"N sitios la
usan sin ser del Estado"**. Un número, no un argumento.

## Ética, y va antes que el método

- **No se construye un sitio de phishing.** Ni de prueba. La falsificación se demuestra por
  **inspección de las cabeceras**, que ya está hecha y no requiere engañar a nadie.
- La medición 1 **solo observa sitios existentes**; no interactúa con usuarios ni recoge datos
  personales.
- La medición 2 es con usuarios: requiere consentimiento y aprobación, y no se hace sin eso.
- Si se encuentran sitios que suplantan, **divulgación responsable**: primero a la ANCI, después
  publicar.

## Decisión

**La medición es viable y barata, y la hipótesis ya está confirmada por inspección.** Lo que falta no
es saber *si* la barra es falsificable —lo es— sino **cuánto se usa mal**. Eso es un número, y es la
tarea siguiente.
