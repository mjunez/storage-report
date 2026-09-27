# storage-report

Reporte visual de uso de disco con servidor web dinámico, auto-refresh y kiosk mode.

## Instalación rápida

### Opción A: Desde repositorio local (desarrollo)
```bash
git clone <ruta-a-storage-report>
cd storage-report
./scripts/install.sh
```

### Opción B: Remota (cuando esté publicado en GitHub)
```bash
curl -sSL https://raw.githubusercontent.com/<TU_USUARIO>/storage-report/main/scripts/install.sh | bash
```

> **Nota:** Reemplaza `<TU_USUARIO>` por tu usuario de GitHub al publicar.

## Qué instala el script

| Componente | Ubicación |
|---|---|
| Paquete Python (editable) | `~/.local/bin/storage-report-serve`, `storage-report-generate` |
| Servicio systemd (user) | `~/.config/systemd/user/storage-report.service` |
| Launcher kiosk | `~/.local/bin/storage-report-app.sh` |
| Entrada menú + icono | `~/.local/share/applications/storage-report.desktop`, `~/.local/share/icons/hicolor/48x48/apps/storage-report.png` |

## Uso

- Servicio: `systemctl --user status storage-report`
- App: **"Storage Report"** en el menú de aplicaciones
- URL directa: http://localhost:8888/storage_report.html

## Características

- **i18n dinámico** EN/ES con selector en header (persistente en localStorage)
- **Kiosk mode** multi-navegador: Chromium → Chrome → Brave → Edge → Firefox → xdg-open
- **Auto-refresh** cada 60s (fetch parcial, sin recargar página)
- **Splash screen** traducida, botón salir (X) + atajo Ctrl+Q
- **Tipografía Orbitron** embebida y servida automáticamente
- **Entry points** Python: `storage-report-serve` (servidor) y `storage-report-generate` (HTML estático)

## Requisitos

- Python 3.9+
- systemd (user services)
- Navegador compatible con kiosk: Chromium, Chrome, Brave, Edge, Firefox
