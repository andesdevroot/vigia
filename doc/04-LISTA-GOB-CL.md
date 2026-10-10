# 04 — T0.5: la lista de dominios del Estado

**2026-10-04.** Respuesta: **es obtenible, y mejor que obtenible — es completa por política, no por
enumeración.** Y el hallazgo de esta tarea cambia el proyecto.

## El dato que lo cierra

`gob.cl` **no es un TLD: es un segundo nivel administrado por el Estado**. Lo opera la **ANCI**
(Agencia Nacional de Ciberseguridad) a través del CSIRT Nacional, con registro en
[nic.gob.cl](https://nic.gob.cl). Solo pueden inscribir los órganos de la Administración del Estado
del art. 1° inciso 2° de la Ley 18.575 — **con excepción de las empresas públicas creadas por ley**.

Fuente: [CSIRT Nacional — Registro de dominios gob.cl](https://csirt.gob.cl/servicios/creacion-de-dominios-gobcl/).

**Consecuencia, y es la respuesta a T0.5:** para certificar que un sitio es del Estado **no hace
falta una lista**. Basta una regla: **¿termina en `.gob.cl`?** Si sí, es del Estado, porque nadie más
puede registrarlo. La completitud no depende de que la lista esté completa — depende de una
**restricción de registro**, que es verificable y no se puede burlar sin controlar el registro.

Medido por Certificate Transparency: **221 dominios `.gob.cl`** registrables, de 3.554 certificados
(un `.gob.cl` sin certificado TLS es invisible para CT, así que la lista real es mayor — y da igual,
porque no se necesita).

## El hallazgo que cambia el proyecto

La ANCI **ya escribió la tesis de este proyecto**, como política. Textual:

> *"la resolución de nombres por sí misma no garantiza la identificabilidad [...] Para proveer
> identificabilidad, es necesario controlar la inscripción y asignación de nombres, y verificar en el
> momento de la inscripción [...] Esto es lo que **no hace NIC Chile con los dominios `.cl`:
> cualquier persona u organización puede inscribir un dominio en `.cl`**."*

> *"todos los engaños de ingeniería social (phishing, smishing, y otros) **dependen de la falta de
> identificabilidad**. Si se garantiza la identificabilidad, se disminuye grandemente la posibilidad
> de fraudes de este tipo."*

Y actúan en consecuencia:

- **Bloquean el typosquat obvio:** *"No se permite el uso de subdominios en la jerarquía `gov.cl`"*.
- **Solo alfanuméricos y guion**, sin tildes ni `ñ`, ≤63 caracteres. DNSSEC obligatorio.
- **Obligan a registrar el `.cl` equivalente**, con un solo propósito: redirigir a `.gob.cl`.
- Y crearon una **barra azul** de "Sitio oficial del Gobierno de Chile", descargable por cualquier
  sitio gubernamental.

## Lo que esto significa para el proyecto

**Malo:** la idea de la lista blanca **no es nuestra**. El Estado la inventó, la fundamentó y la
implementó. Un paper que la proponga es un paper que llega diez años tarde.

**Bueno, y es mucho mejor:** la ANCI **declaró la teoría y construyó el control, pero no publicó
ninguna medición de si funciona.** Nadie ha medido:

1. **Si el ancla de confianza se sostiene.** ¿Cuántos `.gob.cl` existen y son realmente del Estado?
   ¿Hay alguno registrado a nombre de un privado, o con nombre de empresa, contra las propias reglas?
2. **Si la barra azul sirve.** Es un control **visual**, y por lo tanto **falsificable**: cualquiera
   puede copiar el PNG y el CSS. La ANCI no publica verificación de la barra. **Es la hipótesis más
   atacable y la más barata de medir.**
3. **Dónde queda el ataque.** Si `.gob.cl` está cerrado, el atacante no lo usa: usa (a) un homoglifo
   **en el propio TLD** —`gоb.cl` con `о` cirílica, que se ve idéntico—, (b) un `.cl` que parece
   oficial, o (c) la barra copiada sobre un dominio ajeno.

## El paper que emerge

> **Measuring a national trust anchor: does `.gob.cl` give the Chilean State identifiability online?**

Un paper de **medición** sobre una política pública explícita, con su propia teoría declarada por
escrito, y **sin una sola medición de resultado**. Eso es exactamente lo que un paper de medición
debe atacar, y es el mejor terreno posible: hay una hipótesis oficial, es falsable, y nadie la probó.

**DeepSeek + JEV + Python encajan, y ahora en el lugar correcto:**

| pieza | qué hace |
|---|---|
| **Python** | censo de `.gob.cl` vía la zona DNS y CT; detección de homoglifos IDN/punycode; recolección de las páginas |
| **JEV** | clasifica **el contenido**: ¿esta página suplanta a un servicio del Estado? ¿la barra azul está sobre un dominio que no es `.gob.cl`? |
| **DeepSeek** | normaliza y resume el contenido; redacta el hallazgo |

Y el detector de T0.2a **se reusa**: la taxonomía de suplantación es exactamente la que hace falta
para medir la superficie alrededor de un ancla que ahora sí es fiable.

## Decisión

**La vía de la lista blanca queda reformulada, no cerrada:** no se propone el mecanismo —ya existe—
se **mide si funciona**. Eso es más humilde y mucho más publicable.

**Y el bloqueo real es de acceso, no de datos:** para medir el registro haría falta la lista de
inscripciones de ANCI, que no se publica. Se puede pedir por Ley de Transparencia — y eso es una
gestión, no un problema técnico.
