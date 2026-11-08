# Auditoría del portátil

Fecha: 2026-07-12 (Europe/Madrid)

Esta auditoría es de solo lectura. No se han instalado runtimes, dependencias ni modelos.

## Resumen ejecutivo

El MSI Katana 15 B12VGK es suficiente para desarrollar y renderizar el MVP determinista en local. La RTX 4070 Laptop dispone de 8 GB reales de VRAM y FFmpeg puede usar NVENC. El límite práctico para futuros modelos locales no será el almacenamiento, sino la combinación de 8 GB de VRAM y 16 GB de RAM.

Decisión para el MVP: usar CPU/GPU para composición y codificación con FFmpeg, mantener la generación visual detrás de interfaces y no instalar todavía CUDA Toolkit, ComfyUI ni pesos de modelos.

## Hardware

| Componente | Resultado | Implicación |
| --- | --- | --- |
| Equipo | MSI Katana 15 B12VGK | Portátil principal de desarrollo |
| Sistema | Windows 11 Pro 64-bit, build 26200 | Entorno nativo válido para FFmpeg y Python |
| CPU | Intel Core i7-12650H, 10 núcleos / 16 hilos | Suficiente para orquestación, análisis y composición |
| RAM | 16 GB DDR5-4800, 2 x 8 GB | Principal cuello de botella para IA local y multitarea |
| GPU | NVIDIA GeForce RTX 4070 Laptop GPU | Apta para inferencia ligera y aceleración de vídeo |
| VRAM real | 8188 MiB | Diseñar para modelos cuantizados o tareas pequeñas; evitar modelos pesados |
| Límite de potencia observado | 85 W en la primera consulta | Rendimiento inferior a variantes de mayor TGP; medir por tarea |
| Disco C | SSD Samsung 980 PRO 2 TB; 1377 GB libres | Espacio holgado para desarrollo y cachés locales excluidas |
| Disco D | SSD Micron 1 TB; 643 GB libres | El repositorio vive aquí; espacio suficiente para activos de prueba |

Durante la auditoría, la GPU marcó 75-79 °C con unos 8 W y poca carga. No bloquea el diseño, pero antes de cargas largas conviene comprobar ventilación, perfil de energía y temperatura sostenida.

## GPU y vídeo

- Controlador NVIDIA: 610.62.
- CUDA UMD anunciada por el controlador: 13.3.
- `nvcc`: no instalado; por tanto no hay CUDA Toolkit de desarrollo confirmado.
- FFmpeg detecta `cuda`, `d3d11va`, `d3d12va`, `qsv`, `opencl` y `vulkan`.
- FFmpeg incluye codificadores NVIDIA `h264_nvenc`, `hevc_nvenc` y `av1_nvenc`.

La versión CUDA indicada por `nvidia-smi` representa la compatibilidad máxima del controlador, no una instalación del Toolkit. El MVP no necesita `nvcc`: debe usar los binarios de FFmpeg existentes y, más adelante, una distribución de PyTorch que incluya sus runtimes compatibles.

## Toolchain disponible

| Herramienta | Estado |
| --- | --- |
| Python | 3.12.10 y 3.14.3 instalados |
| Node.js | 26.1.0 |
| npm | 11.13.0 |
| FFmpeg / FFprobe | Build GPL 2026-02-28, accesible en PATH |
| Git | 2.53.0 |
| WSL | 2.7.3; Ubuntu WSL2 disponible y detenido |
| Docker | No instalado |
| CUDA Toolkit (`nvcc`) | No instalado |

Para el MVP se recomienda fijar Python 3.12. Python 3.14 y Node 26 son demasiado recientes para asumir compatibilidad amplia con librerías audiovisuales o de IA. Node no es necesario para la primera pieza de extremo a extremo.

## Estado del repositorio

- Solo existían `AGENTS.md`, `CLAUDE.md` y `README.md` al iniciar la auditoría.
- La carpeta todavía no es un repositorio Git.
- La carpeta está gestionada por Syncthing (`.stfolder`).
- No existían `.gitignore` ni `.stignore`.

## Riesgos y recomendaciones

1. Mantener el MVP dentro de un único proceso Python y subprocesos FFmpeg; evitar servicios y contenedores prematuros.
2. No ejecutar simultáneamente un modelo local y un render pesado con solo 16 GB de RAM.
3. Considerar 32 GB de RAM antes de integrar generación local seria; no es requisito para el MVP determinista.
4. Medir siempre tiempo, pico de VRAM/RAM, tamaño de salida y errores por render.
5. Hacer una prueba corta de NVENC y temperatura antes del primer lote, no durante esta fase de arquitectura.
6. Mantener pesos, cachés, temporales, renders y entornos fuera de Syncthing mediante `.stignore`.

