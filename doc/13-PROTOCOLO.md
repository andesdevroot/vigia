# 13 — Protocolo de `T3.1`: ¿la gente reenvía el enlace?

## 1. La pregunta

> Cuando una persona común quiere saber si un mensaje sospechoso es real, **¿lo reenvía de una forma
> que el motor pueda leer?**

El motor solo juzga **enlaces**. Si el enlace no llega, el motor se queda mudo.

## 2. Por qué importa tanto

En `T1.7` se midió contra 45 alertas del CSIRT y salió esto: **en 44 de 45 el enlace no está dentro
del texto citado.** Si eso pasara con la gente, el motor no serviría en el 98 % de los casos, y el
paper no tendría con qué sostenerse.

**Es el riesgo número uno del proyecto, y es el único que no está medido.**

## 3. Una aclaración que cambia el diseño

**Ese 98 % es del formato del CSIRT, no de la gente.** La alerta publica el texto por un lado y la
URL por otro; **en el SMS original el enlace estaba**. Así que el 98 % no es una predicción sobre el
comportamiento de nadie: es un artefacto de la fuente.

Eso convierte a `T3.1` en el experimento que decide entre dos lecturas opuestas:

| Si la gente… | Entonces |
|---|---|
| reenvía el mensaje completo | el motor funciona, y el 98 % era de la fuente |
| manda captura, audio o texto pelado | **el cuello de botella es la modalidad, no el clasificador** |

**Las dos son publicables.** La segunda es, de hecho, más interesante.

## 4. Las tres formas en que puede llegar, y qué implica cada una

| Modalidad | Qué es | Qué habría que construir |
|---|---|---|
| **con enlace** | reenvió el mensaje, o pegó el texto con la URL | nada: es lo que ya hay |
| **con adjunto** | mandó **captura de pantalla** o **audio** | lectura de imágenes (visión) o transcripción |
| **texto sin enlace** | copió y pegó, y la URL se perdió | pedirle el mensaje completo, o nada |

## 5. Diseño: dos brazos, uno controlado y uno observacional

### Brazo A — controlado (el que da el número)

**Veinte personas** no técnicas, con WhatsApp en el teléfono, de edades mezcladas. No ingenieros: el
proyecto existe para **gente común**, y esa es la población.

**Procedimiento, por persona:**

1. Se le explica, y **acepta**, que se está midiendo cómo reenvía mensajes —sin decirle cómo hacerlo—.
2. El investigador le manda **3 mensajes sospechosos reales**, publicados por el CSIRT, como si se los
   hubiera reenviado un tercero.
3. La instrucción es **una sola frase**: *«mándale estos mensajes al robot y mira qué te dice»*.
   **No se menciona la palabra enlace, ni se sugiere reenviar, ni copiar.**
4. Se registra **cómo llegó cada uno**, sin mirar el contenido.

**Lo que NO se dice es el punto del experimento.** Si se les explica que el enlace importa, se mide
lo que hacen cuando se les pide, no lo que hacen solos.

### Brazo B — observacional

Durante dos semanas, quien quiera puede **reenviar estafas que le hayan llegado de verdad**. Eso
mide el caso real, sin laboratorio, y sirve para confirmar o desmentir el brazo A.

Es el que más se parece al uso real, y por eso no se puede controlar: solo se cuenta.

## 6. Los mensajes de prueba

**Reales en su texto, inofensivos en su enlace.** Se toma el texto publicado por el CSIRT y **se
reemplaza el host por uno reservado** que nunca resuelve:

```
Original:   ... Regularice en http://divisionstagnate.cn/SantaIsabelws/tb.php?ea=1
Prueba:     ... Regularice en http://sitio-falso.example/SantaIsabelws/tb.php?ea=1
```

`.example` es de uso reservado (RFC 2606): **no existe y no puede existir**. Tres razones:

1. **Nadie puede pinchar y llegar a algo.** Aunque alguien lo haga, no pasa nada.
2. **La forma del enlace se conserva** —el motor lo ve, lo extrae y lo juzga igual—, así que la
   medición sigue siendo válida.
