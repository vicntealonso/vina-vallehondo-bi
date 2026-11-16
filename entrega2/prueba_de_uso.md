# Prueba de uso del prototipo — Grupo V1

**Requisito (enunciado E2, sección D):** al menos dos personas ajenas al grupo (otro grupo del curso o la contraparte) responden tres preguntas usando solo el prototipo, sin ayuda. Hay que registrar quién, cuánto demoró, qué no entendió y qué cambiamos después. Sin esta prueba, el componente D no puede quedar en "logrado".

**Tiempo por persona:** unos 10 minutos.

---

## Cómo hacerla

1. **Antes:** correr `python run.py` y abrir `streamlit run app.py`. Dejar la pantalla en la pestaña **Respuesta**, con la definición del informe (Día de la factura · Pesos · 2.º sem. vs 1.º · Promedio export.).
2. **Decir solo esto:** "Eres gerente comercial de una viña. Esta pantalla muestra el margen de cada mercado de exportación en 2025. Responde tres preguntas usando solo la pantalla; piensa en voz alta. No podemos ayudarte."
3. **Cronometrar** desde que lee la primera pregunta hasta que responde la tercera.
4. **No ayudar.** Si pregunta algo, responder "¿qué harías tú?" y anotar la duda: es justamente lo que buscamos.
5. **Anotar** dónde dudó, qué buscó y no encontró, y qué leyó mal.
6. **Al final** hacer las dos preguntas de cierre.

## Las tres preguntas (entregar impresas o en el chat)

1. **¿Qué mercado creció más en litros en 2025, y cuánto deja por litro frente al resto?**
2. **Si se convierte con el dólar del día del embarque en vez del de la factura, ¿cambia la conclusión sobre ese mercado?**
3. **¿Brasil es una recomendación o una hipótesis por validar? ¿Por qué?**

Preguntas de cierre:
- ¿Te serviría esta pantalla para decidir el descuento de un mercado? ¿Por qué?
- ¿Qué fue lo más difícil de encontrar o de entender?

### Respuestas correctas (solo para quien registra; no mostrar)

| # | Respuesta esperada | Dónde está en la pantalla |
|---|---|---|
| 1 | Corea del Sur, +33,8 %; deja 1.715 CLP/L, −24 % frente al resto (2.270). Bonus: calculado sobre el 73 % de sus litros | Cifra clave, arriba a la izquierda, y su cobertura al lado |
| 2 | No: Corea baja a 1.679 CLP/L, pero sigue creciendo con poco margen; ningún mercado cambia de clase | Filtro "Dólar para convertir" o pestaña "Definición y detalle" |
| 3 | Hipótesis: mantiene su conclusión solo en 2 de 8 definiciones (con la ventana trimestral no crece) | Tabla "Detalle por mercado", sección "Hipótesis a validar" |

---

## Registro (va en el informe, sección D, y completo en el Anexo B)

| | Persona 1 | Persona 2 | Contraparte (si responde) |
|---|---|---|---|
| Nombre y grupo o cargo | | | Benjamín Espinoza, contraparte (correo) |
| Fecha | | | |
| Tiempo total | | | — |
| Pregunta 1: ¿correcta? | | | |
| Pregunta 2: ¿correcta? | | | |
| Pregunta 3: ¿correcta? | | | |
| ¿Qué no entendió o dónde dudó? | | | |
| ¿Le serviría para decidir? (cita textual) | | | |

## Qué cambiamos después

Anotar cada cambio que produjo la prueba (el enunciado pide que "produjo cambios"):

| Observación de la prueba | Cambio en el prototipo | Commit |
|---|---|---|
| | | |
| | | |

Cuando tengan las observaciones, pásenmelas y hago los cambios en `app.py`; quedan en un commit identificable para citarlo aquí.
