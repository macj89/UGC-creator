# Backends generativos

## Arquitectura activa

UGC Studio es la capa de producto. ComfyUI conserva la ejecución técnica de grafos, modelos, VRAM, caché y outputs. OpenRouter sirve vídeo hero que no cabe con calidad suficiente en 8 GB de VRAM. ElevenLabs es el backend premium de voz mientras se compara con opciones locales.

```text
UGC Studio -> adapter por capacidad -> ComfyUI local -> Flux GGUF
                                \----> OpenRouter -> Kling / Veo
                                \----> ElevenLabs -> voz
```

No se modifica el código de ComfyUI. El servicio instalado en `<ruta-a-tu-ComfyUI>` se comparte mediante su API local en el puerto 8188.

## ComfyUI local

Configuración comprobada el 2026-07-12:

- ComfyUI 0.27.0;
- PyTorch 2.11 CUDA 12.8;
- RTX 4070 Laptop, 8 GB VRAM;
- `ComfyUI-GGUF`;
- `flux1-dev-Q4_K_S.gguf`;
- `t5-v1_1-xxl-encoder-Q5_K_M.gguf` y `clip_l.safetensors`;
- `ae.safetensors`.

UGC Studio genera un prompt API con loaders GGUF, conditioning Flux, sampler, VAE y `SaveImage`. Envía el grafo a `/prompt`, consulta `/history/{prompt_id}` y recupera la imagen mediante `/view`.

El test real produjo imágenes 384×576 y 512×768, y el flujo navegador -> UGC Studio -> ComfyUI -> RTX 4070 -> monitor terminó correctamente.

## OpenRouter

El adaptador utiliza la API asíncrona `/api/v1/videos` de OpenRouter. Consulta primero `/videos/models`, envía el keyframe como `first_frame`, sigue el trabajo mediante `/videos/{job_id}` y descarga el MP4 desde `/videos/{job_id}/content`. El coste devuelto en `usage.cost` forma parte del resultado. La clave nunca llega al navegador.

Para activarlo:

1. copiar `.env.example` como `.env`;
2. escribir `OPENROUTER_API_KEY=...`;
3. reiniciar con `start-studio.ps1`.

El `.env` local ya contiene las claves copiadas desde `UGC-content-manager`. Se han validado los endpoints de cuenta y catálogo sin lanzar todavía una generación facturable. El nodo de vídeo exige un keyframe local previo y muestra una confirmación con modelo, duración y resolución antes de enviar el trabajo. fal.ai queda fuera del flujo principal y solo se reconsiderará si hace falta un backend específico de lip-sync.

## ElevenLabs

El adaptador consulta las voces disponibles y genera audio con `eleven_multilingual_v2`. La lista de voces se valida sin sintetizar audio durante el diagnóstico, evitando consumo accidental.

## Arranque

```powershell
.\start-studio.ps1
```

El script reutiliza ComfyUI si ya está activo. Si no, lo inicia oculto desde `<ruta-a-tu-ComfyUI>` y abre UGC Studio en `http://127.0.0.1:8765`.
