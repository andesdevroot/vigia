# 03 — T0.3: estado del arte

**2026-10-04.** Qué está ocupado, qué queda libre, y qué cambia eso en el plan.

## Método, y su límite

Búsqueda web dirigida a literatura y sistemas, no a notas de prensa. **Límite declarado: el documento
chileno más relevante está detrás de un muro anti-scraping** ([Anubis](https://repositorio.uchile.cl/handle/2250/202581),
prueba de trabajo) y **no pude leerlo**. De él solo tengo el título y fragmentos del índice. Eso es un
blocker de esta tarea, no un detalle: la evaluación de novedad frente a ese trabajo es **incompleta**.

## Lo que existe

| trabajo | qué es | relación con esto |
|---|---|---|
| [Tesis U. de Chile 202581](https://repositorio.uchile.cl/handle/2250/202581) | *Diseño e implementación de sistema automatizado de recolección y análisis de mensajes de texto fraudulentos* | **Chile YA tiene trabajo en esto.** Sistema de recolección y análisis de SMS, con salida JSON. Es el prior art nacional más cercano y **no pude leerlo** |
| [APWG eCrime 2023](https://docs.apwg.org/ecrimeresearch/2023/20240080211286378.pdf) | Una **whitelist** mejora la precisión y reduce falsos positivos | **La idea de certificar el verdadero por lista blanca ya está publicada.** Queda diferenciarse |
| [TraceScope (arXiv 2604.21840)](https://arxiv-org.ezproxy.obspm.fr/html/2604.21840v1) | Triaje interactivo de URL por *adjudicación con checklist* | Muy cercano al patrón preguntas → adjudicación de JEV. Prior art directo del mecanismo |
| [Multimodal phishing (IEEE)](https://xplorestaging.ieee.org/document/11580482) | GNN + BERT + CLIP sobre la página | Confirma el giro al **contenido** que la medición de T0.2 insinuó |
| [Digital Public Infrastructure (Zenodo)](https://www.zenodo.org/records/19150928) | Ciber-resiliencia de infraestructura pública digital en países en desarrollo | Marco donde encaja la ClaveÚnica |
| [Datasets de smishing (IMC 2025, NLPAICS 2026)](https://github.com/reportsmishing/Smishing-Dataset-IMC25) | Corpus etiquetados de reportes públicos, en inglés | El método del corpus está validado. **En español de Chile, no** |
| [urlscan Brand AI](https://urlscan.io/blog/2025/07/30/brand-ai-experimental/) · [CERT-AGID Italia](https://cert-agid.gov.it/news/smishing-a-tema-inps-implementata-verifica-documentale-tramite-intelligenza-artificiale/) | Industria y **un CERT estatal** | Un Estado ya usa IA contra smishing que suplanta a una agencia. El modelo institucional existe |

## Lo que queda libre

1. **Español de Chile, con etiqueta que no puso un anotador pagado.** Los corpus existentes son en
   inglés; la tesis chilena es un sistema, no un corpus público con medición.
2. **La calibración de la negativa medida por segmento.** No apareció en ninguno: todos miden
   precisión. **Nadie mide si el umbral deja pasar más estafas contra un segmento.**
3. **La medición negativa del canal de dominio.** Que buscar la marca en el nombre del dominio no
   tenga volumen **no está publicado**, y es un resultado con consecuencia de método.

## Lo que esto cambia

- **La idea 1 (corpus) pierde fuerza como contribución aislada.** Hay prior art chileno y hay corpus
  en inglés. El aporte tiene que ser **la calibración y la equidad del umbral**, no "un corpus más".
- **La idea 2 (lista blanca) tiene prior art** (APWG). El aporte no es el método, es **la medición
  que lo justifica** — y esa medición la tenemos hecha.
- **La idea 4 (adultos mayores) es la que queda más limpia.** Nadie de los revisados mide el efecto
  por segmento.

## Blocker

**No poder leer la tesis 202581 invalida cualquier afirmación fuerte de novedad frente a Chile.** Hay
que conseguirla: por el repositorio con un navegador, por el autor, o por la escuela de ingeniería.
Es la primera acción de la tarea siguiente.
