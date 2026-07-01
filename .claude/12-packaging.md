# 12 — Packaging & Distribution

## Status
✅ Complete

## Files
- `build/app.spec` — PyInstaller spec (Mac + Windows + Linux)
- `.github/workflows/release.yml` — CI/CD automático
- `src/utils/env.py` — agrega el ffmpeg bundleado al PATH en runtime
- `src/main.py` — llama a env.setup() antes de cualquier import

## Flujo de release

```
git tag v1.0.0
git push origin v1.0.0
       ↓
GitHub Actions dispara automáticamente
       ↓
  mac-latest    →  VideoCutter.app     →  VideoCutter-mac.zip
  win-latest    →  VideoCutter.exe     →  VideoCutter-windows.zip
  ubuntu-latest →  VideoCutter (bin)   →  VideoCutter-linux.tar.gz
       ↓
GitHub Release creado con los tres archivos adjuntos
```

## Cómo hacer un release
```bash
git tag v1.0.0
git push origin v1.0.0
```
Listo. En ~10 minutos el Release aparece en GitHub con los tres instaladores.

## Linux — torch CPU-only
`ultralytics` depende de `torch`. En Linux, `pip install torch` sin más
trae por defecto la build con CUDA, que arrastra paquetes `nvidia-cuda-*`
separados (varios GB en total). PyInstaller los empaqueta igual y el
tar.gz termina superando los 2GB que GitHub permite por asset de release
(falló en el release de `v1.0.0`, error "size must be less than 2147483648").

Fix en `release.yml`, job `build-linux`: instalar torch/torchvision
CPU-only antes del resto de requirements:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt pyinstaller
```
Mac y Windows no tienen este problema (sus wheels de torch ya vienen
compactos), así que solo se aplica en el job de Linux.

## Bundling de ffmpeg
PyInstaller copia el binario de ffmpeg del sistema de build al bundle,
dentro de una subcarpeta `bin/`. `env.setup()` agrega esa subcarpeta
(`sys._MEIPASS/bin`) al PATH en runtime para que `ffmpeg-python` lo
encuentre sin cambios en el código de servicios.

⚠️ El binario va en `bin/` y NO en la raíz del bundle (`binaries=[(ffmpeg_bin, ".")]`)
porque el nombre del ejecutable (`ffmpeg`, sin extensión en Mac/Linux) choca
con el nombre del paquete Python `ffmpeg-python` (carpeta `ffmpeg/` con
`__init__.py`, `nodes.py`, etc.) que PyInstaller también extrae en la raíz.
Un archivo y una carpeta con el mismo nombre en el mismo lugar se pisan,
dejando el paquete `ffmpeg-python` corrupto → `ImportError: cannot import
name 'nodes' from partially initialized module 'ffmpeg' (most likely due
to a circular import)` al abrir la app (crashea apenas arranca, sin mostrar
ventana porque `console=False`). Pasó en Mac (`v1.0.0`); Windows se salvaba
porque el binario se llama `ffmpeg.exe`, no `ffmpeg`, así que no chocaba —
pero Linux tiene el mismo riesgo que Mac (binario sin extensión).

## Tracking — lapx
`ultralytics` usa `bytetrack` para el "Track IDs", que a su vez necesita el
paquete `lap` (o su fork `lapx`, que sí tiene wheels para Python 3.11).
Sin bundlear, `ultralytics` intenta instalarlo solo en tiempo de ejecución
(AutoUpdate vía `pip install`) — eso funciona corriendo desde código fuente
con `pip` a mano, pero en el `.exe`/`.app` empaquetado no hay `pip` ni forma
de instalar nada: tracking rompería para el usuario final la primera vez
que lo use. Por eso `lapx==0.9.4` está en `requirements.txt` y `lap` +
`collect_submodules("lap")` en `app.spec` — así viaja bundleado y
`AutoUpdate` nunca se dispara.

## Mac — Gatekeeper
Sin code signing, Mac muestra "developer unidentified".
Solución para el amigo: clic derecho → Abrir (una sola vez).
Para distribución amplia: Apple Developer Program ($99/año) + notarización.

## YOLO model
No se bundlea — se descarga en `~/.config/Ultralytics/` en el primer uso.
El mensaje en la UI ya avisa al usuario.
