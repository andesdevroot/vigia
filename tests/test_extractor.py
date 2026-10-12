"""Tests de la redacción y del extractor con modelo (`T4.5`).

Sin red: el extractor recibe un `abrir` inyectado, igual que el respondedor de Kapso. Y el test que
más importa no es de comportamiento: es el que comprueba que **lo que sale no lleva datos
personales**, y que **la caché no guarda texto**.
"""

from __future__ import annotations

import json
from typing import Any

from vigia.extractor import CacheDeExtraccion, ExtractorLLM, interpretar_respuesta
from vigia.peticion import PeticionDe
from vigia.redaccion import queda_algun_dato, redactar

# --- redacción -------------------------------------------------------------------------------


def test_la_redaccion_tapa_el_correo_el_enlace_y_el_rut() -> None:
    texto = "Escriba a juan.perez@correo.cl o entre a https://malo.xyz/a. Su RUT 12.345.678-9"
    limpio = redactar(texto)
    assert "[CORREO]" in limpio
    assert "[ENLACE]" in limpio
    assert "[RUT]" in limpio
    assert "juan.perez" not in limpio
    assert "malo.xyz" not in limpio


def test_la_redaccion_tapa_telefonos_y_numeros_de_cuenta() -> None:
    for texto in ("llame al +56 9 1234 5678", "deposite en la cuenta 12345678"):
        limpio = redactar(texto)
        assert not queda_algun_dato(limpio), limpio


def test_la_redaccion_conserva_lo_que_la_extraccion_necesita() -> None:
    """Tapa lo que identifica a una persona y **conserva la petición**, lo único que se extrae."""
    limpio = redactar("BancoEstado: deposite en la cuenta 12345678 o escriba a a@b.cl")
    assert "BancoEstado" in limpio
    assert "deposite" in limpio
    assert "cuenta" in limpio


def test_la_redaccion_es_determinista() -> None:
    texto = "Su RUT 1.234.567-8 y el correo a@b.cl"
    assert redactar(texto) == redactar(texto)


def test_ningun_mensaje_del_corpus_sale_con_numeros_largos() -> None:
    """El invariante de privacidad, sobre las 342 estafas: **después de redactar no queda ningún
    número largo ni ningún correo**."""
    import pathlib

    raiz = pathlib.Path(__file__).resolve().parents[1]
    corpus = json.loads((raiz / "corpus" / "alertas_csirt.json").read_text(encoding="utf-8"))
    con_datos = [e["codigo"] for e in corpus if queda_algun_dato(redactar(str(e["texto_citado"])))]
    assert not con_datos, f"mensajes que saldrían con datos: {con_datos}"


# --- el extractor ----------------------------------------------------------------------------


def test_interpreta_una_respuesta_correcta() -> None:
    peticion = interpretar_respuesta('{"pide": ["clave", "datos_personales"]}', "BancoEstado")
    assert peticion is not None
    assert peticion.pide == (PeticionDe.CLAVE, PeticionDe.DATOS_PERSONALES)
    assert peticion.dice_ser == "BancoEstado"


def test_el_modelo_no_puede_inventar_una_categoria() -> None:
    """El vocabulario es cerrado: lo que no está en la lista **se descarta**.

    Es lo que mantiene auditable a un extractor con modelo. Si pudiera inventar categorías,
    la regla que decide dejaría de estar escrita de antemano.
    """
    peticion = interpretar_respuesta(
        '{"pide": ["clave", "chantaje", "extorsion", "transferencia"]}', None
    )
    assert peticion is not None
    assert peticion.pide == (PeticionDe.CLAVE, PeticionDe.TRANSFERENCIA)


def test_una_respuesta_rodeada_de_texto_igual_se_lee() -> None:
    peticion = interpretar_respuesta(
        'Claro, acá va:\n```json\n{"pide": ["clave"]}\n```\nEspero que sirva.', None
    )
    assert peticion is not None
    assert peticion.pide == (PeticionDe.CLAVE,)


def test_una_respuesta_ilegible_no_revienta() -> None:
    for basura in ("no soy json", "", "{}", "[1, 2, 3]", '{"pide": "clave"}'):
        peticion = interpretar_respuesta(basura, None)
        assert peticion is None or peticion.pide == (), basura


def _cuerpo(peticion: Any) -> dict[str, Any]:
    """El JSON que se mandó. Con `isinstance` para que mypy sepa que `data` es bytes."""
    datos = peticion.data
    assert isinstance(datos, bytes)
    cargado: dict[str, Any] = json.loads(datos)
    return cargado


def _respuesta_falsa(contenido: str) -> bytes:
    return json.dumps({"choices": [{"message": {"content": contenido}}]}).encode()


