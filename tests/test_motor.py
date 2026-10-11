"""Tests del motor de respuesta.

La pregunta cambió en `T1.9`, y la cambió el corpus de `T1.7`: **«¿este enlace es el sitio de la
institución que el mensaje dice ser?»**, y no «¿es del Estado?».

El motivo está medido: en 45 estafas reales del CSIRT, **el 47 % suplanta a Banco Ripley**, un banco
privado. A esa persona, «el enlace NO es del Estado» le dice algo cierto y le deja la duda intacta.

Lo que **no** cambia es la línea roja: se afirma sobre el enlace y sobre la coherencia entre lo
que el mensaje dice y lo que enlaza. Nunca sobre el mensaje.
"""

from vigia.indicadores import Indice
from vigia.motor import Veredicto, evaluar, extraer_enlaces
from vigia.suplantacion import Marca, TipoSuplantacion

MARCAS = (
    Marca(
        nombre="bancoestado",
        etiqueta="BancoEstado",
        alias=("banco estado", "banco de estado"),
        oficiales=frozenset({"bancoestado.cl"}),
    ),
    Marca(
        nombre="claveunica",
        etiqueta="ClaveÚnica",
        alias=("clave unica",),
        oficiales=frozenset({"claveunica.gob.cl"}),
    ),
    Marca(
        nombre="bancoripley",
        etiqueta="Banco Ripley",
        alias=("banco ripley", "ripley"),
        oficiales=frozenset({"bancoripley.cl"}),
    ),
)

CON_PROBLEMA = (Veredicto.AJENO, Veredicto.NO_COINCIDE)
"""Los dos veredictos que le dicen a la persona que hay algo mal. Nunca `COINCIDE` ni `OFICIAL`."""


def test_sin_enlaces_da_sin_enlaces() -> None:
    resultado = evaluar("Su ClaveUnica sera bloqueada, llame al 1510")
    assert resultado.veredicto is Veredicto.SIN_ENLACES
    assert resultado.enlaces == ()


def test_dice_ser_de_claveunica_y_enlaza_a_claveunica_da_coincide() -> None:
    resultado = evaluar("ClaveUnica le informa: renueve en https://claveunica.gob.cl/portal")
    assert resultado.veredicto is Veredicto.COINCIDE
    assert resultado.reclamadas == ("ClaveÚnica",)
    assert [e.registrable for e in resultado.enlaces] == ["claveunica.gob.cl"]


def test_dice_ser_de_claveunica_y_enlaza_a_otro_da_no_coincide() -> None:
    """El caso que la pregunta nueva hace visible, y que la vieja no podía nombrar."""
    resultado = evaluar("Renueve su ClaveUnica en https://claveunica-gob-cl.xyz")
    assert resultado.veredicto is Veredicto.NO_COINCIDE
    assert "ClaveÚnica" in resultado.explicacion
    assert "claveunica-gob-cl.xyz" in resultado.explicacion


def test_dice_ser_de_un_banco_y_enlaza_al_banco_da_coincide() -> None:
    resultado = evaluar("Banco Ripley: su cuenta fue bloqueada. Ingrese a bancoripley.cl",
                        marcas=MARCAS)
    assert resultado.veredicto is Veredicto.COINCIDE
    assert resultado.reclamadas == ("Banco Ripley",)


def test_dice_ser_de_un_banco_y_enlaza_a_otro_lado_da_no_coincide() -> None:
    """El caso del corpus: «Banco Ripley» con un enlace que no es del banco."""
    resultado = evaluar(
        "Banco Ripley, detectamos una actividad inusual. Ingrese a bancoripley-cl.xyz",
        marcas=MARCAS,
    )
    assert resultado.veredicto is Veredicto.NO_COINCIDE
    assert "Banco Ripley" in resultado.explicacion


def test_el_alias_con_espacio_tambien_cuenta_como_reclamo() -> None:
    """El corpus escribe «Banco Ripley» y «bancoripley»; las dos formas tienen que contar."""
    for texto in ("Banco Ripley le informa", "bancoripley le informa"):
        assert evaluar(f"{texto}, ingrese a otro-lado.xyz", marcas=MARCAS).reclamadas == (
            "Banco Ripley",
        )


def test_un_enlace_ajeno_rompe_la_coincidencia() -> None:
    """El invariante del motor, ahora sobre la coherencia.

    Un ataque real pone el enlace bueno **y** el malo en el mismo mensaje: el bueno da confianza y
    el malo es el que se aprieta. Si bastara un enlace legítimo, el motor entregaría su visto bueno
    justo al mensaje mejor construido.
    """
    resultado = evaluar("Banco Ripley: verifique en bancoripley.cl y entre a bit.ly/renovar",
                        marcas=MARCAS)
    assert "bancoripley.cl" in [e.registrable for e in resultado.enlaces]
    assert resultado.veredicto is Veredicto.NO_COINCIDE


