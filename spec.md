# spec.md — la especificación

**v1.0 · 2026-10-10**

**Qué tiene que hacer el sistema**, en requisitos numerados y verificables. El *cómo* está en
`doc/design.md`; la cola, en `task.md`; el método, en `doc/00-METODOLOGIA.md`.

Cada requisito nombra **el test que lo verifica**, y `tests/test_spec.py` **falla si ese test no
existe**. Eso es lo que convierte este archivo en un contrato y no en un documento: no se puede
agregar un requisito sin cubrirlo, ni renombrar un test sin que la especificación se entere.

Un requisito que no se puede verificar **no es un requisito**: es un deseo. Si aparece uno así, va a
`task.md` como tarea, no acá.

---

## 1. El canal y la seguridad del webhook

| # | Requisito | Test |
|---|---|---|
| REQ-01 | Recibe por webhook los mensajes que un ciudadano reenvía a un número de WhatsApp | `test_un_mensaje_con_enlace_ajeno_se_responde` |
| REQ-02 | Rechaza toda petición que no traiga firma | `test_sin_firma_no_responde` |
| REQ-03 | Rechaza toda petición cuya firma no corresponda | `test_una_firma_mala_no_responde` |
| REQ-04 | Verifica la firma sobre los **bytes crudos**, antes de parsear | `test_la_firma_es_sobre_los_bytes_crudos_y_no_sobre_el_json` |
| REQ-05 | Comprueba el largo de la firma antes de compararla | `test_una_firma_de_largo_equivocado_no_pasa` |
| REQ-06 | Acepta la firma escrita en mayúsculas | `test_una_firma_en_mayusculas_pasa` |
| REQ-07 | **Nunca procesa un mensaje saliente propio** | `test_un_mensaje_saliente_no_se_procesa` |
| REQ-08 | Ignora los eventos que no son mensajes entrantes | `test_un_evento_que_no_es_un_mensaje_no_se_procesa` |
| REQ-09 | **Contesta 200 aunque falle**, para no provocar reintentos | `test_el_servidor_contesta_200_aunque_la_firma_sea_mala` |
| REQ-10 | Un cuerpo ilegible no revienta | `test_un_cuerpo_ilegible_no_revienta` |
| REQ-11 | Sin destinatario no se responde | `test_sin_destinatario_no_se_responde` |
| REQ-12 | **El envío no sigue redirecciones**, para que la clave no viaje a otro host | `test_el_envio_no_sigue_redirecciones` |

## 2. La lectura del mensaje

| # | Requisito | Test |
|---|---|---|
| REQ-20 | Lee el texto del formato de Kapso y del de Meta | `test_el_texto_tambien_se_lee_del_formato_de_meta` |
| REQ-21 | Reconoce una captura de pantalla | `test_una_captura_de_pantalla_se_reconoce` |
| REQ-22 | Una reacción no genera respuesta | `test_una_reaccion_no_genera_nada` |
| REQ-23 | Un cuerpo que no es un diccionario no revienta | `test_un_cuerpo_que_no_es_un_diccionario_no_revienta` |
| REQ-24 | El destinatario cae al identificador por negocio | `test_el_destinatario_cae_al_identificador_por_negocio` |
| REQ-25 | Sin destinatario, el mensaje se lee igual | `test_sin_destinatario_se_lee_igual_pero_no_se_podra_responder` |

## 3. La extracción de enlaces

| # | Requisito | Test |
|---|---|---|
| REQ-30 | Extrae enlaces con y sin esquema | `test_enlace_sin_esquema_se_detecta` |
| REQ-31 | Un correo electrónico **no** es un enlace | `test_correo_electronico_no_es_enlace` |
| REQ-32 | Una ruta con punto no es un dominio | `test_una_ruta_con_punto_no_es_un_enlace` |
| REQ-33 | **Un punto sin espacio no inventa un dominio** | `test_un_punto_sin_espacio_no_inventa_un_dominio` |
| REQ-34 | Un dominio en mayúsculas sí es un dominio | `test_un_dominio_en_mayusculas_sigue_siendo_un_dominio` |
| REQ-35 | Una oración pegada a un dominio no se come el dominio | `test_una_oracion_pegada_a_un_dominio_no_se_come_el_dominio` |
| REQ-36 | Los enlaces repetidos aparecen una vez | `test_enlaces_repetidos_aparecen_una_vez` |
| REQ-37 | El punto final no ensucia el enlace | `test_punteo_final_no_ensucia_el_enlace` |
| REQ-38 | Varios enlaces con ruta se reducen a su dominio | `test_varios_enlaces_con_ruta_se_reducen_a_su_dominio` |

