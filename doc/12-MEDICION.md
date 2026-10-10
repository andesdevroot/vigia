# 12 — La medición: 45 estafas reales

## De dónde salieron, y por qué de ahí

Del **CSIRT**, que es el Estado etiquetando la estafa. Dos fuentes que se complementan:

| Fuente | Qué aporta |
|---|---|
| [`github.com/csirtcl/Fraude`](https://github.com/csirtcl/Fraude) | 785 informes con la URL maliciosa y el dominio, en texto limpio |
| `csirt.gob.cl/alertas/{codigo}/` | el texto del mensaje, **citado literalmente** entre comillas tipográficas |

De los 785 informes, **499 son de «Falsificación de Registros o Identidad» y no citan ningún
mensaje**. Ir por ellos primero devolvió **cero ejemplos después de cuarenta consultas** — el primer
intento, y el que enseñó a leer la composición del repositorio antes de recorrerlo.

Los que sirven son los **259 de phishing y smishing**. De ahí salieron **45**, con su código, su URL
maliciosa y su fuente citable. Están en `corpus/alertas_csirt.json`.

## El resultado

```
                        la cita del CSIRT   la cita + el enlace del informe
  avisa                        1  (2%)             45  (100%)
  mudo                        44  (98%)             0    (0%)
  GRAVE                        0   (0%)             0    (0%)
  nombran la marca imitada     0                   0
```

## Lo que estos números NO dicen

**La columna de la derecha es tautológica y no es un resultado.** Ahí se le agregó al mensaje la URL
que el propio informe declara maliciosa, así que el motor dice «no es del Estado» porque se le dio
un enlace que no lo es. Confirma que la regla funciona; **no mide ningún acierto.**

**No hay falsas acusaciones medidas.** Para eso haría falta un corpus de mensajes legítimos, y no
existe. El `0` de la columna `GRAVE` es real y es lo único tranquilizador: **el motor nunca dio por
bueno el enlace de una estafa**, en 45 casos.

Lo que sí dice la columna de la izquierda es sobre el **insumo**, no sobre el motor:

> **El CSIRT cita un fragmento, no el mensaje completo.** En 44 de 45 casos el enlace no está dentro
> de la cita.

O sea: si un ciudadano reenviara exactamente lo que el Estado publicó, **no le serviríamos en el 98 %
de los casos.** En el SMS real el enlace estaba; el informe lo reporta aparte.

## Hallazgo 1 — A quién suplantan de verdad

Contadas sobre las 45 citas:

| Veces | Institución |
|---|---|
| **21** | **Banco Ripley** |
| **16** | **BancoEstado** (escrito «banco de estado») |
| 1 | Copec |
| 1 | Santander |
| 1 | Soprole |

**Casi la mitad son un banco privado.** Y el motor **nombra la marca imitada en 0 de 45 casos**,
porque el catálogo de `T1.3` solo tiene instituciones del Estado que usan `.gob.cl`.

## Hallazgo 2 — La pregunta del producto está mal planteada

El motor contesta **«¿el enlace es del Estado?»**. Pero el 47 % de lo que se suplanta es **Banco
Ripley**, que no es del Estado. A esa persona la respuesta «el enlace NO es del Estado» no le sirve:
le dice algo cierto y le deja la duda intacta.

La pregunta que el corpus pide es otra:

> **«¿Este enlace es el sitio de la institución que el mensaje dice ser?»**

Es un cambio de fondo, no de redacción: obliga a tener catálogo de **lo suplantado**, no solo de lo
estatal, y a que el veredicto hable de la institución nombrada.

## Lo que se puede verificar del hallazgo 1

Los dominios de los suplantados, leídos de su certificado:

| Dominio | Certificado |
|---|---|
| `bancoripley.cl` | `O=BANCO RIPLEY` |
| `bci.cl` | `O=Banco de Credito e Inversiones` |
| `itau.cl` | `O=BANCO ITAU CHILE` |
| `bancochile.cl` | `businessCategory=Private Organization` |
| `bancofalabella.cl`, `ripley.cl`, `soprole.cl`, `copec.cl` | `CN` del dominio |
| **`bancoestado.cl`, `santander.cl`, `scotiabank.cl`** | **sin certificado desde esta máquina** |

Los tres últimos quedan **fuera** por el mismo blocker de DNS que ya declaró `T1.3`. No se adivinan.

## T1.9 — Cambiar la pregunta, y lo que costó

La pregunta pasó de «¿el enlace es del Estado?» a **«¿este enlace es el sitio de la institución que el
mensaje dice ser?»**. Veredictos nuevos: `COINCIDE` y `NO_COINCIDE`.

**Una trampa que apareció al implementarlo:** la URL contaba como «dice ser». Un mensaje
`Banco Ripley le informa: ingrese a claveunica.gob.cl` reclamaba ClaveÚnica por el solo hecho de
enlazarla, así que la lista de reclamadas incluía a las dos y el veredicto daba `COINCIDE` —
escondiendo justo la incoherencia que el motor existe para encontrar. **Enlazar a alguien no es decir
ser él.** Ahora el reclamo se busca en el texto **con los enlaces borrados**.

### La medición con la pregunta nueva no cambió ni un número

```
                         la cita del CSIRT   cita + enlace del informe
  nombra                       0   (0%)             0    (0%)
  avisa                        1   (2%)            45  (100%)
  mudo                        44  (98%)             0    (0%)
  GRAVE                        0   (0%)             0    (0%)
  reconoció de quién dice ser  0                   0
```

**Cero reconocimientos.** No es un fallo de `T1.9`: es que **el catálogo no tiene a los
suplantados**. `nombra` solo se alcanza reconociendo la institución, y el catálogo de `T1.3` son
instituciones estatales bajo `.gob.cl` — mientras que el corpus suplanta bancos.

> **Cambiar la pregunta era necesario, y no es suficiente.** Sin `T1.8` el motor no puede decir «el
> mensaje dice ser de Banco Ripley», porque no sabe quién es Banco Ripley.

Es el orden correcto igual: si el catálogo hubiera crecido primero, el motor habría dicho «el enlace
es de una institución oficial: bancoripley.cl (Banco Ripley)», que no es lo que hay que leer.

## Cómo se reproduce, y con qué se mide

```bash
python3 scripts/cosechar_alertas.py 45   # cosecha; ~2 minutos, con pausa entre consultas
python3 scripts/medir_motor.py           # mide e imprime el cuadro y los fallos
```

Solo se **lee** lo publicado con TLP:CLEAR. No se visita ningún sitio malicioso: la URL se guarda
como texto.