def test_un_enlace_del_estado_ajeno_al_reclamo_da_no_coincide() -> None:
    """Un enlace del Estado no salva a un mensaje que dice ser de otra institución."""
    resultado = evaluar("Banco Ripley le informa: ingrese a claveunica.gob.cl", marcas=MARCAS)
    assert resultado.veredicto is Veredicto.NO_COINCIDE


def test_sin_reclamo_reconocido_cae_al_veredicto_del_enlace() -> None:
    """Cuando no se sabe de quién dice ser, queda la respuesta vieja, que sigue siendo cierta."""
    del_estado = evaluar("Ingrese a https://www.gob.cl/atencion")
    assert del_estado.veredicto is Veredicto.OFICIAL
    assert del_estado.reclamadas == ()

    ajeno = evaluar("Ingrese a https://un-sitio-cualquiera.xyz")
    assert ajeno.veredicto is Veredicto.AJENO
    assert "NO es del Estado" in ajeno.explicacion


def test_un_punto_sin_espacio_no_inventa_un_dominio() -> None:
    """`operativos.Sin` no es un dominio: es un punto sin espacio después.

    Un SMS escrito así producía que el motor nombrara en la respuesta un dominio **que no existe**,
    como si fuera el sitio del atacante. Lo encontró el corpus de 342 —casos `8fph22-00693-01`,
    `8fph23-00714-01` y `8fph23-00748-01`—, no un test unitario.
    """
    for texto in (
        "nuestros servidores ya estan operativos.Sin embargo su cuenta sera bloqueada",
        "garantizar su seguridad.Le recomendamos verificar sus datos",
        "detectamos un problema en su identidad.Para verificarla ingrese sus datos",
    ):
        assert extraer_enlaces(texto) == (), texto


def test_un_dominio_en_mayusculas_sigue_siendo_un_dominio() -> None:
    """`CLAVEUNICA.GOB.CL` es un dominio de verdad escrito a gritos, no una oración."""
    assert [e.registrable for e in extraer_enlaces("INGRESE A CLAVEUNICA.GOB.CL")] == [
        "claveunica.gob.cl"
    ]


def test_una_oracion_pegada_a_un_dominio_no_se_come_el_dominio() -> None:
    assert [e.registrable for e in extraer_enlaces("visite www.sii.cl.Gracias")] == ["sii.cl"]


def test_un_punto_sin_espacio_en_minuscula_no_inventa_un_dominio() -> None:
    """`paquete.por` no es un dominio: `por` no es un TLD.

    La regla de «punto seguido de mayúscula» no lo atrapa, porque acá va en minúscula. Lo que lo
    atrapa es preguntarle a la **lista de la IANA** si la última etiqueta es un TLD de verdad.

    Lo encontró el control invertido de `T4.3`: era la **única falsa acusación** de 210, y el motor
    nombraba `paquete.por` como si fuera el sitio del atacante. Es la segunda vez que este error
    aparece —la primera fue `operativos.Sin`— y por eso ahora la regla es la autoridad, no una
    heurística.
    """
    for texto in (
        "falta un numero de calle en el paquete.por favor actualice",
        "su cuenta esta en regla.sin embargo debe verificar",
        "el proceso sigue en curso.para mayor informacion llame",
    ):
        assert extraer_enlaces(texto) == (), texto


def test_una_etiqueta_final_que_no_es_tld_no_es_un_dominio() -> None:
    """`abc` **sí** es un TLD —la lista tiene 1.437 entradas y hay de todo—, así se usa `por`."""
    assert [e.registrable for e in extraer_enlaces("vea documento.por y real.cl")] == [
        "real.cl"
    ]


def test_los_mensajes_de_prueba_con_example_siguen_siendo_enlaces() -> None:
    """`.example` no está en la lista de la IANA porque **no se delega**, pero es un TLD reservado.

    Y tiene que seguir contando: los mensajes de prueba de `T3.1` lo usan justamente porque no puede
    resolver. Sin esto, el motor dejaría de leer sus propios mensajes de prueba.
    """
    assert [e.registrable for e in extraer_enlaces("ingrese a sitio-falso.example")] == [
        "sitio-falso.example"
    ]


def test_los_tld_reales_de_phishing_si_cuentan() -> None:
    """La lista no puede ser tan estricta que deje pasar el phishing: usa TLD reales."""
    for host in ("sitio.xyz", "sitio.sbs", "sitio.live", "sitio.top", "sitio.cn", "sitio.info"):
        assert [e.registrable for e in extraer_enlaces(f"ingrese a {host}")] == [host], host


