"""Tests del motor de respuesta (T1.1). Rojo primero.

El motor contesta una sola cosa, y la contesta bien: **si el enlace del mensaje es del Estado**.
Todo lo demás —si el mensaje convence, si pide datos, si el sitio es bonito— no se puede saber
leyendo un texto, y por eso no se afirma.
"""

from vigia.motor import Veredicto, evaluar, extraer_enlaces
from vigia.suplantacion import Marca, TipoSuplantacion

MARCAS = (
    Marca(nombre="bancoestado", oficiales=frozenset({"bancoestado.cl"})),
    Marca(nombre="claveunica", oficiales=frozenset({"claveunica.gob.cl"})),
)


def test_sin_enlaces_da_sin_enlaces() -> None:
    resultado = evaluar("Su ClaveUnica sera bloqueada, llame al 1510")
    assert resultado.veredicto is Veredicto.SIN_ENLACES
    assert resultado.enlaces == ()


def test_enlace_del_estado_da_oficial() -> None:
    resultado = evaluar("Renueve en https://claveunica.gob.cl/portal antes del viernes")
    assert resultado.veredicto is Veredicto.OFICIAL
    assert [e.registrable for e in resultado.enlaces] == ["claveunica.gob.cl"]
    assert resultado.enlaces[0].es_del_estado


def test_enlace_ajeno_da_ajeno() -> None:
    resultado = evaluar("Renueve en https://claveunica-gob-cl.xyz antes del viernes")
    assert resultado.veredicto is Veredicto.AJENO
    assert resultado.enlaces[0].registrable == "claveunica-gob-cl.xyz"


def test_un_enlace_ajeno_basta_para_no_ser_oficial() -> None:
    """El invariante del motor.

    Un ataque real pone el enlace bueno **y** el malo en el mismo mensaje: el bueno da confianza y
    el malo es el que se aprieta. Si bastara un enlace del Estado, el motor entregaría su visto
    bueno justo al mensaje mejor construido.
    """
    resultado = evaluar("Verifique en claveunica.gob.cl y luego entre a bit.ly/renovar")
    assert "claveunica.gob.cl" in [e.registrable for e in resultado.enlaces]
    assert resultado.veredicto is Veredicto.AJENO

    for texto in (
        "claveunica.gob.cl y bit.ly/x",
        "www.sii.cl y www.sii-cl.xyz",
        "http://claveunica.gob.cl y http://claveunica.gob.cl.xyz",
    ):
        assert evaluar(texto).veredicto is Veredicto.AJENO


def test_enlace_sin_esquema_se_detecta() -> None:
    assert [e.registrable for e in extraer_enlaces("visite www.sii.cl/personas")] == ["sii.cl"]


def test_correo_electronico_no_es_enlace() -> None:
    """Un correo de contacto no es un enlace que se aprieta, y marcarlo sería una falsa alarma."""
    resultado = evaluar("Escribanos a contacto@bancoestado.cl o llame al 600 123 4567")
    assert resultado.enlaces == ()
    assert resultado.veredicto is Veredicto.SIN_ENLACES


def test_homoglifo_cirilico_no_pasa_por_oficial() -> None:
    """`claveunica.gоb.cl` con la `o` cirílica se ve igual y no es el dominio del Estado.

    Es el ataque que la vista no puede ganar y el programa sí, que es la razón de existir del
    proyecto.
    """
    resultado = evaluar("Ingrese a claveunica.g\u043eb.cl")
    assert resultado.veredicto is Veredicto.AJENO
    assert resultado.enlaces[0].ascii is False


def test_terminar_parecido_a_gob_cl_no_es_ser_del_estado() -> None:
    for host in ("claveunica.gob.cl.xyz", "claveunicagob.cl", "gob-cl.xyz", "claveunica.gob.com"):
        resultado = evaluar(f"ingrese a {host}")
        assert resultado.veredicto is Veredicto.AJENO, host


def test_punteo_final_no_ensucia_el_enlace() -> None:
    resultado = evaluar("Ingrese a https://claveunica.gob.cl.")
    assert [e.registrable for e in resultado.enlaces] == ["claveunica.gob.cl"]


def test_mayusculas_no_importan() -> None:
    resultado = evaluar("INGRESE A CLAVEUNICA.GOB.CL")
    assert resultado.veredicto is Veredicto.OFICIAL


def test_enlaces_repetidos_aparecen_una_vez() -> None:
    resultado = evaluar("claveunica.gob.cl y otra vez claveunica.gob.cl")
    assert [e.registrable for e in resultado.enlaces] == ["claveunica.gob.cl"]


