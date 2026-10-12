# 16 — Publicar: el orden, y por qué el orden importa

**2026-10-11.** Dónde vive cada cosa, y la secuencia que no se puede invertir.

## Las tres cosas son distintas, y no se reemplazan

| | Qué da | Qué NO da |
|---|---|---|
| **Zenodo** | **DOI citable** del artefacto, gratis, sin aval | Lectores |
| **TechRxiv** | Preprint con marca **IEEE**, sin aval | Revisión de pares |
| **arXiv** | Prestigio y prioridad | **Pide endorsement** para el primer envío |
| **LinkedIn** | **Usuarios**, que es lo que falta | Cita. Nadie cita un post |

> **El cuello de botella del proyecto no es publicar. Es que nadie ha usado el bot.**

Cuatro mensajes de prueba, todos del autor. Por eso LinkedIn no es una alternativa a publicar: es
**otra cosa**, y es la que desbloquea la medición que el paper declara como fallo.

## El orden que no se puede invertir

**Zenodo solo recoge los releases creados DESPUÉS de activar el repositorio.** Si se crea el release
primero y se activa después, ese release **no recibe DOI** y hay que cortar otro.

```
1. Activar el repositorio en Zenodo        <- primero, siempre
2. Crear el release en GitHub              <- después
3. Zenodo le asigna el DOI solo
```

### Paso 1 — Activar en Zenodo (lo hace el autor, con su cuenta)

1. Entrar a <https://zenodo.org> y elegir **Sign in with GitHub**.
2. Ir a **Settings → GitHub** (<https://zenodo.org/account/settings/github/>).
3. Buscar `andesdevroot/vigia` en la lista y **poner el interruptor en ON**.
4. Volver a GitHub y **refrescar** la página de *Settings → Webhooks* del repositorio: Zenodo deja un
   webhook. Si no está, la conexión no quedó.

**No hay nada que subir a mano.** `.zenodo.json` ya está en la raíz del repositorio, así que Zenodo
toma el título, los autores, la licencia y las palabras clave de ahí. El archivo existe justamente
para no tener que llenar el formulario y para que los metadatos queden versionados con el código.

### Paso 2 — El release

```bash
git tag -a v0.1.0 -m "vigia 0.1.0"
git push origin v0.1.0
gh release create v0.1.0 --title "vigia 0.1.0" --notes-file doc/RELEASE-0.1.0.md
```

### Paso 3 — Verificar el DOI

En <https://zenodo.org/account/settings/github/> el repositorio tiene que mostrar un **badge con el
DOI**. Copiarlo y pegarlo en el README.

- **Versión específica:** `10.5281/zenodo.XXXXXXX` — cita **esta versión de los datos**. Es la que va
  en el paper.
- **Concepto:** `10.5281/zenodo.YYYYYYY` — apunta **siempre a la última**. Es la que va en el README.

> **En el paper se cita el DOI de la versión, no el de concepto.** Un resultado medido sobre datos que
> cambian no es reproducible.

### Alternativa sin GitHub

Si se prefiere no conectar la cuenta, Zenodo acepta una **subida manual**: se descarga el zip del
repositorio, se sube, y se pegan los mismos metadatos. Funciona igual y da el mismo DOI. Lo que se
pierde es que **cada release futuro reciba su DOI solo**.

## Después: TechRxiv, sin esperar a nadie

<https://www.techrxiv.org> — repositorio de IEEE, **abierto y moderado**, para ingeniería y ciencias
de la computación. **No pide endorsement de un tercero**, que es lo que arXiv sí pide.

El paper está en `.privado/` (fuera del control de versiones, ver `T2.1`). Se sube desde ahí.

**Y no hay conflicto con arXiv:** tener un preprint antes no impide publicar en arXiv después. Si el
endorsement llega, el mismo contenido va a los dos.

## Y el correo del trabajo: pensarlo dos veces

Usar el correo institucional **acelera el endorsement de arXiv**, porque acredita afiliación. Pero
tiene un costo que no es obvio:

> **El paper quedaría asociado al empleador.** Y este proyecto apunta a vender detección de
> suplantación **a bancos**, mientras el autor trabaja en uno.

Como Investigador Independiente la afiliación es limpia y no crea ese conflicto. Vale la pena
consultarlo en el trabajo **antes** de usar el correo, y no solo por permiso: por coherencia.

## Lo que sí desbloquea LinkedIn

No es una publicación: es **usuarios**. Y son los que faltan para dos cosas que el paper declara
como débiles:

| | |
|---|---|
| **El experimento de `T3.1`** | 20 personas × 3 mensajes. Diseñado, sin correr. Mide **qué fracción de los mensajes reenviados trae el enlace**, que es el número que decide la tesis del paper |
| **Sensibilidad** | ~40 mensajes etiquetados a mano. Pero primero hacen falta mensajes reales |
| **El corpus legítimo** | No existe, y bloquea **dos** mediciones |

Los tres necesitan lo mismo: **gente usando el bot.** Un post que diga «construí esto, pruébenlo» con
un número que lo respalde consigue eso; un preprint no.

## El repositorio, en una línea

**El paper es un producto del repositorio, no una parte del repositorio.** El paper vive en
TechRxiv o arXiv; el repositorio es el artefacto, y el DOI de Zenodo lo hace citable.
