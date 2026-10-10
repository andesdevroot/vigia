"""Firma de los webhooks de Kapso (T1.4a). Módulo puro: solo stdlib.

## Por qué se verifica sobre los BYTES y no sobre el JSON

Kapso firma el cuerpo **crudo** con HMAC-SHA256 y manda el resultado en `X-Webhook-Signature`. Si se
parsea primero y se vuelve a serializar, `json.dumps` puede cambiar el espaciado y el HMAC cambia
con él: **todas** las peticiones legítimas se rechazarían, y el arreglo natural —aflojar la
comparación— es justo el que abre la puerta. Hay un test que fija que la firma del JSON
re-serializado no vale.

## Por qué la comparación es de tiempo constante

`==` corta en el primer byte distinto. Con suficientes intentos, el tiempo de respuesta revela
cuántos bytes van bien y la firma se adivina byte a byte. `hmac.compare_digest` recorre siempre
todo.

## Qué prueba la firma, y qué no

Prueba **quién mandó el cuerpo**: alguien que conoce el secreto. No prueba que el contenido sea
cierto, ni que el mensaje lo haya escrito una persona. Es una puerta, no una opinión.
"""

from __future__ import annotations

import hashlib
import hmac

LARGO_FIRMA = 64
"""SHA256 en hexadecimal: 32 bytes, 64 caracteres. Se comprueba **antes** de comparar.

Una firma de otro largo no puede ser válida, y descartarla temprano evita que un valor absurdo
llegue a la comparación.
"""


def firmar(cuerpo: bytes, secreto: str) -> str:
    """La firma que *debería* traer el cuerpo. Existe para que `es_valida` sea comprobable."""
    return hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()


def es_valida(firma: str | None, cuerpo: bytes, secreto: str) -> bool:
    """Si `firma` corresponde a `cuerpo` con `secreto`.

    Acepta mayúsculas: lo que importa es el valor, no cómo se escribió. Rechaza cualquier cosa que
    no sea hexadecimal de 64 caracteres, sin excepción y sin ruido.
    """
    if firma is None or len(firma) != LARGO_FIRMA:
        return False
    try:
        bytes.fromhex(firma)
    except ValueError:
        return False
    return hmac.compare_digest(firma.lower(), firmar(cuerpo, secreto))
