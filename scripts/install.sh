#!/usr/bin/env bash
set -euo pipefail

# storage-report installer
# Uso local:  ./scripts/install.sh
# Uso remoto: curl -sSL https://raw.githubusercontent.com/<user>/storage-report/main/scripts/install.sh | bash

REPO_URL="https://github.com/${GITHUB_USER:-michael}/storage-report.git"
INSTALL_DIR="$HOME/.local/share/storage-report"
BIN_DIR="$HOME/.local/bin"
SYSTEMD_DIR="$HOME/.config/systemd/user"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/48x48/apps"

# Detectar si corremos desde el repo clonado (local) o desde curl|bash (remoto)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

if [[ -f "$REPO_ROOT/pyproject.toml" && -d "$REPO_ROOT/storage_report" ]]; then
    # Modo local: ya estamos dentro del repo
    SOURCE_DIR="$REPO_ROOT"
    echo "Modo local detectado: $SOURCE_DIR"
else
    # Modo remoto: clonar repo
    SOURCE_DIR="$INSTALL_DIR"
    echo "Modo remoto: clonando repo a $INSTALL_DIR"
    rm -rf "$INSTALL_DIR"
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

echo "Instalando storage-report..."

# 1. Instalar paquete Python (entry points: storage-report-serve, storage-report-generate)
pip install --user -e "$SOURCE_DIR"

# 2. Instalar servicio systemd (usa entry point storage-report-serve)
mkdir -p "$SYSTEMD_DIR"
cp "$SOURCE_DIR/systemd/storage-report.service" "$SYSTEMD_DIR/"
systemctl --user daemon-reload
systemctl --user enable --now storage-report.service

# 3. Crear launcher app (kiosk mode)
cat > "$BIN_DIR/storage-report-app.sh" << 'EOF'
#!/usr/bin/env bash
# Storage Report App Launcher
# Opens the storage report web view in kiosk app mode

URL="http://localhost:8888/storage_report.html"
USER_DATA_DIR="$HOME/.config/storage-report"

mkdir -p "$USER_DATA_DIR"

# Priority order: chromium > google-chrome > brave > msedge > firefox > xdg-open
if command -v chromium >/dev/null 2>&1; then
    exec chromium --app="$URL" --class=storage-report --user-data-dir="$USER_DATA_DIR" --disable-features=TranslateUI,Translate --disable-translate --no-first-run --no-default-browser-check
elif command -v google-chrome >/dev/null 2>&1; then
    exec google-chrome --app="$URL" --class=storage-report --user-data-dir="$USER_DATA_DIR" --disable-features=TranslateUI,Translate --disable-translate --no-first-run --no-default-browser-check
elif command -v brave-browser >/dev/null 2>&1; then
    exec brave-browser --app="$URL" --class=storage-report --user-data-dir="$USER_DATA_DIR" --disable-features=TranslateUI,Translate --disable-translate --no-first-run --no-default-browser-check
elif command -v brave >/dev/null 2>&1; then
    exec brave --app="$URL" --class=storage-report --user-data-dir="$USER_DATA_DIR" --disable-features=TranslateUI,Translate --disable-translate --no-first-run --no-default-browser-check
elif command -v msedge >/dev/null 2>&1; then
    exec msedge --app="$URL" --class=storage-report --user-data-dir="$USER_DATA_DIR" --disable-features=TranslateUI,Translate --disable-translate --no-first-run --no-default-browser-check
elif command -v microsoft-edge >/dev/null 2>&1; then
    exec microsoft-edge --app="$URL" --class=storage-report --user-data-dir="$USER_DATA_DIR" --disable-features=TranslateUI,Translate --disable-translate --no-first-run --no-default-browser-check
elif command -v firefox >/dev/null 2>&1; then
    # Firefox uses --kiosk for fullscreen kiosk mode (no --app equivalent)
    exec firefox --kiosk "$URL" --class=storage-report --profile "$USER_DATA_DIR/firefox-profile" --no-remote
else
    xdg-open "$URL" >/dev/null 2>&1
fi
EOF
chmod +x "$BIN_DIR/storage-report-app.sh"

# 4. Instalar icono y desktop entry
mkdir -p "$ICON_DIR"
cp "$SOURCE_DIR/storage_report/static/assets/hdd.png" "$ICON_DIR/storage-report.png"

cat > "$DESKTOP_DIR/storage-report.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Storage Report
Comment=Reporte de almacenamiento local
Exec=$BIN_DIR/storage-report-app.sh
Icon=storage-report
Terminal=false
Categories=System;Utility;
StartupWMClass=storage-report
EOF

update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo "Instalación completa."
echo "  Servicio: systemctl --user status storage-report"
echo "  App: 'Storage Report' en el menú de aplicaciones"
echo "  URL: http://localhost:8888/storage_report.html"
