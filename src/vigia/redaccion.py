"""Redacción local antes de mandar nada afuera (`T4.5`). Módulo puro: solo stdlib.

## La respuesta a «¿puede quedar en caché y después se borra?»

**No alcanza, y por una razón simple: el problema no es nuestra copia.** Cuando el texto sale a un
proveedor de modelos, la transmisión ya ocurrió, y lo que el proveedor retenga —de horas a semanas,
según su política— no lo controlamos nosotros. Borrar **nuestra** caché no borra la de él.

**Lo que sí sirve es no mandar el dato.** Y resulta que **el modelo no necesita el mensaje: necesita
la petición.** Para saber si un texto pide la clave no hacen falta el RUT, el teléfono, el número de
cuenta ni el enlace.

Así que se **redacta acá, en el servidor**, y afuera sale un texto sin datos personales.

## Y ahí sí, la caché tiene sentido — pero la del resultado, no la del mensaje

La campaña del CSIRT se manda **masivamente**: el mismo texto llega miles de veces. Se guarda
`hash(texto redactado) → extracción`, y nada más.

- **No se guarda el texto**, ni siquiera redactado: se guarda un hash y seis etiquetas.
- Un mensaje repetido **no se vuelve a mandar**: una campaña de diez mil se transmite
  una vez.

## Lo que esto **no** resuelve, y se declara

- **No quita el nombre de la institución ni el asunto**, porque son justamente lo que hay que
  extraer. Un mensaje redactado sigue diciendo «BancoEstado» y «bloqueada».
- **No protege del proveedor en general**: sigue viendo un texto. Garantiza que **no ve los
  datos personales**.
"""

from __future__ import annotations

import re

PATRONES: tuple[tuple[re.Pattern[str], str], ...] = (
    # El orden importa: lo específico antes que lo genérico, o el RUT se come el teléfono.
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "[CORREO]"),
    (re.compile(r"https?://\S+", re.IGNORECASE), "[ENLACE]"),
    (re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}\s?-?\s?[\dkK]\b"), "[RUT]"),
    (re.compile(r"\+?56\s?9\s?\d{4}\s?\d{4}\b"), "[TELEFONO]"),
    (re.compile(r"\b9\s?\d{4}\s?\d{4}\b"), "[TELEFONO]"),
    (re.compile(r"\b\d{4}\s\d{4}\b"), "[NUMERO]"),
    # **Sin fronteras de palabra, a propósito.** Un código dentro de un alfanumérico, como
    # `D541472056CL` o `BCE001547-56`, es igual de identificable y no aporta nada. Los tres
    # Los tres mensajes que se escapaban de las 342 eran así, y los encontró el test que
    # recorre el corpus entero en vez de confiar en los patrones.
    (re.compile(r"\d{6,}"), "[NUMERO]"),
)
"""Lo que se tapa, en orden. **El enlace también**, y no es un detalle: así el dominio malicioso no
sale del servidor. El motor ya lo juzgó antes, con sus propias reglas."""


def redactar(texto: str) -> str:
    """El texto sin correos, enlaces, RUT, teléfonos ni números largos.

    **Conserva lo que la extracción necesita**: el nombre de la institución, el verbo y
    la urgencia. Tapa lo que identifica a una persona.
    """
    limpio = texto
    for patron, reemplazo in PATRONES:
        limpio = patron.sub(reemplazo, limpio)
    return limpio


def queda_algun_dato(texto: str) -> bool:
    """Si después de redactar queda algo con forma de dato personal.

    Existe para poder **comprobarlo**: un test recorre el corpus y verifica que ningún texto
    conserve un número largo. Es la garantía de que la redacción no tiene un agujero silencioso.
    """
    return bool(re.search(r"\d{6,}", texto) or re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", texto))
