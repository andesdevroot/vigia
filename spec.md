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

## 10. El índice de indicadores del Estado

| # | Requisito | Test |
|---|---|---|
| REQ-120 | Un enlace que el Estado reportó da `CONFIRMADO` | `test_un_enlace_reportado_por_el_estado_da_confirmado` |
| REQ-121 | Lo confirmado manda sobre los demás veredictos | `test_lo_confirmado_manda_sobre_los_demas_veredictos` |
| REQ-122 | **La respuesta cita la alerta del CSIRT** | `test_la_respuesta_cita_la_alerta_del_csirt` |
| REQ-123 | Sin índice no se confirma nada | `test_sin_indice_no_se_confirma_nada` |
| REQ-124 | Un archivo de índice roto da un índice **vacío**, no una excepción | `test_un_archivo_corrupto_da_un_indice_vacio` |
| REQ-125 | La consulta usa el dominio **registrable** | `test_la_consulta_usa_el_dominio_registrable` |
| REQ-126 | El índice del paquete trae datos | `test_el_indice_del_paquete_tiene_dominios` |
| REQ-127 | Un dominio real del corpus queda confirmado | `test_un_dominio_real_del_corpus_da_confirmado` |
| REQ-128 | Citar la alerta no autoriza a prometer seguridad | `test_un_dominio_confirmado_no_promete_seguridad_por_el_resto` |
| REQ-129 | **Una plataforma compartida nunca se confirma**, aunque el índice la traiga | `test_una_plataforma_compartida_nunca_se_confirma` |
| REQ-130 | **Un sufijo público nunca se confirma**: `com.br` no es un dominio | `test_un_sufijo_publico_nunca_se_confirma` |
| REQ-131 | Un dominio normal **sí** se confirma: el filtro no se pasa de listo | `test_un_dominio_normal_si_se_confirma` |
| REQ-132 | Un índice sin la clave `dominios` da un índice vacío | `test_un_archivo_sin_la_clave_dominios_da_un_indice_vacio` |
| REQ-133 | Un índice inexistente da un índice vacío | `test_un_archivo_inexistente_da_un_indice_vacio` |

## 11. Los invariantes sobre el corpus real

| # | Requisito | Test |
|---|---|---|
| REQ-140 | **Ninguna estafa del corpus recibe un veredicto favorable** sobre el mensaje completo | `test_ninguna_estafa_del_corpus_recibe_un_veredicto_favorable` |
| REQ-141 | Los fallos conocidos sobre la cita recortada están **declarados uno por uno** | `test_los_graves_sobre_la_cita_estan_declarados` |
| REQ-142 | La respuesta útil no baja del suelo: es un **trinquete** | `test_la_respuesta_util_no_baja_del_suelo` |
| REQ-143 | El corpus está completo: 300 o más, con todos sus campos | `test_el_corpus_esta_completo` |
| REQ-144 | El corpus tiene **una sola clase**, y por eso no se entrena | `test_el_corpus_solo_tiene_una_clase_y_por_eso_no_se_entrena` |

## 12. El control invertido

| # | Requisito | Test |
|---|---|---|
| REQ-150 | **Ningún mensaje de control es acusado**: dice ser de X y enlaza a X | `test_ningun_mensaje_de_control_es_acusado` |
| REQ-151 | El control **solo cambia el enlace**: el texto queda idéntico | `test_el_control_solo_cambia_el_enlace` |
| REQ-152 | Los enlaces de control son los **oficiales del catálogo** | `test_los_enlaces_de_control_son_los_oficiales_del_catalogo` |
| REQ-153 | La coincidencia no baja del suelo: es un **trinquete** | `test_la_coincidencia_no_baja_del_suelo` |
| REQ-154 | Los acusados declarados siguen ocurriendo, o se sacan de la lista | `test_los_acusados_declarados_siguen_ocurriendo` |
| REQ-155 | El control tiene suficientes casos | `test_el_control_tiene_suficientes_casos` |

## 13. Los TLD de verdad

| # | Requisito | Test |
|---|---|---|
| REQ-160 | Un punto sin espacio **en minúscula** no inventa un dominio | `test_un_punto_sin_espacio_en_minuscula_no_inventa_un_dominio` |
| REQ-161 | Una etiqueta final que no es un TLD no es un dominio | `test_una_etiqueta_final_que_no_es_tld_no_es_un_dominio` |
| REQ-162 | Los TLD reales del phishing **sí** cuentan | `test_los_tld_reales_de_phishing_si_cuentan` |
| REQ-163 | `.example` sigue siendo un enlace: es reservado, y los mensajes de prueba lo usan | `test_los_mensajes_de_prueba_con_example_siguen_siendo_enlaces` |

## 14. La petición del mensaje

| # | Requisito | Test |
|---|---|---|
| REQ-170 | Pedir la clave a nombre de una institución es indebido | `test_pedir_la_clave_a_nombre_de_una_institucion_es_indebido` |
| REQ-171 | Pedir una transferencia es indebido | `test_pedir_una_transferencia_es_indebido` |
| REQ-172 | **Pinchar un enlace o llamar no es indebido**: son avisos normales | `test_pinchar_un_enlace_no_es_indebido` |
| REQ-173 | **Sin reclamo no hay petición indebida**: hacen falta las dos condiciones | `test_sin_reclamo_no_hay_peticion_indebida` |
| REQ-174 | Un mensaje sin enlace que pide la clave **ya no es mudo** | `test_un_mensaje_sin_enlace_que_pide_la_clave_ya_no_es_mudo` |
| REQ-175 | Lo confirmado por el Estado manda sobre la petición | `test_lo_confirmado_sigue_mandando_sobre_la_peticion` |
| REQ-176 | Sin extractor inyectado el veredicto no cambia | `test_sin_peticion_inyectada_el_veredicto_no_cambia` |
| REQ-177 | El extractor de referencia es determinista | `test_el_extractor_de_referencia_es_determinista` |
| REQ-178 | **El extractor de referencia confunde la negación**, y está declarado | `test_el_extractor_de_referencia_confunde_la_negacion_y_se_declara` |
| REQ-179 | **Las falsas alarmas del baseline están declaradas** una por una | `test_las_falsas_alarmas_del_extractor_de_referencia_estan_declaradas` |
| REQ-180 | La respuesta por petición no promete seguridad | `test_la_respuesta_por_peticion_no_promete_seguridad` |

