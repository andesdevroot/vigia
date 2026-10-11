"""Tests de la petición (`T4.4`).

La regla es determinista y se prueba como tal. El extractor de referencia también, **con su defecto
conocido incluido**: no entiende la negación, y eso es exactamente lo que un modelo tendría que
superar para justificarse.
"""

from __future__ import annotations

from vigia.motor import Veredicto, evaluar
from vigia.peticion import (
    SONDAS,
    Peticion,
    PeticionDe,
    es_peticion_indebida,
    extraer_por_palabras,
)


def test_pedir_la_clave_a_nombre_de_una_institucion_es_indebido() -> None:
    peticion = Peticion(dice_ser="BancoEstado", pide=(PeticionDe.CLAVE,))
    assert es_peticion_indebida(peticion)
    assert peticion.lo_indebido() == (PeticionDe.CLAVE,)


def test_pedir_una_transferencia_es_indebido() -> None:
    peticion = Peticion(dice_ser="BancoEstado", pide=(PeticionDe.TRANSFERENCIA,))
    assert es_peticion_indebida(peticion)


def test_pinchar_un_enlace_no_es_indebido() -> None:
    """Pedir que alguien pinche un enlace **es lo normal** en un aviso legítimo.

    Marcarlo convertiría la herramienta en una alarma, y una alarma que suena siempre deja de
    escucharse.
    """
    peticion = Peticion(dice_ser="BancoEstado", pide=(PeticionDe.PINCHAR, PeticionDe.LLAMAR))
    assert not es_peticion_indebida(peticion)
    assert peticion.lo_indebido() == ()


def test_sin_reclamo_no_hay_peticion_indebida() -> None:
    """**Las dos condiciones hacen falta.**

    Pedir la clave no es fraude si lo pide alguien que no dice ser un banco: puede ser una charla
    entre conocidos. Sin el reclamo, la regla no se aplica.
    """
    assert not es_peticion_indebida(Peticion(dice_ser=None, pide=(PeticionDe.CLAVE,)))


def test_sin_peticion_no_hay_nada() -> None:
    assert not es_peticion_indebida(None)
    assert not es_peticion_indebida(Peticion(dice_ser="BancoEstado", pide=()))


def test_el_extractor_de_referencia_encuentra_la_clave() -> None:
    peticion = extraer_por_palabras("Ingrese su clave para continuar", "BancoEstado")
    assert PeticionDe.CLAVE in peticion.pide
    assert es_peticion_indebida(peticion)


def test_el_extractor_de_referencia_encuentra_la_transferencia_y_los_datos() -> None:
    peticion = extraer_por_palabras(
        "Deposite en la cuenta corriente y confirme los datos de su tarjeta", "BancoEstado"
    )
    assert PeticionDe.TRANSFERENCIA in peticion.pide
    assert PeticionDe.DATOS_PERSONALES in peticion.pide


def test_el_extractor_de_referencia_ignora_las_tildes() -> None:
    peticion = extraer_por_palabras("Escriba su CONTRASEÑA", "BancoEstado")
    assert PeticionDe.CLAVE in peticion.pide


def test_el_extractor_de_referencia_es_determinista() -> None:
    texto = "Ingrese su clave y deposite"
    assert extraer_por_palabras(texto, "X") == extraer_por_palabras(texto, "X")


def test_el_extractor_de_referencia_confunde_la_negacion_y_se_declara() -> None:
    """«Nunca le pediremos su clave» contiene «clave», y el extractor de referencia lo marca.

    **Es su defecto conocido**, y es la razón de que exista: para que un modelo tenga que ganarle a
    algo. Un LLM entiende la negación; buscar señales, no. Si el modelo no supera esto, no se
    justifica.
    """
    peticion = extraer_por_palabras(
        "Recuerde: nunca le pediremos su clave por mensaje", "BancoEstado"
    )
    assert PeticionDe.CLAVE in peticion.pide
    assert es_peticion_indebida(peticion)


