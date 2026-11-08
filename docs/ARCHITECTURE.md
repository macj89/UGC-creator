# Arquitectura del MVP

## Decisión

El MVP será una aplicación local-first de línea de comandos, organizada como un pipeline reanudable. Python 3.12 orquesta trabajos y FFmpeg produce el vídeo de forma determinista. Los motores generativos se conectarán después mediante adaptadores por capacidad, sin formar parte del núcleo.

La primera prueba debe terminar en un MP4 vertical reproducible utilizando fotos y clips reales, movimiento 2.5D sencillo, voz en off, música opcional, overlays, CTA y subtítulos. No incluye avatar, lip-sync, entrenamiento ni generación pesada.

## Flujo de datos

```text
brief + marca + activos + consentimiento
                 |
                 v
        validación e inventario
                 |
                 v
    conceptos -> hooks -> guion
                 |
                 v
       storyboard / timeline
                 |
                 v
 voz + planos reales + subtítulos
                 |
                 v
      compositor FFmpeg/NVENC
                 |
                 v
 maestro + variantes + manifiesto + métricas
                 |
                 v
          control y aprobación humana
```

## Límites de los módulos

### Dominio

Define estructuras estables y sin dependencias de proveedor:

- `ProjectBrief`: negocio, audiencia, oferta, zona, CTA y restricciones.
- `Asset`: ruta, tipo, dimensiones, duración, procedencia, derechos y etiquetas.
- `Claim`: texto, fuente, estado de verificación y fecha.
- `Concept`, `Hook`, `Script`, `Shot` y `Timeline`.
- `RenderRecipe`: entradas, versiones, parámetros, seed cuando aplique y hashes.
- `Variant`: cambios respecto al maestro.
- `Evaluation`: validaciones técnicas, revisión humana y métricas de publicación.

### Ingesta y catálogo de activos

Lee un proyecto, ejecuta `ffprobe`, normaliza metadatos y genera proxies o miniaturas en caché. Nunca modifica el original. Los emparejamientos antes/después y las etiquetas de estancia comienzan manuales; la clasificación automática puede añadirse después.

### Dirección creativa

Produce propuestas estructuradas, no vídeo. En el MVP puede operar con plantillas y edición humana. Cualquier LLM futuro será un adaptador que devuelva el mismo esquema y no podrá aprobar claims por sí solo.

### Planificador

Convierte guion y storyboard en una timeline declarativa. Resuelve duraciones, recortes, safe areas, transiciones, voz, música, subtítulos y overlays antes del render. La timeline es la fuente de verdad del montaje.

### Render determinista

Compila la timeline a filtros/comandos FFmpeg. Debe soportar:

- lienzo 1080 x 1920 y duración de 20-35 segundos;
- fotos con zoom/pan/parallax sencillo y clips con recorte controlado;
- textos y logotipos renderizados, nunca generados dentro de una imagen;
- mezcla de voz y música con niveles explícitos;
- subtítulos incrustados y archivo SRT/VTT asociado;
- H.264 NVENC como salida de trabajo, con fallback por CPU;
- sustitución de un plano sin regenerar activos no afectados.

### Variantes

Aplica parches declarativos a la receta maestra: hook, CTA, voz, orden o duración. Comparte intermediarios por hash y crea un manifiesto distinto para cada salida.

### Control de calidad

Dos barreras separadas:

- automática: resolución, relación de aspecto, duración, audio, frames negros, subtítulos, archivos ausentes y hashes;
- humana: fidelidad del inmueble/reforma, claims, marca, ritmo, autenticidad, consentimiento y disclosure.

### Motores intercambiables

La frontera futura se define por capacidad:

```python
class ImageToVideoEngine(Protocol):
    def generate(self, request: ImageToVideoRequest) -> GeneratedAsset: ...
```

El mismo patrón se aplicará a `image_generation`, `voice`, `talking_head`, `lip_sync` y `upscale`. Cada resultado debe registrar proveedor, modelo, versión, parámetros, coste, latencia, VRAM y procedencia. Los adaptadores local, GPU alquilada y API no deben filtrarse al dominio ni al renderizador.

## Estructura propuesta

```text
UGC-creator/
  docs/
  src/ugc_creator/
    domain/          # modelos y reglas puras
    project/         # carga, validación y manifiestos
    assets/          # ffprobe, catálogo, proxies y hashes
    creative/        # plantillas de concepto, hook y guion
    planning/        # storyboard y compilación de timeline
    render/          # composición FFmpeg y subtítulos
    variants/        # parches y matriz de variantes
    quality/         # controles automáticos y checklist humano
    engines/         # protocolos; adapters/ se añade al integrar motores
    telemetry/       # tiempos, recursos, fallos, costes y calidad
    cli.py
  schemas/           # JSON Schema versionados
  templates/         # estilos de vídeo y branding, sin datos del cliente
  examples/          # proyecto sintético pequeño y redistribuible
  tests/
    unit/
    integration/
    fixtures/
  workspace/         # datos locales ignorados y no sincronizados
```

## Contrato de proyecto

Cada trabajo tendrá una carpeta independiente:

```text
workspace/projects/<project_id>/
  project.yaml
  assets/originals/
  assets/proxies/
  creative/concepts.json
  creative/script.json
  timeline/master.json
  variants/
  renders/
  manifests/
  reviews/
  logs/
```

`project.yaml` referencia originales y recoge derechos, pero los originales no se duplican si ya residen en una ubicación controlada. Los manifiestos y recetas son datos pequeños y trazables; proxies, cachés y renders son regenerables.

## Reanudación y caché

Cada etapa consume artefactos versionados y produce resultados direccionados por hash. Una etapa se reutiliza si coinciden:

- hash de entradas;
- versión del esquema y del código de la etapa;
- parámetros y versión de herramientas o motor.

Esto permite cambiar el CTA sin recalcular voz o planos, y reemplazar una toma sin reconstruir todo el anuncio.

## Decisiones tecnológicas del MVP

| Área | Elección inicial | Motivo |
| --- | --- | --- |
| Runtime | Python 3.12 | Compatibilidad y orquestación simple |
| Modelos de datos | Dataclasses + validación de esquema | Contratos explícitos sin framework pesado |
| Configuración | YAML de autoría + JSON normalizado | Editable por humanos y reproducible |
| Render | FFmpeg / FFprobe | Determinista, disponible y acelerado |
| Codificación | H.264 NVENC; fallback libx264 | Velocidad local y portabilidad |
| CLI | `python -m ugc_creator` | Primera interfaz mínima y automatizable |
| Estado | Archivos + manifiestos | Sin base de datos ni servicio prematuros |
| Pruebas | Unitarias + render corto de integración | Verifica reglas y salida audiovisual |

No se necesita aún frontend web, base de datos, cola distribuida, Docker, ComfyUI ni CUDA Toolkit.

## Criterio de éxito del MVP

El MVP está validado cuando un proyecto de prueba real puede producir, en una ejecución repetible:

1. inventario verificable de 8-20 activos;
2. tres conceptos y tres hooks por concepto;
3. storyboard y timeline revisables;
4. un maestro 1080 x 1920 de 20-35 segundos;
5. al menos cinco variantes sin duplicar trabajo innecesario;
6. subtítulos y CTA legibles dentro de safe areas;
7. manifiestos con hashes, herramientas, parámetros, tiempos y procedencia;
8. checklist de aprobación de claims, derechos y fidelidad visual.

