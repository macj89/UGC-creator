# UGC Creator

Sistema para crear y probar anuncios verticales de estilo UGC para reformas e inmobiliaria.

## UGC Studio — interfaz principal

El MVP principal es un estudio visual por nodos inspirado en ComfyUI, orientado a dirección audiovisual en vez de a parámetros técnicos aislados. Incluye canvas editable, inspector contextual, monitor 9:16, cola, persistencia y tres workflows:

- reforma con transformación cinematográfica;
- tour inmobiliario editorial;
- presentador UGC consentido con B-roll.

Los nodos cubren brief, activos reales, dirección creativa, diseño de plano, imagen-a-vídeo, look development, voz, montaje, continuidad, QA y variantes. Los controles incluyen óptica, encuadre, cámara, intensidad de movimiento, seed, steps, guidance, color, textura, interpretación, ritmo, subtítulos y exportación.

Para abrir el estudio:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\ugc-studio.exe
```

Con la instalación compartida de ComfyUI ya disponible, el arranque recomendado es:

```powershell
.\start-studio.ps1
```

El nodo `Keyframe · Flux local` ejecuta realmente Flux GGUF en ComfyUI y devuelve la imagen al monitor. El nodo `Hero motion · OpenRouter` permite seleccionar Kling o Veo usando `OPENROUTER_API_KEY`. ElevenLabs queda disponible para voz mediante `ELEVENLABS_API_KEY`. Las claves permanecen exclusivamente en el backend.

Se abre en `http://127.0.0.1:8765`. ComfyUI genera los keyframes localmente. Después de obtener un keyframe, el nodo de vídeo puede enviarlo a Kling o Veo mediante OpenRouter, siempre tras una confirmación explícita de modelo, duración y resolución.

Para navegar por el graph: arrastra el fondo vacío para desplazarte, usa la rueda o `+ / −` para cambiar el zoom y pulsa `⌗` para encajar el workflow completo. Seleccionar un nodo abre sus controles en el inspector.

La interfaz CLI/FFmpeg descrita más abajo se conserva como backend determinista y prueba técnica. No representa el aspecto final del contenido ni la experiencia principal del producto.

## Tesis

No intentamos entrenar un modelo fundacional ni clonar toda una plataforma como Higgsfield. Construimos una capa de dirección creativa y producción que convierte los activos reales de cada negocio en muchas variantes publicables:

`brief + fotos/vídeos + oferta -> concepto -> guion -> storyboard -> voz/actor -> montaje -> subtítulos -> variantes -> exportación`

El sistema será local-first y modular. La generación pesada podrá ejecutarse en una GPU local, una GPU alquilada o una API sin cambiar el resto del flujo.

## Primeros casos de uso

### Reformas

- Antes/después narrado: “Este piso parecía perdido, pero mira el resultado”.
- Presupuesto transparente: tres decisiones que encarecen una reforma.
- Diario de obra: problema, solución y resultado en 20-30 segundos.
- Falso podcast o selfie educativo con imágenes reales de apoyo.
- Testimonio recreado solo con consentimiento y claramente identificado si es sintético.
- Variantes por barrio, tipo de vivienda, estancia, presupuesto y objeción.

### Inmobiliaria

- Presentador virtual sobre fotos y clips reales del inmueble.
- Recorrido con parallax y movimientos suaves a partir de fotografías.
- “Tres razones para visitar este piso” y “Para quién encaja / para quién no”.
- Vídeos por perfil: familia, inversor, primera vivienda o comprador internacional.
- Versiones multidioma a partir de una misma ficha.
- Pack UGC como servicio adicional para propietarios y promotores.

## MVP

Entrada:

- ficha del inmueble o brief de la reforma;
- 8-20 fotos y clips reales;
- identidad de marca, zona, precio/oferta y llamada a la acción;
- consentimiento y derechos de imagen.

Salida:

- 3 conceptos;
- 3 hooks por concepto;
- un vídeo maestro vertical de 20-35 segundos;
- 5-9 variantes cambiando hook, orden, voz y CTA;
- subtítulos incrustados y exportación 1080x1920.

## Arquitectura propuesta

