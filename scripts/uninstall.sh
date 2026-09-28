#!/usr/bin/env bash
# storage-report uninstaller
# Uso: ./scripts/uninstall.sh

set -euo pipefail

echo "Desinstalando storage-report..."

# 1. Detener y deshabilitar servicio systemd
echo "→ Deteniendo y deshabilitando servicio systemd..."
systemctl --user disable --now storage-report.service 2>/dev/null || true
rm -f /home/michael/.config/systemd/user/storage-report.service
systemctl --user daemon-reload

# 2. Desinstalar paquete Python
echo "→ Desinstalando paquete Python..."
pip uninstall -y storage-report 2>/dev/null || true

# 3. Eliminar archivos de instalación
echo "→ Eliminando archivos de instalación..."
rm -f /home/michael/.local/bin/storage-report-serve
rm -f /home/michael/.local/bin/storage-report-generate
rm -f /home/michael/.local/bin/storage-report-app.sh
rm -f /home/michael/.local/share/applications/storage-report.desktop
rm -f /home/michael/.local/share/icons/hicolor/48x48/apps/storage-report.png

# 5. Eliminar directorios de datos
rm -rf /home/michael/.local/share/storage-report
rm -rf /home/michael/.config/storage-report

# 6. Eliminar cache de pip
rm -rf /home/michael/.cache/pip/*storage-report* 2>/dev/null || true

echo "✓ Desinstalación completa."