def test_el_extractor_manda_el_texto_redactado() -> None:
    """**El invariante de privacidad del extractor.** Lo que sale no lleva el RUT, ni el
    teléfono, ni el enlace: va redactado."""
    capturadas: list[Any] = []

    def abrir(peticion: Any) -> Any:
        capturadas.append(peticion)
        return _respuesta_falsa('{"pide": ["clave"]}')

    extractor = ExtractorLLM("https://api.ejemplo.invalid/v1", "clave", "modelo", abrir=abrir)
    peticion = extractor.extraer(
        "Su RUT 12.345.678-9, llame al +56 9 1234 5678 o entre a https://malo.xyz/a", "BancoEstado"
    )

    assert peticion.pide == (PeticionDe.CLAVE,)
    enviado = _cuerpo(capturadas[0])["messages"][0]["content"]
    for dato in ("12.345.678-9", "+56 9 1234 5678", "malo.xyz"):
        assert dato not in enviado, dato
    assert "[RUT]" in enviado and "[ENLACE]" in enviado


def test_el_extractor_pide_json_y_enumera_el_vocabulario() -> None:
    extractor = ExtractorLLM("https://x.invalid/v1", "k", "m", abrir=lambda p: b"{}")
    enviado = _cuerpo(extractor.construir_peticion("hola"))["messages"][0]["content"]
    assert "JSON" in enviado
    for valor in PeticionDe:
        assert str(valor) in enviado, valor
    assert "negación" in enviado


def test_el_extractor_avisa_de_la_negacion() -> None:
    """La vara medida del baseline es la negación: el prompt tiene que pedirla explícita."""
    extractor = ExtractorLLM("https://x.invalid/v1", "k", "m", abrir=lambda p: b"{}")
    enviado = _cuerpo(extractor.construir_peticion("hola"))["messages"][0]["content"]
    assert "nunca le pediremos" in enviado


def test_un_fallo_del_proveedor_no_acusa_a_nadie() -> None:
    """Si la API falla, la petición sale **vacía**: el motor no acusa por un error de red."""
    def abrir(peticion: Any) -> Any:
        raise TimeoutError

    extractor = ExtractorLLM("https://x.invalid/v1", "k", "m", abrir=abrir)
    peticion = extractor.extraer("deposite en la cuenta 12345678", "BancoEstado")
    assert peticion.pide == ()
    assert peticion.dice_ser == "BancoEstado"


# --- la caché --------------------------------------------------------------------------------


class ContadorDeLlamadas:
    def __init__(self) -> None:
        self.llamadas = 0

    def extraer(self, texto: str, dice_ser: str | None) -> Any:
        from vigia.peticion import Peticion

        self.llamadas += 1
        return Peticion(dice_ser=dice_ser, pide=(PeticionDe.CLAVE,))


def test_la_cache_evita_mandar_dos_veces_el_mismo_mensaje() -> None:
    """Una campaña masiva se transmite **una vez**: es lo que hace que el costo no escale con la
    cantidad de víctimas."""
    falso = ContadorDeLlamadas()
    cache = CacheDeExtraccion(falso)
    for _ in range(50):
        cache.extraer("BancoEstado: escriba su clave en el sitio", "BancoEstado")
    assert falso.llamadas == 1
    assert cache.aciertos == 49


def test_la_cache_no_guarda_el_texto() -> None:
    """**El invariante de privacidad de la caché.** Lo guardado son hashes y etiquetas."""
    cache = CacheDeExtraccion(ContadorDeLlamadas())
    texto = "BancoEstado: su RUT 12.345.678-9, escriba su clave"
    cache.extraer(texto, "BancoEstado")
    for clave in cache.claves():
        assert texto not in clave
        assert "clave" not in clave
        assert len(clave) == 64  # sha256 en hexadecimal


def test_un_proveedor_caido_no_parece_un_modelo_perfecto() -> None:
    """Sin el contador, un 401 daría **cero falsas alarmas** y el modelo parecería intachable.

    Pasó de verdad: el comparador informó «JEV PASA» mientras todas sus llamadas devolvían 401. Una
    petición vacía se ve igual que un modelo que no encontró nada.
    """
    def abrir(peticion: Any) -> Any:
        raise TimeoutError

    extractor = ExtractorLLM("https://x.invalid/v1", "k", "m", abrir=abrir)
    assert extractor.fallos == 0
    extractor.extraer("deposite en la cuenta 12345678", "BancoEstado")
    extractor.extraer("otra cosa", "BancoEstado")
    assert extractor.fallos == 2


def test_una_respuesta_que_no_se_entiende_cuenta_como_fallo() -> None:
    extractor = ExtractorLLM("https://x.invalid/v1", "k", "m", abrir=lambda p: b"no soy json")
    extractor.extraer("hola", None)
    assert extractor.fallos == 1