def test_se_reporta_la_marca_suplantada() -> None:
    resultado = evaluar("entre a bancoestado--cl.xyz", marcas=MARCAS)
    assert [s.marca for s in resultado.suplantaciones] == ["bancoestado"]
    assert resultado.suplantaciones[0].tipo is TipoSuplantacion.PUNTO_A_GUION


def test_la_explicacion_de_oficial_no_promete_seguridad() -> None:
    """La línea roja del producto: se afirma sobre el enlace, nunca sobre el mensaje.

    Decir «es seguro» es lo único que este programa no puede hacer, porque un enlace del Estado
    dentro de un mensaje falso es exactamente el ataque mejor construido.
    """
    resultado = evaluar("Ingrese a https://claveunica.gob.cl")
    explicacion = resultado.explicacion.lower()
    assert "claveunica.gob.cl" in explicacion
    assert "seguro" not in explicacion
    assert "confiar" not in explicacion


def test_sin_enlaces_pero_dice_ser_del_estado_queda_marcado() -> None:
    resultado = evaluar("Su ClaveUnica sera bloqueada, llame al 1510")
    assert resultado.dice_ser_del_estado
    assert resultado.veredicto is Veredicto.SIN_ENLACES


def test_el_dominio_propio_de_una_institucion_no_se_acusa() -> None:
    """El peor error posible sería decirle falso a un mensaje verdadero.

    `sernac.cl` no termina en `.gob.cl`, así que sin catálogo un mensaje legítimo del SERNAC se
    leería como suplantación — y eso enseña a desconfiar de lo verdadero, que es lo contrario de lo
    que este programa tiene que lograr.
    """
    resultado = evaluar("Ingrese su reclamo en https://www.sernac.cl/reclamo")
    assert resultado.veredicto is Veredicto.OFICIAL
    assert resultado.enlaces[0].institucion == "SERNAC"
    assert "SERNAC" in resultado.explicacion


def test_un_parecido_del_dominio_de_una_institucion_si_se_acusa() -> None:
    for host in ("sernac-cl.xyz", "sernac.gob.cl.xyz", "sernaccl.com"):
        assert evaluar(f"reclame en {host}").veredicto is Veredicto.AJENO, host


def test_un_enlace_conocido_no_lava_a_uno_desconocido() -> None:
    """El invariante de T1.1 sigue en pie ahora que el catálogo amplía lo que se acepta."""
    resultado = evaluar("Reclame en sernac.cl y confirme en bit.ly/reclamo")
    assert resultado.veredicto is Veredicto.AJENO


def test_una_institucion_nombrada_en_el_texto_cuenta_como_decir_ser_del_estado() -> None:
    """El hueco que quedó a la vista al cerrar T1.4: `BANCOESTADO` no se reconocía."""
    resultado = evaluar("SERVEL: tiene una multa. Pague en bit.ly/multa")
    assert resultado.dice_ser_del_estado
    assert resultado.veredicto is Veredicto.AJENO


def test_el_nombre_tiene_que_aparecer_como_palabra_completa() -> None:
    """`sii` está en el catálogo con tres letras: no puede dispararse dentro de otra palabra."""
    assert not evaluar("Escriba asii mismo, vea bit.ly/x").dice_ser_del_estado


def test_una_palabra_ambigua_como_metro_se_marca_de_mas_y_se_acepta() -> None:
    """`metro` es el nombre del Metro y también una unidad de largo.

    La comparación es por palabra completa, así que «un metro cuadrado» cuenta como mención y la
    respuesta agrega una frase de más. **Se acepta y se declara:** la alternativa —una lista de
    excepciones por palabra— es más código del que este problema merece, y el error va en la
    dirección segura: dice de más, no calla de menos.
    """
    assert evaluar("El paño mide un metro cuadrado, vea bit.ly/paño").dice_ser_del_estado


def test_un_enlace_conocido_no_se_acusa_dentro_de_un_mensaje_ajeno() -> None:
    """El mensaje mezclado es el ataque: un enlace real de adorno y uno falso para apretar.

    Acusar al real sería, además de falso, lo más confuso posible: la respuesta tiene que separar
    «esto es del SERNAC» de «esto no es del Estado».
    """
    resultado = evaluar("Reclame en sernac.cl y confirme en bit.ly/reclamo")
    assert resultado.veredicto is Veredicto.AJENO
    assert "sernac.cl es de SERNAC" in resultado.explicacion
    assert "bit.ly NO es del Estado" in resultado.explicacion


def test_la_marca_imitada_se_nombra_como_se_escribe() -> None:
    """La respuesta la lee una persona: «ClaveÚnica», no el nombre con el que se compara."""
    resultado = evaluar("entre a claveunica-gob-cl.xyz")
    assert "ClaveÚnica" in resultado.explicacion
