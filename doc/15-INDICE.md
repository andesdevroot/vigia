# 15 — El índice de indicadores del Estado

## Qué es

Un archivo dentro del paquete: **738 dominios que el Estado ya publicó como fraudulentos**, cada uno
con los códigos de las alertas que lo dicen. La consulta es un `dict.get`.

```
"ucmstudio.info": ["8fph22-00693-01", "8fph22-00672-01", ...]
```

## Por qué cambia el motor

Hasta `T4.2` el motor juzgaba un enlace **por su forma**: si termina en `.gob.cl`, si es de una
institución del catálogo, si se parece a una marca. Nada de eso usa la **historia** del dominio.

El índice agrega lo único que el Estado ya sabe y nosotros no. Y **no predice: cita.**

| Veredicto | Qué afirma |
|---|---|
| `AJENO` | «no es de nadie que yo conozca» — **débil** |
| `CONFIRMADO` | «el CSIRT publicó que este dominio es fraudulento, en **esta** alerta» |

Lo segundo no es una inferencia: es un hecho con fuente, y el ciudadano puede ir a leerla. Por eso
**manda sobre todos los demás veredictos**.

## De dónde sale

| Fuente | Qué aporta |
|---|---|
| `github.com/csirtcl/Fraude` | **785 informes**, cada uno con sus URLs y sus dominios |
| `corpus/alertas_csirt.json` | las URLs de las 342 alertas ya cosechadas |

Se reconstruye con `scripts/construir_indice.py`, que es reproducible y no necesita credenciales.

## Las dos cosas que **no** se pueden confirmar, y las encontraron los tests

### 1. Plataformas compartidas

El CSIRT reporta **una URL** en `bit.ly`, y eso **no** vuelve fraudulento a `bit.ly`, que aloja los
enlaces de todo el mundo. Confirmar el dominio entero condenaría a medio internet.

Medido en el índice: **70 alertas reportan un `bit.ly`**, 21 un `web.app`, 12 un `myshopify.com`,
10 un `is.gd`, 7 un `firebaseapp.com`, 6 un `cloudflare-ipfs.com`.

Los acortadores y el hosting gratuito son **dónde vive** el phishing, no **qué es**. Es la misma
lección de `T0.2`, cuando el canal de Certificate Transparency resultó no tener volumen.

### 2. Sufijos públicos

El índice guardaba **`com.br`** (14 alertas), **`com.au`** (10) y **`com.np`** (8). Eso no son
dominios: son **sufijos de registro**.

`etiqueta_registrable` reduce por etiquetas contadas —dos, o tres para `.gob.cl`— y no conoce la
lista de sufijos públicos. Entonces `algo.com.br` se reduce a `com.br`, y confirmarlo habría
condenado a **todo Brasil**.

**Limitación declarada:** el motor sigue reduciendo `algo.com.br` a `com.br`. Para un proyecto
chileno el impacto es bajo —el fraude local usa `.cl` y TLDs aleatorios—, pero **está mal** y queda
anotado.

## Cómo se hace cumplir

El filtro está **en la consulta y no solo al construir el índice**. Aunque el archivo traiga un
`bit.ly`, la respuesta nunca puede confirmarlo. Hay dos tests que lo fijan con un índice que los
contiene a propósito.

**Un dato que no se puede defender en la consulta no se defiende en ninguna parte.**

## Ética

Solo se **lee** lo publicado con TLP:CLEAR. Las URLs se guardan **reducidas a dominio** y **jamás se
visitan**. No hay datos personales: el índice es una lista de dominios y códigos de alerta.

## Cómo se reconstruye

```bash
python3 scripts/construir_indice.py     # ~3 minutos, con pausa entre consultas
```

Corre además `test_los_dominios_del_catalogo_siguen_vivos`, que es el recordatorio de que **una lista
de confianza —o de desconfianza— empeora sola con el tiempo**.
