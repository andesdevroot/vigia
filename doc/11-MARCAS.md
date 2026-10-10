# 11 — El catálogo de instituciones

## Por qué esto es lo más peligroso del proyecto

Todo lo demás que hace el motor es **conservador**: ante la duda, no concluye. Un dominio en este
catálogo hace lo contrario — convierte un enlace ajeno en un enlace oficial.

Un error acá **no produce una falsa alarma: produce un falso negativo.** El motor daría por bueno el
enlace del atacante. Por eso cada entrada se verificó **abriendo el sitio y leyendo su certificado**,
y acá está la evidencia. Ningún dominio se escribió de memoria.

## La medición

Fecha: **2026-10-10**. Herramientas: `curl -L` con agente de navegador, y `openssl s_client` para el
certificado.

| Institución | Dominio | Evidencia |
|---|---|---|
| ClaveÚnica | `claveunica.gob.cl`, `claveunica.cl` | 200 «Portal ciudadano ClaveÚnica»; certificado `CN=claveunica.gob.cl`, SAN `*.claveunica.cl` |
| SII | `sii.gob.cl` | 200 → `homer.sii.cl`; certificado `O=SERVICIO DE IMPUESTOS INTERNOS` |
| ChileAtiende | `chileatiende.gob.cl` | 200; certificado `CN=*.chileatiende.gob.cl` |
| SUBTEL | `subtel.gob.cl` | 200; certificado `CN=subtel.gob.cl` |
| FONASA | `fonasa.gob.cl` | `fonasa.cl` 200 → `www.fonasa.gob.cl`, «Fondo Nacional de Salud \| Fonasa» |
| Servel | `servel.cl` | 200 «Servicio Electoral de Chile»; certificado `O=SERVICIO ELECTORAL` |
| SERNAC | `sernac.cl` | 200; certificado `CN=*.sernac.cl` |
| Carabineros | `carabineros.cl` | 200; certificado `O=DIRECCION DE LOGISTICA DE CARABINEROS` |
| PDI | `pdichile.cl` | 200 «Policía De Investigaciones De Chile»; certificado `CN=pdichile.cl` |
| Correos de Chile | `correos.cl` | 200; certificado `O=Empresa de Correos de Chile` |
| Metro | `metro.cl` | 200 «Metro de Santiago»; certificado SAN `metro.cl`, `*.metro.cl` |
| TVN | `tvn.cl` | 200; certificado `CN=tvn.cl`, SAN `*.tvn.cl` |
| Codelco | `codelco.cl`, `codelco.com` | `codelco.cl` → `www.codelco.com`; certificado `O=Corporacion Nacional del Cobre de Chile` |
| TGR | `tgr.cl` | 200; certificado `CN=*.tgr.cl`, SAN `tgr.cl` |
| **Banco Ripley** | `bancoripley.cl` | certificado `O=BANCO RIPLEY` |
| Ripley | `ripley.cl` | certificado `CN=ripley.cl` |
| BCI | `bci.cl` | certificado `O=Banco de Credito e Inversiones` |
| Banco Itaú | `itau.cl` | certificado `O=BANCO ITAU CHILE` |
| Banco de Chile | `bancochile.cl` | certificado `businessCategory=Private Organization` |
| Banco Falabella | `bancofalabella.cl` | certificado `CN=bancofalabella.cl` |
| Copec | `copec.cl` | certificado `CN=copec.cl` |
| Soprole | `soprole.cl` | certificado `CN=www.soprole.cl` |
| **BancoEstado** | `bancoestado.cl` | **1.825 certificados**: `*.bancoestado.cl`, `*.auth.vibe.bancoestado.cl`, `*.open-banking-mtls-prod.bancoestado.cl`; `www` en Akamai |
| Santander | `santander.cl` | **1.865 certificados**: `*.dev.wp.banco.santander.cl`, `*.author.prod.wp.banco.santander.cl`; `www` en Akamai |
| Scotiabank | `scotiabank.cl` | **572 certificados**: `Portal-ScotiaEmpresas.scotiabank.cl`, `Origenmty-banco.scotiabank.cl`; `www` en Akamai |

### Los tres últimos, y el blocker que no era (`T1.8b`)

**`bancoestado.cl` es el 36 % del corpus** y era el hueco más grande que quedaba. Los tres estaban
declarados como imposibles de verificar porque **su DNS no resolvía desde esta máquina**.

