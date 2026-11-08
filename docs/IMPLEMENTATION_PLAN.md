# Plan de implementación del MVP

## Hito 0 — Base reproducible

- Inicializar Git cuando el propietario lo apruebe.
- Crear el paquete Python 3.12 y pruebas mínimas.
- Versionar los esquemas de proyecto, activo, timeline, receta y evaluación.
- Añadir un comando `doctor` que compruebe Python, FFmpeg, FFprobe y NVENC sin instalar nada.

Salida: el entorno puede diagnosticarse y un proyecto vacío puede validarse.

## Hito 1 — Proyecto real e ingesta

- Elegir una reforma con buen antes/después como primera prueba.
- Reunir 8-20 fotos/clips, marca, oferta, zona, CTA y evidencia de claims/derechos.
- Catalogar dimensiones, duración, orientación, hash y procedencia.
- Etiquetar manualmente antes/después, estancia y prioridad.

Salida: inventario revisado y brief válido. No se genera contenido sintético.

## Hito 2 — Dirección y timeline

- Crear plantillas para transformación, utilidad y oferta.
- Producir tres conceptos y tres hooks por concepto.
- Elegir un concepto y convertirlo en guion, storyboard y timeline declarativa.
- Añadir una pista de voz temporal o consentida y subtítulos sincronizados.

Salida: plan completo del anuncio revisable antes de renderizar.

## Hito 3 — Render vertical determinista

- Implementar recorte 9:16, Ken Burns/parallax simple, cortes y transiciones limitadas.
- Implementar branding, textos, CTA y safe areas.
- Mezclar voz/música y exportar subtítulos.
- Codificar con NVENC y verificar con FFprobe.

Salida: un maestro 1080 x 1920 de 20-35 segundos con manifiesto reproducible.

## Hito 4 — Variantes y control de calidad

- Definir parches de hook, CTA, orden, voz y duración.
- Reutilizar intermediarios por hash.
- Crear al menos cinco variantes.
- Ejecutar controles automáticos y completar aprobación humana.

Salida: lote comparable, trazable y listo para una publicación controlada.

## Hito 5 — Medición

- Registrar identificador de variante, canal y fecha.
- Capturar retención a 3 segundos, tiempo medio, clics, leads y coste por lead.
- Comparar una sola variable por grupo cuando sea posible.

Salida: datos suficientes para decidir qué formato merece iteración.

## Hito 6 — Primer motor generativo, solo tras validar el flujo

- Seleccionar un único plano difícil de conseguir con activos reales.
- Evaluar un motor local que quepa en 8 GB de VRAM y el mismo plano mediante API.
- Medir calidad, consistencia, tiempo, VRAM y coste.
- Integrarlo mediante el protocolo de capacidad, no dentro del renderizador.

Salida: decisión basada en una comparación real. Este hito requiere aprobación antes de descargar pesos o contratar una API.

## Siguiente acción concreta

Crear el contrato de datos y el comando `doctor`, y en paralelo preparar la carpeta del primer caso de reforma. La selección del caso y sus activos requiere información del propietario; la infraestructura determinista no.