## 4. El veredicto

| # | Requisito | Test |
|---|---|---|
| REQ-40 | Sin enlaces, el veredicto es `SIN_ENLACES` | `test_sin_enlaces_da_sin_enlaces` |
| REQ-41 | `COINCIDE` cuando el enlace es de quien el mensaje dice ser | `test_dice_ser_de_un_banco_y_enlaza_al_banco_da_coincide` |
| REQ-42 | `NO_COINCIDE` cuando no lo es | `test_dice_ser_de_un_banco_y_enlaza_a_otro_lado_da_no_coincide` |
| REQ-43 | **Un enlace ajeno rompe la coincidencia** aunque haya otro legítimo | `test_un_enlace_ajeno_rompe_la_coincidencia` |
| REQ-44 | **Enlazar a alguien no es decir ser él** | `test_un_enlace_del_estado_ajeno_al_reclamo_da_no_coincide` |
| REQ-45 | Sin reclamo reconocido, cae al veredicto del enlace | `test_sin_reclamo_reconocido_cae_al_veredicto_del_enlace` |
| REQ-46 | El dominio propio de una institución no se acusa | `test_el_dominio_propio_de_una_institucion_no_se_acusa` |
| REQ-47 | Un parecido del dominio de una institución no coincide | `test_un_parecido_del_dominio_de_una_institucion_no_coincide` |
| REQ-48 | No se nombra dos veces la misma institución | `test_no_se_nombran_dos_veces_la_misma_institucion` |
| REQ-49 | Un homoglifo cirílico no da coincide | `test_homoglifo_cirilico_no_da_coincide` |
| REQ-50 | Una institución nombrada en el texto cuenta como reclamo | `test_una_institucion_nombrada_en_el_texto_cuenta_como_reclamo` |
| REQ-51 | El nombre tiene que aparecer como palabra completa | `test_el_nombre_tiene_que_aparecer_como_palabra_completa` |
| REQ-52 | Un alias de la institución también cuenta como reclamo | `test_el_alias_con_espacio_tambien_cuenta_como_reclamo` |

## 5. La respuesta

| # | Requisito | Test |
|---|---|---|
| REQ-60 | **Nunca afirma que un mensaje es seguro** | `test_ninguna_respuesta_promete_seguridad` |
| REQ-61 | Un enlace del Estado no promete seguridad | `test_un_enlace_del_estado_lo_dice_sin_prometer_seguridad` |
| REQ-62 | Sin enlaces, pide el mensaje completo | `test_sin_enlaces_invita_a_pegar_el_mensaje` |
| REQ-63 | Una captura sin texto pide el texto | `test_una_imagen_sola_pide_el_texto` |
| REQ-64 | Una captura con texto se evalúa por el texto | `test_una_imagen_con_texto_se_evalua_por_el_texto` |
| REQ-65 | El mensaje mezclado nombra las dos partes | `test_el_mensaje_mezclado_nombra_las_dos_partes` |
| REQ-66 | La marca imitada se nombra como se escribe | `test_la_marca_imitada_se_nombra_como_se_escribe` |

## 6. Privacidad y medición

| # | Requisito | Test |
|---|---|---|
| REQ-70 | **El contador no puede guardar el contenido**: no hay dónde ponerlo | `test_el_contador_no_puede_guardar_el_contenido` |
| REQ-71 | El contador está apagado por defecto | `test_el_servidor_no_cuenta_nada_si_no_se_le_pide` |
| REQ-72 | El contador cuenta cuando se le pide | `test_el_servidor_cuenta_la_modalidad_cuando_se_le_pide` |
| REQ-73 | El contador acumula por día | `test_el_contador_acumula_por_dia` |
| REQ-74 | El contador no revienta con un archivo corrupto | `test_el_contador_no_revienta_con_un_archivo_corrupto` |
| REQ-75 | Un texto con enlace cuenta como enlace | `test_un_texto_con_enlace_cuenta_como_enlace` |
| REQ-76 | Un texto sin enlace cuenta como texto sin enlace | `test_un_texto_sin_enlace_cuenta_como_texto_sin_enlace` |
| REQ-77 | Una captura sin texto cuenta como adjunto | `test_una_captura_sin_texto_cuenta_como_adjunto` |
| REQ-78 | Una captura **con** enlace en el texto cuenta como enlace | `test_una_captura_con_enlace_en_el_texto_cuenta_como_enlace` |

