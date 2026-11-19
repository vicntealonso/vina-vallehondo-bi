# Prueba de uso del prototipo

Dos personas de otros grupos del curso respondieron tres preguntas usando solo el prototipo publicado (https://vina-vallehondo-bi.streamlit.app/), sin ayuda del grupo. Se cronometró cada pregunta y al final se les preguntó si la pantalla les serviría para decidir el descuento de un mercado.

## Preguntas

1. ¿Qué mercado creció más en litros entre el 1.er y el 2.º semestre de 2025, y cuánto deja por litro frente al resto?
2. ¿Brasil es una recomendación o una hipótesis a validar? ¿Por qué?
3. Con el dólar del día del embarque, ¿cambia la conclusión? ¿Sigue siendo el mismo mercado el que deja menos margen por litro?

## Resultados

| | Josefa Abett de la Torre (G7) | Aracely Paillal (G2) |
|---|---|---|
| Fecha | 17-11-2026 | 18-11-2026 |
| Contactada por | Vicente Gajardo | Vanessa Castro |
| Tiempo total | ~5 min | ~6 min |
| Correctas | 3 de 3 | 1 completa; 2 correctas pero incompletas |
| Qué le costó | Por qué Brasil es hipótesis («2 de 8» no dice qué definición lo cambia); que el recuperable y el equilibrio no cambian con el filtro del dólar; la columna «Margen litros extra»; encontrar el simulador | La cifra clave no decía que Corea es la que más creció; el filtro tenía otro nombre en el test; qué significa «Embarque»; el contexto del rubro |
| ¿Le sirve para decidir? | «Sí, en buena parte. Muestra el problema y su causa […]. Para negociar me faltaría ver el descuento por cliente/contrato dentro de Corea del Sur, y que el simulador esté más a la vista» | «Puede ser. Teniendo bien explícitos los KPIs principales» |

## Qué cambiamos después

| Observación | Cambio en el prototipo | Commit |
|---|---|---|
| No se entiende por qué Brasil es hipótesis | Junto a «2 de 8» se muestra con qué definiciones cambia (trimestral y mediana) | b5f5f80 |
| El recuperable no cambia con el filtro del dólar | Nota: se calcula siempre con el dólar de la factura | b5f5f80 |
| Columna «Margen litros extra» poco clara | Ayuda (tooltip) en la columna | b5f5f80 |
| El simulador está escondido en la segunda pestaña | Acceso al simulador desde la pantalla principal | b5f5f80 |
| La cobertura cuesta entenderla | Redactada como «73 de cada 100 litros» | b5f5f80 |
| Para negociar faltaba el descuento por cliente dentro de Corea | Tabla de descuento, margen y recuperable por cliente de Corea, dentro del simulador | 25d4735 |
| La cifra clave no dice que Corea es la que más creció | Ahora dice «el mercado que más creció en litros» | c47d65e |
| No se entiende «Embarque» | Ayuda en el filtro que explica factura y embarque | c47d65e |
| Falta contexto del rubro | No se agregó: la pantalla es para la gerencia de la viña | — |

Captura de la versión actual: [captura_prototipo.png](captura_prototipo.png).