1. **Director creativo**: genera ángulos, hooks, guion, lista de planos y claims verificables.
2. **Gestor de activos**: clasifica estancias, antes/después, obra, acabados y planos aprovechables.
3. **Generador visual**: imagen-a-vídeo y B-roll con ComfyUI + Wan/LTX, local o remoto.
4. **Presentador y voz**: voz sintética consentida, talking head opcional y lip-sync.
5. **Editor determinista**: FFmpeg y una plantilla programática para cortes, overlays, branding y subtítulos.
6. **Motor de variantes**: combina hooks, voces, duraciones, CTA y orden de escenas.
7. **Control de calidad**: valida artefactos, datos del inmueble, claims, identidad y disclosure.
8. **Medición**: registra cada variante y sus métricas para aprender qué hooks y formatos funcionan.

## Principios del producto

- Activos reales primero; generación sintética como apoyo.
- La autenticidad importa más que un acabado excesivamente cinematográfico.
- Nunca alterar de forma engañosa dimensiones, vistas, estado o acabados de un inmueble.
- No fabricar testimonios ni suplantar a personas reales.
- Guardar trazabilidad de fuentes, prompts, modelos y versiones.
- Diseñar para experimentar: una pieza no es el producto; lo es el sistema de variantes.

## Fases

### Fase 1 — Prototipo sin avatar

Fotos reales, movimiento 2.5D, voz en off, textos, subtítulos y edición automática. Es la opción más rápida, barata y fiable para validar demanda.

### Fase 2 — Presentador UGC

Actor propio o avatar consentido, planos selfie, lip-sync y combinación con B-roll real.

### Fase 3 — Generación y personalización a escala

Imagen-a-vídeo, múltiples idiomas, personalización por zona/audiencia y lotes de anuncios conectados a fichas de inmuebles.

## Primera prueba recomendada

Elegir una reforma con buen antes/después y un inmueble con al menos 12 fotos. Crear para cada uno tres enfoques:

1. historia/transformación;
2. utilidad/consejo;
3. oferta/visita.

Publicar variantes controladas y medir retención a 3 segundos, tiempo medio de reproducción, clics, leads y coste por lead. La decisión de invertir más en generación local debe basarse en esta prueba, no solo en la calidad visual.

## MVP ejecutable

El repositorio incluye un pipeline local de extremo a extremo. Usa Python 3.12 y FFmpeg para inventariar activos, crear conceptos y hooks, generar una timeline, renderizar un maestro vertical, producir cinco variantes y verificar técnicamente las salidas. No descarga modelos.

### Preparación

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m ugc_creator doctor
```

### Demostración completa

```powershell
.\.venv\Scripts\python.exe -m ugc_creator demo workspace\projects\demo-reforma
.\.venv\Scripts\python.exe -m ugc_creator all workspace\projects\demo-reforma
```

El proyecto demo crea ocho imágenes abstractas y una voz de sistema únicamente para validar el pipeline. Está marcado como `demo_only` y no representa una reforma real.

Las salidas aparecen en `workspace/projects/demo-reforma/renders/`: maestro y SRT, dos variantes de hook, dos de CTA, una de orden, manifiestos reproducibles y controles automáticos.

### Usarlo con activos reales

1. Copiar el proyecto demo a otra carpeta dentro de `workspace/projects/`.
2. Sustituir los ocho PNG por 8-20 fotos o clips propios.
3. Actualizar `project.yaml`, incluidos brief, marca, derechos, CTA y rutas.
4. Añadir una voz WAV/MP3 consentida o eliminar `voiceover.path` para usar silencio.
5. Ejecutar `.\.venv\Scripts\python.exe -m ugc_creator all workspace\projects\mi-proyecto`.

Las etapas también se ejecutan por separado con `inspect`, `plan`, `render`, `variants` y `verify`. Los originales nunca se modifican. Los segmentos se cachean por hash para reutilizarlos entre variantes.

## Documentación técnica

- `docs/HARDWARE_AUDIT.md`: auditoría del portátil.
- `docs/ARCHITECTURE.md`: módulos, contratos y decisiones.
- `docs/IMPLEMENTATION_PLAN.md`: hitos posteriores al MVP.

## Licencia

MIT — ver [LICENSE](LICENSE).