def test_un_mensaje_sin_enlace_que_pide_la_clave_ya_no_es_mudo() -> None:
    """**La brecha que `T4.4` cierra.** Antes esto daba `SIN_ENLACES`: el motor no decía nada."""
    texto = "Su ClaveUnica sera bloqueada. Responda este mensaje con su clave y su RUT"
    sin_peticion = evaluar(texto)
    assert sin_peticion.veredicto is Veredicto.SIN_ENLACES

    peticion = extraer_por_palabras(texto, "ClaveÚnica")
    con_peticion = evaluar(texto, peticion=peticion)
    assert con_peticion.veredicto is Veredicto.PIDE_LO_INDEBIDO
    assert "ClaveÚnica" in con_peticion.explicacion


def test_lo_confirmado_sigue_mandando_sobre_la_peticion() -> None:
    """Si el Estado ya publicó que el dominio es fraude, eso es lo más fuerte que se puede decir."""
    from vigia.indicadores import Indice

    indice = Indice({"malo.xyz": ["X-01"]})
    peticion = Peticion(dice_ser="BancoEstado", pide=(PeticionDe.CLAVE,))
    resultado = evaluar("ingrese a malo.xyz y escriba su clave", indice=indice, peticion=peticion)
    assert resultado.veredicto is Veredicto.CONFIRMADO


def test_la_respuesta_por_peticion_no_promete_seguridad() -> None:
    peticion = Peticion(dice_ser="BancoEstado", pide=(PeticionDe.CLAVE,))
    explicacion = evaluar("escriba su clave", peticion=peticion).explicacion.lower()
    assert "seguro" not in explicacion
    assert "confiar" not in explicacion


def test_sin_peticion_inyectada_el_veredicto_no_cambia() -> None:
    """El motor sin extractor se comporta exactamente como antes: la regla no se dispara sola."""
    texto = "Su ClaveUnica sera bloqueada, llame al 1510"
    assert evaluar(texto).veredicto is Veredicto.SIN_ENLACES


FALSAS_ALARMAS_CONOCIDAS = {
    "Recuerde: nunca le pediremos su clave por mensaje ni por teléfono.": "negación: «nunca»",
    "Su clave es personal. No la comparta con nadie.": "negación: «no la comparta»",
    "Para su seguridad, no entregue sus datos personales por mensaje.": "negación: «no entregue»",
}
"""Las sondas que el extractor de referencia **marca y no debería**, con su causa: no entiende
la negación.

Se declaran una por una, igual que los graves del corpus. **Si aparece una cuarta, este test
falla; y si alguna deja de ocurrir, también** — porque eso significaría que un extractor mejor
llegó, y hay que enterarse.

Y de qué se trata: las tres son **consejos contra el phishing**. El extractor de referencia marca
precisamente los mensajes que enseñan a la gente a cuidarse.
"""


def test_las_falsas_alarmas_del_extractor_de_referencia_estan_declaradas() -> None:
    """El baseline no sirve, y está medido: **3 de 6 frases legítimas marcadas como fraude**.

    Es el argumento medido a favor de un extractor con modelo, y le pone la vara: tiene que
    **entender la negación** antes de que valga la pena mandar el mensaje de alguien a un tercero.
    """
    marcadas = {
        frase
        for frase in SONDAS
        if es_peticion_indebida(extraer_por_palabras(frase, "BancoEstado"))
    }
    nuevas = sorted(marcadas - set(FALSAS_ALARMAS_CONOCIDAS))
    resueltas = sorted(set(FALSAS_ALARMAS_CONOCIDAS) - marcadas)
    assert not nuevas, f"falsas alarmas nuevas del baseline: {nuevas}"
    assert not resueltas, f"sondas que el baseline ya acierta (revisar la lista): {resueltas}"


def test_las_sondas_son_frases_que_una_institucion_escribiria() -> None:
    assert len(SONDAS) >= 6
    for frase in SONDAS:
        assert frase.endswith("."), frase