3. El veredicto del robot no cambia: sigue siendo `NO_COINCIDE` si el mensaje dice ser de un banco.

**No se inventan mensajes.** Los tres salen del corpus de `doc/12-MEDICION.md`, y cada uno tiene su
fuente citable.

## 7. Qué se registra

Por cada intento, **solo esto**:

| Campo | Valores |
|---|---|
| Modalidad | `con_enlace` · `con_adjunto` · `texto_sin_enlace` |
| Momento | día y hora, sin identificar a nadie |
| Código del mensaje | `A`, `B` o `C` |

**Nunca el texto, nunca el número, nunca el nombre.** No es una promesa de la política de privacidad:
el instrumento de medición **no tiene dónde guardarlos** (§8).

Y dos preguntas al final, en voz alta, que se anotan aparte: *«¿te sirvió?»* y *«¿lo usarías otra
vez?»*.

## 8. El instrumento: un contador que no puede filtrar

El servidor gana un contador **apagado por defecto**, que se enciende con `VIGIA_CONTAR=1` y escribe
**agregados**:

```json
{"2026-10-10": {"con_enlace": 41, "con_adjunto": 12, "texto_sin_enlace": 7}}
```

No hay ningún camino por el que el texto de un mensaje llegue a ese archivo: el contador recibe un
`MensajeRecibido` y devuelve una de tres etiquetas. **Un instrumento de medición que no puede
guardar lo que mide** es más fuerte que una promesa, y para el paper es un argumento, no una nota al
pie.

## 9. Ética, explícita

- **Los mensajes no son reales como ataque.** El enlace no resuelve. Nadie queda expuesto.
- **Son públicos**: los publicó el CSIRT con TLP:CLEAR para advertir a la gente.
- **Hay consentimiento informado** antes de empezar, y se puede parar en cualquier momento.
- **No se guarda nada de nadie**: ni el número, ni el texto.
- **No se pide que nadie pinche un enlace**, ni siquiera el inofensivo.
- **Los resultados se publican agregados**, nunca por persona.

## 10. Cómo se lee el resultado

Con 20 personas × 3 mensajes = **60 intentos**, el número sale con su intervalo.

| Escenario | Qué significa | Qué sigue |
|---|---|---|
| **≥ 80 % con enlace** | el canal funciona; el 98 % era de la fuente | el paper se sostiene como está, y se escribe la sección de despliegue |
| **50–80 %** | funciona a medias, y la modalidad importa | visión (imágenes) pasa a ser la prioridad, y **es una contribución del paper** |
| **< 50 %** | el enlace casi nunca llega | **el motor no es el producto**: hay que leer capturas, y el paper cambia de tesis |

El tercer escenario **no es un fracaso**. Es el hallazgo de que el cuello de botella del fraude
ciudadano está en la **modalidad** y no en la clasificación — y eso nadie lo ha medido.

## 11. Limitaciones, declaradas por adelantado

1. **20 personas no son una muestra representativa de Chile.** Es un piloto, y se presenta como tal.
2. **La gente sabe que la observan.** El brazo B mitiga eso, no lo elimina.
3. **Los mensajes son de 2022–2023.** Las estafas de hoy pueden tener otra forma.
4. **El enlace está saneado.** Si alguien decide no reenviar por desconfianza del dominio raro, eso
   aparecería como «texto sin enlace» sin serlo. Se controla mirando si el texto llegó completo.
5. **Mide intención, no uso sostenido.** Que lo hagan una vez no dice que lo hagan siempre.

## 12. Antes de arrancar

- [ ] El contador implementado y probado (`VIGIA_CONTAR=1`)
- [ ] Los 3 mensajes de prueba armados desde el corpus, con el host saneado
- [ ] El robot levantado con el túnel y el webhook activo
- [ ] 20 personas reclutadas, mezcladas en edad y sin perfil técnico
- [ ] La planilla de registro, con las tres modalidades y nada más
- [ ] El texto de consentimiento, leído antes de empezar
