# vigia — el servidor del webhook.
#
# **No instala nada, y es a propósito.** El núcleo de decisión usa solo la stdlib, y hay un test que
# lo impone (`tests/test_despliegue.py`). Un `pip install` acá metería dependencias por la puerta de
# atrás y la propiedad que hace reproducible el veredicto se perdería sin que nadie se entere.
#
# Los secretos **no entran por COPY**: van por variables de entorno. Un `.env` copiado queda en las
# capas de la imagen para siempre, y las capas se publican.

FROM python:3.13-slim

# Sin bytecode al lado del código. Y sin buffer: en un contenedor los registros tienen que salir a
# medida que pasan, o depurar es adivinar.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Solo lo que el servidor necesita. El corpus va incluido para que la imagen sea el artefacto
# completo y no una parte.
COPY src/ ./src/
COPY corpus/ ./corpus/
COPY LICENSE LICENSE-CORPUS NOTICE ./

# **Sin root.** El proceso no escribe en el disco: la memoria del límite vive en RAM, a propósito.
RUN useradd --create-home --shell /usr/sbin/nologin vigia
USER vigia

# El puerto lo manda la plataforma por `PORT`. 8000 es el valor por defecto para correr local.
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-m", "vigia.salud"]

CMD ["python", "-u", "-m", "vigia.servidor"]