## 7. El catálogo

| # | Requisito | Test |
|---|---|---|
| REQ-80 | Toda institución tiene al menos un dominio | `test_toda_marca_tiene_al_menos_un_dominio` |
| REQ-81 | Los dominios ya son etiquetas registrables | `test_los_dominios_ya_son_etiquetas_registrables` |
| REQ-82 | Ningún dominio pertenece a dos instituciones | `test_ningun_dominio_pertenece_a_dos_marcas` |
| REQ-83 | Ningún nombre de institución se repite | `test_ningun_nombre_de_marca_se_repite` |
| REQ-84 | Los nombres están plegados y sin separadores | `test_los_nombres_estan_en_minusculas_y_sin_separadores` |
| REQ-85 | Los alias están plegados | `test_los_alias_estan_plegados_y_pueden_teñir_espacios` |
| REQ-86 | Toda institución se puede mostrar en la respuesta | `test_toda_marca_se_puede_mostrar_en_la_respuesta` |
| REQ-87 | **El catálogo se vuelve a medir**: los dominios siguen vivos | `test_los_dominios_del_catalogo_siguen_vivos` |

## 8. El detector de marcas parecidas

| # | Requisito | Test |
|---|---|---|
| REQ-90 | La normalización iguala homoglifos | `test_la_normalizacion_iguala_homoglifos` |
| REQ-91 | La normalización **no** inventa igualdades | `test_la_normalizacion_no_inventa_igualdades` |
| REQ-92 | La normalización saca separadores | `test_la_normalizacion_saca_separadores` |
| REQ-93 | El mismo nombre con otro TLD se detecta | `test_el_mismo_nombre_con_otro_tld` |
| REQ-94 | El punto cambiado por guion se detecta | `test_el_punto_cambiado_por_guion` |
| REQ-95 | La marca embebida se detecta, con cota | `test_la_regla_de_subcadena_tiene_cota` |
| REQ-96 | Un dominio ajeno no se marca | `test_un_dominio_ajeno_no_se_marca` |
| REQ-97 | Un dominio oficial no es suplantación | `test_el_dominio_oficial_no_es_suplantacion` |
| REQ-98 | **Una coincidencia no afirma que sea malicioso** | `test_una_coincidencia_no_afirma_que_sea_malicioso` |
| REQ-99 | La unidad registrable de `.gob.cl` es de tres etiquetas | `test_la_unidad_registrable` |

## 9. Los mensajes de prueba de `T3.1`

| # | Requisito | Test |
|---|---|---|
| REQ-100 | **Ninguno puede resolver**: solo se cambió el TLD por `.example` | `test_ningun_mensaje_de_prueba_puede_resolver` |
| REQ-101 | Los tres dan el mejor veredicto posible | `test_los_tres_dan_el_mejor_veredicto` |

## 10. La arquitectura

| # | Requisito | Test |
|---|---|---|
| REQ-110 | Importar el paquete **no arrastra la librería de red** | `test_importar_vigia_no_arrastra_httpx` |
| REQ-111 | El paquete no depende de nada externo, y agregar una es una decisión | `test_el_paquete_no_depende_de_nada_externo_todavia` |

---

## Lo que **no** está especificado, y se declara

Un requisito que no se puede verificar todavía no se escribe acá. Lo que está pendiente vive en
`task.md`, y son estos:

| Pendiente | Por qué no es un requisito todavía |
|---|---|
| Índice de los indicadores del Estado (`T4.2`) | No está construido |
| Extracción de **la petición** del mensaje (`T4.4`) | No está construido, y es el núcleo nuevo |
| Lectura de capturas (`T4.5`) | No está construido |
| Calibración contra mensajes legítimos (`T4.3`) | Falta el corpus |
