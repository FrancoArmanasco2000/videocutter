# 12 — Packaging & Distribution

## Status
✅ Complete

## Files
- `build/app.spec` — PyInstaller spec (Mac + Windows)
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
PyInstaller copia el binario de ffmpeg del sistema de build al bundle.
`env.setup()` agrega `sys._MEIPASS` al PATH en runtime para que
`ffmpeg-python` lo encuentre sin cambios en el código de servicios.

## Mac — Gatekeeper
Sin code signing, Mac muestra "developer unidentified".
Solución para el amigo: clic derecho → Abrir (una sola vez).
Para distribución amplia: Apple Developer Program ($99/año) + notarización.

## YOLO model
No se bundlea — se descarga en `~/.config/Ultralytics/` en el primer uso.
El mensaje en la UI ya avisa al usuario.