def test_enlace_sin_esquema_se_detecta() -> None:
    assert [e.registrable for e in extraer_enlaces("visite www.sii.cl/personas")] == ["sii.cl"]


def test_una_ruta_con_punto_no_es_un_enlace() -> None:
    """`.../SantaIsabelws/tb.php` no es un dominio: es una ruta, y nombrarla sería acusar en falso.

    Lo encontró la medición sobre el corpus —el ejemplo `8fph22-00674-01`— y no un test unitario: el
    motor nombraba `tb.php` como si fuera un sitio del atacante.
    """
    resultado = evaluar("ingrese a http://divisionstagnate.cn/SantaIsabelws/tb.php?ea=1")
    assert [e.registrable for e in resultado.enlaces] == ["divisionstagnate.cn"]


def test_varios_enlaces_con_ruta_se_reducen_a_su_dominio() -> None:
    resultado = evaluar("vea https://uno.cl/a/b.php y http://dos.xyz/c/d.html")
    assert [e.registrable for e in resultado.enlaces] == ["uno.cl", "dos.xyz"]


def test_correo_electronico_no_es_enlace() -> None:
    """Un correo de contacto no es un enlace que se aprieta, y marcarlo sería una falsa alarma."""
    resultado = evaluar("Escribanos a contacto@bancoestado.cl o llame al 600 123 4567")
    assert resultado.enlaces == ()
    assert resultado.veredicto is Veredicto.SIN_ENLACES


def test_homoglifo_cirilico_no_da_coincide() -> None:
    """`claveunica.gоb.cl` con la `o` cirílica se ve igual y no es el dominio de ClaveÚnica.

    Es el ataque que la vista no puede ganar y el programa sí, que es la razón de existir del
    proyecto.
    """
    resultado = evaluar("ClaveUnica le informa: ingrese a claveunica.g\u043eb.cl")
    assert resultado.veredicto is Veredicto.NO_COINCIDE
    assert resultado.enlaces[0].ascii is False


def test_terminar_parecido_a_gob_cl_no_da_coincide() -> None:
    for host in ("claveunica.gob.cl.xyz", "claveunicagob.cl", "gob-cl.xyz", "claveunica.gob.com"):
        assert evaluar(f"ingrese a {host}").veredicto in CON_PROBLEMA, host


def test_punteo_final_no_ensucia_el_enlace() -> None:
    resultado = evaluar("Ingrese a https://claveunica.gob.cl.")
    assert [e.registrable for e in resultado.enlaces] == ["claveunica.gob.cl"]


def test_mayusculas_no_importan() -> None:
    assert evaluar("CLAVEUNICA LE INFORMA, INGRESE A CLAVEUNICA.GOB.CL").veredicto is (
        Veredicto.COINCIDE
    )


def test_enlaces_repetidos_aparecen_una_vez() -> None:
    resultado = evaluar("claveunica.gob.cl y otra vez claveunica.gob.cl")
    assert [e.registrable for e in resultado.enlaces] == ["claveunica.gob.cl"]


def test_se_reporta_la_marca_suplantada() -> None:
    resultado = evaluar("entre a bancoestado--cl.xyz", marcas=MARCAS)
    assert [s.marca for s in resultado.suplantaciones] == ["bancoestado"]
    assert resultado.suplantaciones[0].tipo is TipoSuplantacion.PUNTO_A_GUION


def test_ninguna_respuesta_promete_seguridad() -> None:
    """La línea roja, sobre **todos** los veredictos y no solo sobre el amable.

    Decir «es seguro» es lo único que este programa no puede hacer: un enlace legítimo dentro de un
    mensaje falso existe, y es exactamente el ataque mejor construido.
    """
    textos = (
        "Ingrese a https://claveunica.gob.cl",
        "Ingrese a https://www.gob.cl",
        "Banco Ripley: ingrese a bancoripley.cl",
        "Banco Ripley: ingrese a otro-lado.xyz",
        "Ingrese a https://un-sitio-cualquiera.xyz",
        "Su ClaveUnica sera bloqueada",
    )
    for texto in textos:
        explicacion = evaluar(texto).explicacion.lower()
        assert "seguro" not in explicacion, texto
        assert "confiar" not in explicacion, texto
        assert "confiable" not in explicacion, texto


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


def test_un_parecido_del_dominio_de_una_institucion_no_coincide() -> None:
    for host in ("sernac-cl.xyz", "sernac.gob.cl.xyz", "sernaccl.com"):
        assert evaluar(f"reclame en {host}").veredicto in CON_PROBLEMA, host


def test_un_enlace_conocido_no_lava_a_uno_desconocido() -> None:
    resultado = evaluar("Reclame en sernac.cl y confirme en bit.ly/reclamo")
    assert resultado.veredicto is Veredicto.AJENO


