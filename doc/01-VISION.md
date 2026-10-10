# 01 — Visión

**v0.1 · 2026-10-04 · HIPÓTESIS, NO DECISIÓN**

## El problema

En Chile, la **ClaveÚnica** es la llave maestra de los servicios del Estado, y su segundo factor es
un SMS. El **fraude de portabilidad no reconocida** (*SIM swapping*) convierte esa debilidad en un
ataque concreto: se pide un duplicado de SIM a nombre de la víctima, su teléfono queda sin señal, y
el atacante reinicia las claves bancarias desde ahí.

- **~700 reclamos ante SUBTEL en lo que va de 2026** por portabilidad no reconocida.
- SUBTEL está evaluando **más medidas de certificación de identidad** — o sea, la ventana está
  abierta.
- El ataque es de **dos fases**: primero se cosechan datos personales (sitios y mensajes falsos),
  después se pide el duplicado. **La fase 1 es la intervenible.**

## La hipótesis

> Existe una **superficie de suplantación** medible —sitios y mensajes que cosechan credenciales
> suplantando marcas chilenas— y se puede **vigilar de forma continua** con datos públicos.

Y si existe, la pregunta interesante no es *detectarla* sino **cómo avisar sin alarmar en falso**:
una falsa alarma en seguridad destruye confianza más rápido de lo que la detección la construye.

## Lo que hay que validar ANTES de construir

**`[T0.1]` es la tarea que decide si este proyecto existe.**

1. **¿Cuántos dominios de suplantación aparecen de verdad?** Los logs de *Certificate Transparency*
   son públicos y capturan cada certificado TLS emitido. Si filtrando `.cl` y similitud contra las
   marcas del Estado y la banca aparecen **cientos**, hay proyecto. Si aparecen **decenas**, hay una
   nota, no un paper.
2. **¿Cuánto cuesta el canal?** La API pública de `crt.sh` **falla (404) y es substring-exacta**: para
   typosquats hay que enumerar variaciones y consultar una por una. El canal real son los logs en
   bruto, que son un *stream*. Eso es infraestructura, no un script.

**Verificado ya, como indicio:** una consulta a `crt.sh` por `bancoestado` devolvió 2 dominios
registrables y **los 2 no oficiales** (`bancoestado--cl.xyz`, `derivacionbancoestado.cl`). Es una
anécdota, no una medición — pero el mecanismo detecta.

## Fuera de alcance, y por qué

- **"Alguien está usando tu clave"**: requiere ser el proveedor de identidad. Solo el Estado puede
  verlo, y un tercero no puede construirlo.
- **"Tu clave fue filtrada"**: requiere el corpus de filtraciones. Es un problema de datos, no de IA.

Lo construible desde afuera es **avisar del ataque antes de que la usen**, que es donde el aviso
todavía sirve.

## Métricas

| | |
|---|---|
| Cobertura | dominios de suplantación descubiertos / estimados |
| Precisión | falsos positivos sobre dominios legítimos |
| **Falsa alarma** | la métrica que decide si un aviso es usable |
| Antelación | tiempo entre el aviso y el primer uso conocido |
