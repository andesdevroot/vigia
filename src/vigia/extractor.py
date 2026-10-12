"""El extractor con modelo (`T4.5`): un LLM llena el formulario, y nada más.

## Qué hace un modelo acá, y qué no

**Extrae campos cerrados. No decide.** La decisión la toma `peticion.es_peticion_indebida`, que es
una regla escrita y citable. Esa división es todo el diseño: **un modelo en el veredicto destruiría
lo único que hace confiable a esto.**

## La vara que tiene que cumplir

El extractor de referencia —buscar señales— **marca 3 de 6 frases que una institución sí
escribiría**, y las tres son consejos contra el phishing. El modelo **tiene que ganarle**, o no
vale su costo ni la transmisión. El conjunto de conformidad está en `peticion.SONDAS`.

## Qué se le manda, y qué se guarda

**El texto redactado**, nunca el mensaje: sin correos, sin enlaces, sin RUT, sin teléfonos, sin
números. El proveedor no ve datos personales.

Y la caché guarda `hash(texto redactado) → extracción`: **seis etiquetas y un hash**, no el texto.
Una campaña masiva se transmite una vez.

## Lo que no se puede afirmar

Que el proveedor no retenga lo que recibe. **No lo controlamos.** Por eso se redacta, y por eso hay
que decirlo en la bienvenida del robot: lo que sí se garantiza es que **no salen datos personales**.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any, Protocol

from vigia.peticion import Peticion, PeticionDe
from vigia.redaccion import redactar

TIEMPO_LIMITE_S = 45

INSTRUCCION = (
    "Eres un extractor de datos. Recibes el texto de un mensaje que alguien reenvió porque le "
    "pareció sospechoso, ya sin datos personales. **No opines sobre si es fraude.** Devuelve SOLO "
    'un objeto JSON, sin explicación, con esta forma exacta:\n{"pide": [], "urgencia": null}\n\n'
    "`pide` es una lista con los valores de esta lista cerrada que el mensaje pida: "
    + ", ".join(f'"{v}"' for v in PeticionDe)
    + '.\n\n`urgencia` es uno de: "bloqueo", "plazo", "multa", "premio", o null.\n\n'
    "Ojo con la negación: «nunca le pediremos su clave» o «no comparta su clave» **no** piden la "
    "clave, y por lo tanto `pide` va vacío. Responde solo el JSON."
)
"""El prompt. Pide **solo el formulario**, y avisa de la negación porque es la vara medida."""

_RE_JSON = re.compile(r"\{.*\}", re.S)


class Extractor(Protocol):
    """Lo que el motor necesita para saber qué pide un mensaje.

    Se inyecta, igual que el respondedor de Kapso, y así se prueba sin red.
    """

    def extraer(self, texto: str, dice_ser: str | None) -> Peticion: ...


Abridor = Callable[[urllib.request.Request], Any]


def interpretar_respuesta(crudo: str, dice_ser: str | None) -> Peticion | None:
    """La respuesta del modelo como `Peticion`, **descartando lo que no esté en el vocabulario**.

    El modelo no puede inventar una categoría nueva: si devuelve algo que no está en la lista
    cerrada, se ignora. Es lo que hace que un extractor siga siendo auditable aunque lo llene un
    modelo.
    """
    encontrado = _RE_JSON.search(crudo)
    if not encontrado:
        return None
    try:
        datos = json.loads(encontrado.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(datos, dict):
        return None

    crudos = datos.get("pide")
    pedidas: list[PeticionDe] = []
    if isinstance(crudos, list):
        for valor in crudos:
            try:
                pedidas.append(PeticionDe(str(valor).strip().lower()))
            except ValueError:
                continue
    urgencia = datos.get("urgencia")
    return Peticion(
        dice_ser=dice_ser,
        pide=tuple(dict.fromkeys(pedidas)),
        urgencia=str(urgencia) if isinstance(urgencia, str) and urgencia else None,
    )


def _abrir_con_limite(peticion: urllib.request.Request) -> Any:
    with urllib.request.urlopen(peticion, timeout=TIEMPO_LIMITE_S) as respuesta:
        return respuesta.read()


class ExtractorLLM:
    """Un extractor contra una API compatible con la de OpenAI: sirve para DeepSeek y para JEV.

    **Una sola implementación y dos configuraciones** es lo que permite enfrentar modelos y decir
    cuál gana, en vez de elegir por gusto. La vara está en `peticion.SONDAS`.
    """

    def __init__(
        self, base: str, api_key: str, modelo: str, abrir: Abridor | None = None
    ) -> None:
        self._url = base.rstrip("/") + "/chat/completions"
        self._api_key = api_key
        self._modelo = modelo
        self._abrir: Abridor = abrir or _abrir_con_limite
        self.fallos = 0
        self.ultimo_error: str | None = None
        """Cuántas veces no se pudo extraer. **Se cuenta a propósito.**

        Una llamada que falla devuelve una petición vacía, y una petición vacía se ve igual que un
        modelo que no encontró nada: **un proveedor caído daría cero falsas alarmas y parecería
        perfecto**. Pasó, y por eso el contador existe.
        """

    def construir_peticion(self, texto: str) -> urllib.request.Request:
        """La petición HTTP, con **el texto redactado**. Separada para poder comprobarla sin red."""
        mensaje = f"{INSTRUCCION}\n\nMENSAJE:\n{redactar(texto)}"
        cuerpo = {
            "model": self._modelo,
            "messages": [{"role": "user", "content": mensaje}],
            "temperature": 0,
        }
        cabeceras = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        return urllib.request.Request(
            self._url, data=json.dumps(cuerpo).encode(), headers=cabeceras, method="POST"
        )

    def extraer(self, texto: str, dice_ser: str | None) -> Peticion:
        """Extrae la petición. Si algo falla devuelve una **vacía**, que no acusa a nadie."""
        try:
            crudo = self._abrir(self.construir_peticion(texto))
        except urllib.error.HTTPError as error:
            self.fallos += 1
            self.ultimo_error = f"HTTP {error.code}"
            return Peticion(dice_ser=dice_ser, pide=())
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            self.fallos += 1
            self.ultimo_error = type(error).__name__
            return Peticion(dice_ser=dice_ser, pide=())
        leida = self.leer(crudo, dice_ser)
        if leida is None:
            self.fallos += 1
            self.ultimo_error = "respuesta ilegible"
            return Peticion(dice_ser=dice_ser, pide=())
        return leida

    @staticmethod
    def leer(crudo: object, dice_ser: str | None) -> Peticion | None:
        """El contenido del modelo dentro del sobre de la respuesta."""
        if isinstance(crudo, bytes):
            crudo = crudo.decode("utf-8", "replace")
        try:
            sobre = json.loads(str(crudo))
            contenido = sobre["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            return None
        return interpretar_respuesta(str(contenido), dice_ser)


class CacheDeExtraccion:
    """Envuelve un extractor y **no repite** lo ya extraído.

    La campaña del CSIRT se manda masivamente: el mismo texto llega miles de veces. La clave es el
    hash del texto redactado, y lo guardado es **la extracción**, nunca el texto.

    En memoria y sin persistencia: dura lo que dura el proceso, que para una campaña activa alcanza.
    """

    def __init__(self, extraer: Extractor) -> None:
        self._extraer = extraer
        self._guardado: dict[str, Peticion] = {}
        self.aciertos = 0

    def __call__(self, texto: str, dice_ser: str | None) -> Peticion:
        return self.extraer(texto, dice_ser)

    def extraer(self, texto: str, dice_ser: str | None) -> Peticion:
        clave = hashlib.sha256(redactar(texto).encode()).hexdigest()
        if clave in self._guardado:
            self.aciertos += 1
            guardada = self._guardado[clave]
            return Peticion(dice_ser=dice_ser, pide=guardada.pide, urgencia=guardada.urgencia)
        peticion = self._extraer.extraer(texto, dice_ser)
        self._guardado[clave] = peticion
        return peticion

    def claves(self) -> tuple[str, ...]:
        """Las claves guardadas. Son hashes: **no hay ningún texto acá.**"""
        return tuple(self._guardado)