def test_una_institucion_nombrada_en_el_texto_cuenta_como_reclamo() -> None:
    resultado = evaluar("SERVEL: tiene una multa. Pague en bit.ly/multa")
    assert resultado.dice_ser_del_estado
    assert resultado.reclamadas == ("Servel",)
    assert resultado.veredicto is Veredicto.NO_COINCIDE


def test_el_mensaje_mezclado_nombra_las_dos_partes() -> None:
    """El mensaje mezclado es el ataque: un enlace legítimo de adorno y uno falso para apretar.

    La respuesta tiene que nombrar de quién dice ser y cuál es el enlace que no le corresponde.
    """
    resultado = evaluar("Reclame en sernac.cl y confirme en bit.ly/reclamo")
    assert "SERNAC" in resultado.explicacion
    assert "bit.ly" in resultado.explicacion


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


def test_no_se_nombran_dos_veces_la_misma_institucion() -> None:
    """«Banco Ripley» y «Ripley» son la misma cosa para quien lee.

    Sin esto, la frase que más importa quedaba como «El mensaje dice ser de Banco Ripley, Ripley»,
    y **lo encontró el armado de los mensajes de `T3.1`**, no un test unitario.
    """
    resultado = evaluar(
        "Banco Ripley, detecto una actividad inusual en su tarjeta Ripley. "
        "Actualice sus datos en bit.example/3Ub4EKA"
    )
    assert resultado.reclamadas == ("Banco Ripley",)
    assert resultado.veredicto is Veredicto.NO_COINCIDE


def test_un_enlace_reportado_por_el_estado_da_confirmado() -> None:
    """`CONFIRMADO` es el veredicto más fuerte: **no es una inferencia, es un hecho con fuente**.

    Los demás veredictos juzgan el enlace por su forma. Este lo juzga por su historia: el Estado ya
    publicó que ese dominio es fraudulento.
    """
    indice = Indice({"nhmwcotitostado.info": ["8fph22-00664-01"]})
    resultado = evaluar(
        "Banco de Estado le comunica: ingrese a nhmwcotitostado.info/activacion/", indice=indice
    )
    assert resultado.veredicto is Veredicto.CONFIRMADO
    assert resultado.confirmados == ("nhmwcotitostado.info",)


def test_lo_confirmado_manda_sobre_los_demas_veredictos() -> None:
    """Un enlace confirmado es lo más fuerte que se puede decir, aunque el otro enlace coincida."""
    indice = Indice({"malo.xyz": ["X-01"]})
    resultado = evaluar(
        "SERNAC le informa: reclame en sernac.cl y confirme en malo.xyz", indice=indice
    )
    assert resultado.veredicto is Veredicto.CONFIRMADO
    assert resultado.enlaces  # los dos enlaces se siguen viendo


def test_la_respuesta_cita_la_alerta_del_csirt() -> None:
    """El ciudadano tiene que poder ir a leer la fuente. Citar es la mitad del valor."""
    indice = Indice({"malo.xyz": ["8fph22-00664-01"]})
    resultado = evaluar("ingrese a malo.xyz", indice=indice)
    assert "csirt.gob.cl/alertas/8fph22-00664-01/" in resultado.explicacion
    assert "malo.xyz" in resultado.explicacion


def test_sin_indice_no_se_confirma_nada() -> None:
    """Sin índice el motor degrada a lo que era antes. **No arranca mal: arranca sin confirmar.**"""
    resultado = evaluar("ingrese a malo.xyz", indice=Indice({}))
    assert resultado.veredicto is Veredicto.AJENO
    assert resultado.confirmados == ()


def test_un_dominio_real_del_corpus_da_confirmado() -> None:
    """La prueba de aceptación: con el índice que se construye desde el CSIRT, un dominio real del
    corpus tiene que quedar confirmado."""
    resultado = evaluar(
        "Banco de Estado le comunica: ingrese a "
        "https://nhmwcotitostado.info/activacion/cuenta-ulen/"
    )
    assert resultado.veredicto is Veredicto.CONFIRMADO
    assert resultado.confirmados == ("nhmwcotitostado.info",)


def test_un_dominio_confirmado_no_promete_seguridad_por_el_resto() -> None:
    """Citar la alerta no autoriza a decir que el mensaje es seguro: el resto sigue sin validar."""
    indice = Indice({"malo.xyz": ["X-01"]})
    explicacion = evaluar("ingrese a malo.xyz", indice=indice).explicacion.lower()
    assert "seguro" not in explicacion
    assert "confiar" not in explicacion


def test_la_marca_imitada_se_nombra_como_se_escribe() -> None:
    """La respuesta la lee una persona: «ClaveÚnica», no el nombre con el que se compara."""
    assert "ClaveÚnica" in evaluar("entre a claveunica-gob-cl.xyz").explicacion