**El blocker no era el sitio: era la sonda.** Dos hallazgos:

1. **La raíz de los tres no tiene registro A.** Solo `www.` resuelve — el mismo patrón que ya había
   aparecido con `fonasa.gob.cl`. Preguntar por la raíz y concluir «no existe» era el error.
2. **El DNS local se puede rodear.** `dns.google` resuelve por HTTPS, y `crt.sh` da los certificados
   **emitidos** para un dominio: eso prueba que existe y quién lo pidió, sin necesidad de DNS.

Los certificados son concluyentes porque **nombran subsistemas internos de un banco** —`open-banking
mtls-prod`, `Portal-ScotiaEmpresas`, `wp.banco`— que nadie más tendría. Y los tres `www` están detrás
de Akamai, que es lo que usan los bancos chilenos.

> **Consecuencia para el método:** un dominio que «no resuelve» **no es un dominio que no existe**.
> Antes de declararlo hueco hay que probar `www.`, preguntar por HTTPS y mirar los certificados
> emitidos.

### Las ocho últimas entraron por una medición, no por gusto (`T1.8`)

El corpus de `doc/12-MEDICION.md` —45 estafas reales del CSIRT— dice a quién suplantan de verdad:
**Banco Ripley 21 veces**, BancoEstado 16, y una cada uno para Copec, Santander y Soprole.

Con el catálogo solo de instituciones estatales, **el motor reconocía de quién decía ser el mensaje
en 0 de 45 casos**, y el veredicto `NO_COINCIDE` era inalcanzable. Con estas ocho entradas pasó a
**24 de 45 (53 %)**.

**Los alias son parte del dato, no un adorno.** El corpus escribe «Banco Ripley», «bancoripley» y
«banco ripley» para lo mismo; comparar solo contra el nombre normalizado perdía dos de las tres. Un
alias va en minúsculas y sin tildes porque el texto del mensaje se pliega antes de comparar, y hay un
test que lo fija.

## Lo que la medición corrigió, y por eso se mide

| Hallazgo | Consecuencia |
|---|---|
| **`servel.gob.cl` no existe y `servel.cl` sí** | Sin catálogo, un mensaje legítimo del Servel se leería como falso. **Es el caso que justifica todo el módulo** |
| `fonasa.cl` es un redirector hacia `fonasa.gob.cl` | Se guarda el destino, no el que se escribe |
| `sii.gob.cl` redirige a `homer.sii.cl` | La entrada guarda la **etiqueta registrable**, que es lo que se compara |
| `codelco.cl` redirige a `codelco.com` | Se guardan los dos |
| `fonasa.gob.cl` **no tiene registro DNS** en la raíz; `www.fonasa.gob.cl` sí | La sonda de vida prueba los dos hosts |
| `sii.gob.cl` sirve una cadena de certificado que Python no puede validar | La sonda cuenta un fallo de certificado como «vivo»: el servidor contesta |

**Cuatro de catorce entradas estaban mal en el borrador escrito de memoria.** Ninguna de las cuatro
se habría notado sin abrir el sitio.

## Lo que queda afuera, y por qué no se adivina

**BancoEstado, Banco de Chile, Registro Civil, MINSAL y JUNAEB** quedaron fuera: **su DNS no resuelve
desde la máquina donde se hizo la verificación** (`curl: (6) Could not resolve host`).

No se inventó el dominio para completar la lista. Queda **declarado** como hueco conocido, y significa
que hoy un mensaje legítimo de BancoEstado con su enlace real **se leería como ajeno** — el error que
el catálogo existe para evitar. Cerrarlo requiere verificar esos dominios desde otra red.

## Cómo crece

1. Abrir el sitio y leer su **certificado**: el `O=` o el `CN=` tienen que nombrar a la institución.
2. Anotar la evidencia acá, con la fecha.
3. Agregar la entrada en `src/vigia/marcas.py` —`nombre` normalizado en minúsculas, `etiqueta` con
   la grafía que se le muestra a una persona, `oficiales` ya reducido a etiqueta registrable—.
4. Correr `VIGIA_INTEGRACION=1 uv run pytest tests/test_marcas.py -m integracion`, que vuelve a medir
   la lista entera.

**El paso 4 es lo que impide que una lista de confianza se pudra en silencio.** Es el único tipo de
dato de este proyecto que empeora solo con el tiempo.