## 15. La redacción y el extractor con modelo

| # | Requisito | Test |
|---|---|---|
| REQ-190 | La redacción tapa el correo, el enlace y el RUT | `test_la_redaccion_tapa_el_correo_el_enlace_y_el_rut` |
| REQ-191 | Tapa teléfonos y números de cuenta | `test_la_redaccion_tapa_telefonos_y_numeros_de_cuenta` |
| REQ-192 | **Conserva lo que la extracción necesita** | `test_la_redaccion_conserva_lo_que_la_extraccion_necesita` |
| REQ-193 | **Ningún mensaje del corpus sale con números largos ni correos** | `test_ningun_mensaje_del_corpus_sale_con_numeros_largos` |
| REQ-194 | El extractor manda el texto **redactado** | `test_el_extractor_manda_el_texto_redactado` |
| REQ-195 | El modelo **no puede inventar una categoría** | `test_el_modelo_no_puede_inventar_una_categoria` |
| REQ-196 | El prompt enumera el vocabulario y avisa de la negación | `test_el_extractor_pide_json_y_enumera_el_vocabulario` |
| REQ-197 | Un fallo del proveedor **no acusa a nadie** | `test_un_fallo_del_proveedor_no_acusa_a_nadie` |
| REQ-198 | **La caché no guarda el texto**: hashes y etiquetas | `test_la_cache_no_guarda_el_texto` |
| REQ-199 | La caché evita mandar dos veces el mismo mensaje | `test_la_cache_evita_mandar_dos_veces_el_mismo_mensaje` |
| REQ-200 | Una respuesta ilegible no revienta | `test_una_respuesta_ilegible_no_revienta` |

## 16. El extractor conectado al robot

| # | Requisito | Test |
|---|---|---|
| REQ-210 | Un mensaje sin enlace que pide la clave **ya no queda mudo** en el robot | `test_un_mensaje_sin_enlace_que_pide_la_clave_ya_no_queda_mudo` |
| REQ-211 | **Sin extractor el motor se comporta como antes** | `test_sin_extractor_el_motor_se_comporta_como_antes` |
| REQ-212 | El proveedor caído se declara y no parece perfecto | `test_un_proveedor_caido_no_parece_un_modelo_perfecto` |
| REQ-213 | **La petición nunca tapa lo que dice el enlace** | `test_la_peticion_nunca_tapa_lo_que_dice_el_enlace` |
| REQ-214 | La petición solo decide cuando **no hay enlace** que juzgar | `test_la_peticion_sigue_decidiendo_cuando_no_hay_enlace` |
| REQ-215 | **Lo que pide se dice en castellano**, no en el vocabulario del modelo | `test_lo_que_pide_se_dice_en_castellano` |
| REQ-216 | Con una sola cosa no se pone la conjunción | `test_con_una_sola_cosa_no_se_pone_la_conjuncion` |
| REQ-217 | Con tres, la conjunción va antes de la última | `test_con_tres_cosas_la_conjuncion_va_antes_de_la_ultima` |
| REQ-218 | Sin petición indebida no se agrega nada | `test_sin_peticion_indebida_no_dice_nada` |

## 18. El límite, los avisos y el registro

| # | Requisito | Test |
|---|---|---|
| REQ-220 | La primera vez que alguien escribe se le **avisa de la privacidad** | `test_la_primera_vez_avisa_de_la_privacidad` |
| REQ-221 | Ese aviso **no se repite** en los mensajes siguientes | `test_la_privacidad_se_avisa_una_sola_vez` |
| REQ-222 | El aviso es **por persona**: si no, el segundo nunca se entera | `test_a_cada_persona_se_le_avisa_por_separado` |
| REQ-223 | Bajo el límite se contesta siempre | `test_bajo_el_limite_se_contesta_siempre` |
| REQ-224 | Al cruzar el límite **se avisa una vez**, y después no se contesta | `test_al_cruzar_el_limite_se_avisa_una_vez_y_despues_no_se_contesta` |
| REQ-225 | El límite es **por persona**, no global | `test_el_limite_es_por_persona_y_no_global` |
| REQ-226 | La ventana se renueva: nadie queda bloqueado para siempre | `test_la_ventana_se_renueva` |
| REQ-227 | **La memoria no guarda el mensaje**: solo números y banderas | `test_la_memoria_no_guarda_el_mensaje` |
| REQ-228 | La memoria **no crece sin límite** | `test_no_crece_sin_limite` |
| REQ-229 | **El límite corta los mensajes y ahorra dinero** | `test_el_limite_corta_los_mensajes_y_ahorra_dinero` |
| REQ-230 | El aviso de privacidad viaja en la primera respuesta | `test_el_aviso_de_privacidad_viaja_en_la_primera_respuesta` |
| REQ-231 | Sin memoria el robot se comporta como antes | `test_sin_memoria_nada_cambia` |
| REQ-232 | **El servidor anota por qué no respondió** | `test_el_servidor_anota_por_que_no_respondio` |

## 17. La arquitectura

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
