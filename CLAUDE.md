# UGC Creator — contexto para agentes

## Misión

Construir un estudio de producción UGC asistido por IA para pymes y empresas que no pueden asumir rodajes publicitarios tradicionales. Los primeros clientes y bancos de pruebas serán una empresa de reformas y una inmobiliaria propias.

Esto no es un parche ni un generador de un solo vídeo. El objetivo es un sistema de producción modular, repetible y comercializable que pueda mejorar al aparecer nuevos modelos.

El propietario del proyecto es supervisor de CGI. El sistema debe aprovechar su criterio de dirección visual, composición, continuidad, integración y control de calidad; no intentar sustituirlo con una caja negra.

## Entorno principal

- Desarrollar y ejecutar preferentemente en el portátil con RTX 4070.
- La carpeta se comparte mediante Syncthing con otros equipos.
- Antes de instalar modelos, comprobar sistema operativo, VRAM real, RAM, almacenamiento libre, CUDA, controladores y versiones de Python/Node/FFmpeg.
- No descargar pesos grandes ni contratar APIs sin aprobación explícita.
- No sincronizar por Syncthing pesos de modelos, cachés, renders temporales, entornos virtuales ni dependencias regenerables.

## Tesis de producto

La ventaja competitiva no será clonar un modelo fundacional. Será la capa de dirección y producción:

`brief + activos reales -> estrategia -> hooks -> guion -> storyboard -> planos -> voz/presentador -> composición -> edición -> variantes -> aprobación -> métricas`

Los motores generativos deben ser intercambiables:

- GPU local para desarrollo, imágenes, composición y generaciones compatibles con la VRAM disponible.
- GPU alquilada para lotes o modelos pesados.
- APIs externas para planos premium o capacidades que aún no sean competitivas en local.

Un cambio de modelo o proveedor no debe obligar a reescribir el producto.

## Principios técnicos

1. Diseñar interfaces por capacidad (`image_generation`, `image_to_video`, `talking_head`, `voice`, `upscale`, etc.), no por proveedor.
2. Guardar recetas reproducibles: modelo, versión, seed, prompt, workflow, parámetros y activos de origen.
3. Separar claramente dirección creativa, generación, composición, edición y exportación.
4. Usar activos reales como base siempre que aumenten autenticidad o precisión.
5. Mantener un editor determinista para textos, logotipos, subtítulos, CTA y exportaciones; no pedir a un modelo generativo que produzca texto legible.
6. Diseñar desde el principio para variantes y evaluación, no solo para una pieza final.
7. Poder reanudar trabajos, reemplazar un plano y volver a renderizar sin regenerar todo el anuncio.
8. Registrar costes, tiempos, VRAM, fallos y calidad por motor.

## Primer producto mínimo

Crear anuncios verticales 9:16 de 20-35 segundos a partir de fotos, clips y datos reales.

Entrada mínima:

- brief de reforma o ficha de inmueble;
- 8-20 fotos o clips;
- identidad de marca;
- oferta, zona, audiencia y CTA;
- derechos y consentimientos necesarios.

Salida mínima:

- tres conceptos creativos;
- tres hooks por concepto;
- storyboard y lista de planos;
- un vídeo maestro;
- cinco o más variantes de hook, voz, orden o CTA;
- subtítulos y exportación 1080x1920;
- manifiesto reproducible del proyecto.

La primera versión no necesita un avatar. Debe validar el flujo con fotografía real, movimiento 2.5D/parallax, voz en off, B-roll, textos, subtítulos y montaje automático. El presentador UGC y el lip-sync llegan después.

## Casos iniciales

### Reformas

- antes/después con narrativa;
- diario de obra;
- errores que encarecen una reforma;
- explicación de decisiones, materiales y presupuesto;
- variantes por estancia, barrio, objeción y presupuesto.

### Inmobiliaria

- recorrido narrado con fotos y clips reales;
- tres razones para visitar el inmueble;
- versión por perfil de comprador;
- versiones multidioma;
- pack de lanzamiento UGC como servicio adicional.

## Seguridad, ética y precisión

- No inventar testimonios ni suplantar a personas reales.
- Obtener consentimiento para voz, rostro y clonación de identidad.
- Identificar adecuadamente contenido sintético cuando corresponda.
- No alterar engañosamente dimensiones, vistas, ubicación, estado, acabados o características de un inmueble.
- Verificar precios, superficies, plazos, garantías y claims antes de publicar.
- Conservar procedencia de activos y trazabilidad de cada generación.

## Próxima sesión: orden de trabajo

1. Leer `README.md` y este documento.
2. Auditar el portátil y documentar GPU/VRAM, RAM, disco, CUDA, Python, Node y FFmpeg.
3. Proponer una arquitectura de repositorio y un plan de implementación por hitos.
4. Definir un proyecto de prueba real: una reforma y/o un inmueble con activos disponibles.
5. Construir primero un render vertical determinista con assets reales y datos de ejemplo.
6. Integrar después un único motor local de imagen/vídeo que encaje en la RTX 4070.
7. Comparar el mismo plano con una API externa antes de decidir compras de hardware.

No empezar instalando muchas interfaces o modelos. Primero debe existir una pieza completa, medible y reproducible de extremo a extremo.
