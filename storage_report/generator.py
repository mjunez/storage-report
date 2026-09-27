#!/usr/bin/env python3
"""
Genera reporte visual completo de uso de disco (tema Hermes 2FA) con datos actualizados
"""
import subprocess
import os
import json
from pathlib import Path
from datetime import datetime
import base64

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return ""

USER_HOME = os.path.expanduser('~')
USER_NAME = os.getenv('USER') or os.getenv('USERNAME') or 'user'

def get_distro_name():
    try:
        with open('/etc/os-release') as f:
            data = {}
            for line in f:
                if '=' in line:
                    k,v = line.strip().split('=',1)
                    data[k]=v.strip('"')
            pretty = data.get('PRETTY_NAME')
            if pretty:
                return pretty
    except:
        pass
    return 'Linux'

def get_disk_info():
    return run_cmd("df -h / /home /boot 2>/dev/null")

def parse_disk_usage(df_output, mountpoint):
    for line in df_output.split('\n'):
        if line.strip().endswith(mountpoint):
            parts = line.split()
            if len(parts) >= 5:
                return {
                    'total': parts[1],
                    'used': parts[2],
                    'avail': parts[3],
                    'use_pct': parts[4]
                }
    return {'total': 'N/A', 'used': 'N/A', 'avail': 'N/A', 'use_pct': 'N/A'}

def get_home_usage():
    out = run_cmd(f"du -sh {USER_HOME} 2>/dev/null")
    return out.split('\\t')[0] if out else "N/A"

def get_dir_sizes(path, limit=10):
    out = run_cmd(f"du -sh {path}/* 2>/dev/null | sort -hr | head -{limit}")
    return out

def get_top_files(path, limit=15):
    out = run_cmd(f"find {path} -type f -exec du -h {{}} + 2>/dev/null | sort -hr | head -{limit}")
    return out

def get_icon_base64():
    """Lee el icono y lo convierte a base64"""
    import importlib.resources as ir
    try:
        # Intenta icono embebido en el paquete
        try:
            data = ir.files('storage_report.static.assets').joinpath('hdd.png').read_bytes()
            return base64.b64encode(data).decode()
        except Exception:
            pass
        # Fallback a Pictures del usuario
        icon_path = Path(USER_HOME) / "Pictures" / "hdd.png"
        if icon_path.exists():
            with open(icon_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return ""

def generate_html():
    # Diccionario de traducciones
    TR = {
        'en': {
            'title': 'Storage Report',
            'subtitle_prefix': 'Analyzed: ',
            'main_disk': 'Main Disk (/)',
            'home_user': "Home ({user})",
            'total': 'Total',
            'used': 'Used',
            'available': 'Available',
            'boot': 'Boot',
            'critical_spaces': 'Critical Spaces',
            'top_dirs': 'Top Directories in {home}',
            'largest_files': 'Largest Files in {home}',
            'size': 'Size',
            'location': 'Location',
            'workspace': 'Workspace ({home}/workspace)',
            'local_share': '~/.local/share - Top directories',
            'system_dirs': 'System - Top directories',
            'directory': 'Directory',
            'warning_title': 'Warning:',
            'warning_boot': '/boot is at {pct} ({used} / {total}). Consider cleaning old kernels.',
            'tips_title': 'Recommendations:',
            'tip1': 'Clean ~/.local/share/Trash (check for large files in trash)',
            'tip2': 'Check ~/nvidia-all (old .run and .pkg files)',
            'tip3': 'Clean yay cache: ~/.cache/yay/',
            'tip4': 'Consider moving large ISOs to external storage',
            'footer': 'Powered by mjunez - Copyright 2026',
            'exit': 'X',
            'lang_en': 'EN',
            'lang_es': 'ESP',
            'splash_loading': 'Loading...',
            'header_subtitle': '{distro} - Analyzed: {timestamp}',
        },
        'es': {
            'title': 'Reporte de Almacenamiento',
            'subtitle_prefix': 'Analizado: ',
            'main_disk': 'Disco Principal (/)',
            'home_user': 'Home ({user})',
            'total': 'Total',
            'used': 'Usado',
            'available': 'Disponible',
            'boot': 'Boot',
            'critical_spaces': 'Espacios Criticos',
            'top_dirs': 'Top Directorios en {home}',
            'largest_files': 'Archivos Mas Grandes en {home}',
            'size': 'Tamano',
            'location': 'Ubicacion',
            'workspace': 'Workspace ({home}/workspace)',
            'local_share': '~/.local/share - Top directorios',
            'system_dirs': 'Sistema - Top directorios',
            'directory': 'Directorio',
            'warning_title': 'Atencion:',
            'warning_boot': '/boot esta al {pct} ({used} / {total}). Considera limpiar kernels antiguos.',
            'tips_title': 'Recomendaciones:',
            'tip1': 'Limpia ~/.local/share/Trash (revisa archivos grandes en papelera)',
            'tip2': 'Revisa ~/nvidia-all (archivos .run y .pkg antiguos)',
            'tip3': 'Limpia cache de yay: ~/.cache/yay/',
            'tip4': 'Considera mover ISOs grandes a almacenamiento externo',
            'footer': 'Powered by mjunez - Copyright 2026',
            'exit': 'X',
            'lang_en': 'EN',
            'lang_es': 'ESP',
            'splash_loading': 'Cargando...',
            'header_subtitle': '{distro} - Analizado: {timestamp}',
        }
    }
    
    df_output = get_disk_info()
    root_disk = parse_disk_usage(df_output, '/')
    home_disk = parse_disk_usage(df_output, '/home')
    boot_disk = parse_disk_usage(df_output, '/boot')
    
    home_total = get_home_usage()
    
    home_dirs = get_dir_sizes(USER_HOME, 15)
    top_files = get_top_files(USER_HOME, 15)
    workspace_dirs = get_dir_sizes(os.path.join(USER_HOME,'workspace'), 10)
    local_share = get_dir_sizes(os.path.join(USER_HOME,'.local/share'), 15)
    usr_dirs = get_dir_sizes('/usr', 10)
    var_dirs = get_dir_sizes('/var', 10)
    
    # Obtener tamaños específicos para espacios críticos
    var_size = run_cmd("du -sh /var 2>/dev/null | cut -f1")
    flatpak_size = run_cmd("du -sh /var/lib/flatpak 2>/dev/null | cut -f1")
    steam_size = run_cmd("du -sh /usr/share/steam 2>/dev/null | cut -f1")
    
    date_str = datetime.now().strftime('%d %b %Y')
    timestamp_str = datetime.now().strftime('%d %b %Y %H:%M')
    
    # Procesar top files para tabla HTML
    top_files_rows = ""
    for line in top_files.strip().split('\n'):
        if line.strip():
            parts = line.split('\t', 1)
            if len(parts) == 2:
                size, path = parts
                top_files_rows += f'            <tr><td class="size">{size}</td><td class="path">{path}</td></tr>\n'
    
    # Procesar system dirs para tabla
    system_rows = ""
    for line in (usr_dirs + '\n' + var_dirs).strip().split('\n'):
        if line.strip():
            parts = line.split('\t', 1)
            if len(parts) == 2:
                size, path = parts
                system_rows += f'            <tr><td class="path">{path}</td><td class="size">{size}</td></tr>\n'
    
    # Icono base64
    icon_b64 = get_icon_base64()
    icon_html = f'<img src="data:image/png;base64,{icon_b64}" class="title-icon" alt="HDD" style="width:32px;height:32px;vertical-align:middle;margin-right:0.75rem;border:2px solid var(--accent);border-radius:4px;">' if icon_b64 else ''
    
    # Copiar fuente Orbitron a /tmp para que el servidor la sirva
    font_dest_dir = Path("/tmp/storage-report-fonts")
    font_dest_dir.mkdir(parents=True, exist_ok=True)
    font_src = Path(__file__).parent / "static" / "fonts" / "Orbitron-VariableFont_wght.ttf"
    font_dest = font_dest_dir / "Orbitron-VariableFont_wght.ttf"
    try:
        if font_src.exists():
            font_dest.write_bytes(font_src.read_bytes())
    except Exception:
        pass
    
    # Función helper para traducciones
    def tr(key, lang='en'):
        return TR.get(lang, TR['en']).get(key, key)
    
    # Build HTML using list of strings to avoid formatting conflicts
    html = []
    html.append('<!DOCTYPE html>')
    html.append('<html lang="en">')
    html.append('<head>')
    html.append('<meta charset="UTF-8">')
    html.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html.append(f'<title>{tr("title", "en")}</title>')
    html.append('<style>')
    html.append('    :root {')
    html.append('        --bg: #0f1117;')
    html.append('        --card: #181b24;')
    html.append('        --card-2: #1f2330;')
    html.append('        --border: #2a2f3d;')
    html.append('        --text: #e6e9ef;')
    html.append('        --muted: #8b92a5;')
    html.append('        --accent: #5b8cff;')
    html.append('        --accent-2: #3a6bff;')
    html.append('        --ok: #36d39a;')
    html.append('        --fail: #ff6b6b;')
    html.append('        --term-bg: #0b0e14;')
    html.append('        --term-glow: #4ef0a3;')
    html.append('    }')
    html.append('    @font-face {')
    html.append('        font-family: "Orbitron";')
    html.append('        src: url("/storage-report-fonts/Orbitron-VariableFont_wght.ttf") format("truetype");')
    html.append('        font-weight: 400 900;')
    html.append('        font-display: swap;')
    html.append('    }')
    html.append('    * { box-sizing: border-box; margin: 0; padding: 0; }')
    html.append('    body {')
    html.append('        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, system-ui, sans-serif;')
    html.append('        background: radial-gradient(1200px 600px at 50% -10%, #1a2030 0%, var(--bg) 60%);')
    html.append('        color: var(--text);')
    html.append('        min-height: 100vh;')
    html.append('        margin: 0;')
    html.append('        padding: 2rem 1rem;')
    html.append('    }')
    html.append('    .container { max-width: 1400px; margin: 0 auto; }')
    html.append('    h1 {')
    html.append('        font-size: 2.2em;')
    html.append('        margin-bottom: 10px;')
    html.append('        background: linear-gradient(135deg, var(--accent), var(--accent-2));')
    html.append('        -webkit-background-clip: text;')
    html.append('        -webkit-text-fill-color: transparent;')
    html.append('        background-clip: text;')
    html.append('        display: flex;')
    html.append('        align-items: center;')
    html.append('        gap: 0.75rem;')
    html.append('        font-family: "Orbitron", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, system-ui, sans-serif;')
    html.append('        font-weight: 700;')
    html.append('    }')
    html.append('    .title-icon { border:2px solid var(--accent); border-radius:4px; }')
    html.append('    .subtitle { color: var(--muted); margin-bottom: 30px; font-size: 1rem; }')
    html.append('    .header { position: sticky; top: 0; left: 0; right: 0; background: var(--bg); padding: 1rem 2rem 1.5rem; z-index: 10; backdrop-filter: blur(6px); }')
    html.append('    .splash { position: fixed; inset: 0; background: var(--bg); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }')
    html.append('    .splash .splash-icon { width: 64px; height: 64px; border: 2px solid var(--accent); border-radius: 9px; margin-bottom: 1rem; display: flex; align-items: center; justify-content: center; }')
    html.append('    .splash .splash-text { font-family: "Orbitron", sans-serif; font-weight: 600; color: var(--muted); letter-spacing: 0.5px; }')
    html.append('    .grid {')
    html.append('        display: grid;')
    html.append('        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));')
    html.append('        gap: 2.5rem;')
    html.append('        margin-top: 2rem;')
    html.append('        margin-bottom: 2rem;')
    html.append('    }')
    html.append('    .card {')
    html.append('        background: var(--card);')
    html.append('        border: 1px solid var(--border);')
    html.append('        border-radius: 16px;')
    html.append('        padding: 1.5rem;')
    html.append('        box-shadow: 0 20px 60px rgba(0,0,0,0.45);')
    html.append('        transition: transform 0.2s, box-shadow 0.2s;')
    html.append('        margin-bottom: 2.5rem;')
    html.append('    }')
    html.append('    .card:hover { transform: translateY(-2px); box-shadow: 0 0 0 1px var(--accent), 0 0 0 4px rgba(91,140,255,0.12); }')
    html.append('    .card h2 {')
    html.append('        font-size: 1.15rem;')
    html.append('        margin: 0 0 1rem;')
    html.append('        color: var(--accent);')
    html.append('        letter-spacing: 0.2px;')
    html.append('        font-family: "Orbitron", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, system-ui, sans-serif;')
    html.append('        font-weight: 600;')
    html.append('    }')
    html.append('    .stat {')
    html.append('        display: flex;')
    html.append('        justify-content: space-between;')
    html.append('        padding: 0.75rem 0;')
    html.append('        border-bottom: 1px solid var(--border);')
    html.append('    }')
    html.append('    .stat:last-child { border-bottom: none; }')
    html.append('    .stat-name { color: var(--muted); font-size: 0.85rem; }')
    html.append('    .stat-value { font-weight: 600; color: var(--text); font-size: 0.95rem; }')
    html.append('    .progress-bar {')
    html.append('        width: 100%;')
    html.append('        height: 8px;')
    html.append('        background: var(--term-bg);')
    html.append('        border-radius: 9px;')
    html.append('        overflow: hidden;')
    html.append('        margin-top: 0.75rem;')
    html.append('    }')
    html.append('    .progress-fill {')
    html.append('        height: 100%;')
    html.append('        background: linear-gradient(180deg, var(--accent) 0%, var(--accent-2) 100%);')
    html.append('        border-radius: 9px;')
    html.append('        transition: width 0.5s ease;')
    html.append('    }')
    html.append('    .badge {')
    html.append('        display: inline-block;')
    html.append('        padding: 0.35rem 0.75rem;')
    html.append('        border-radius: 9px;')
    html.append('        font-size: 0.8rem;')
    html.append('        font-weight: 600;')
    html.append('        margin: 0.2rem;')
    html.append('    }')
    html.append('    .badge-danger { background: rgba(255,107,107,0.18); color: var(--fail); border: 1px solid var(--fail); }')
    html.append('    .badge-warning { background: rgba(255,180,50,0.18); color: #ffb432; border: 1px solid #ffb432; }')
    html.append('    .badge-success { background: rgba(54,211,154,0.18); color: var(--ok); border: 1px solid var(--ok); }')
    html.append('    .badge-info { background: rgba(91,140,255,0.18); color: var(--accent); border: 1px solid var(--accent); }')
    html.append('    table {')
    html.append('        width: 100%;')
    html.append('        border-collapse: collapse;')
    html.append('        margin-top: 1rem;')
    html.append('    }')
    html.append('    th, td {')
    html.append('        padding: 0.75rem;')
    html.append('        text-align: left;')
    html.append('        border-bottom: 1px solid var(--border);')
    html.append('    }')
    html.append('    th {')
    html.append('        color: var(--accent);')
    html.append('        font-size: 0.82rem;')
    html.append('        text-transform: uppercase;')
    html.append('        letter-spacing: 0.6px;')
    html.append('        font-weight: 600;')
    html.append('    }')
    html.append('    tr:hover { background: var(--card-2); }')
    html.append('    .size { font-family: monospace; color: var(--text); font-size: 0.9rem; }')
    html.append('    .path { color: var(--muted); font-size: 0.85rem; }')
    html.append('    .warning-box {')
    html.append('        background: var(--card-2);')
    html.append('        border: 1px solid var(--fail);')
    html.append('        border-radius: 12px;')
    html.append('        padding: 1rem;')
    html.append('        margin: 1.5rem 0;')
    html.append('    }')
    html.append('    .warning-box strong { color: var(--fail); }')
    html.append('    .tip-box {')
    html.append('        background: var(--card-2);')
    html.append('        border: 1px solid var(--ok);')
    html.append('        border-radius: 12px;')
    html.append('        padding: 1rem;')
    html.append('        margin: 1.5rem 0;')
    html.append('    }')
    html.append('    .tip-box strong { color: var(--ok); }')
    html.append('    pre {')
    html.append('        background: var(--term-bg);')
    html.append('        padding: 1rem;')
    html.append('        border-radius: 12px;')
    html.append('        overflow-x: auto;')
    html.append('        font-size: 0.85rem;')
    html.append('        border: 1px solid var(--border);')
    html.append('        font-family: "JetBrains Mono", "Fira Code", monospace;')
    html.append('    }')
    html.append('    .step {')
    html.append('        background: var(--card-2);')
    html.append('        border: 1px solid var(--border);')
    html.append('        border-radius: 12px;')
    html.append('        padding: 1rem;')
    html.append('        margin-bottom: 0.9rem;')
    html.append('    }')
    html.append('    .step legend, .step .legend {')
    html.append('        font-weight: 600;')
    html.append('        font-size: 0.82rem;')
    html.append('        color: var(--muted);')
    html.append('        text-transform: uppercase;')
    html.append('        letter-spacing: 0.6px;')
    html.append('        margin-bottom: 0.6rem;')
    html.append('        display: block;')
    html.append('    }')
    html.append('    button {')
    html.append('        width: 100%;')
    html.append('        padding: 0.7rem 1rem;')
    html.append('        background: linear-gradient(180deg, var(--accent) 0%, var(--accent-2) 100%);')
    html.append('        color: white;')
    html.append('        border: none;')
    html.append('        border-radius: 9px;')
    html.append('        font-size: 0.92rem;')
    html.append('        font-weight: 600;')
    html.append('        cursor: pointer;')
    html.append('        transition: transform 0.05s ease, filter 0.15s ease;')
    html.append('    }')
    html.append('    button:hover { filter: brightness(1.08); }')
    html.append('    button:active { transform: translateY(1px); }')
    html.append('    input:disabled, button:disabled, .step.disabled { opacity: 0.45; cursor: not-allowed; }')
    html.append('    .step.active { box-shadow: 0 0 0 1px var(--accent), 0 0 0 4px rgba(91,140,255,0.12); }')
    html.append('    .step legend, .step .legend { font-weight: 600; font-size: 0.82rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 0.6rem; display: block; }')
    html.append('</style>')
    # Embeber datos i18n como JSON para uso en cliente
    html.append('<script type="application/json" id="i18n-data">' + json.dumps(TR, ensure_ascii=False) + '</script>')
    html.append('</head>')
    html.append('<body>')
    html.append('    <div class="splash" id="splash">')
    html.append('        <div class="splash-icon"><img src="data:image/png;base64,' + (icon_b64 if icon_b64 else '') + '" style="width:32px;height:32px;"></div>')
    html.append('        <div class="splash-text" data-i18n="splash_loading">Cargando...</div>')
    html.append('    </div>')
    html.append('<div class="container">')
    html.append('    <div class="header">')
    html.append('    <h1 data-i18n="title">' + icon_html + 'Reporte de Almacenamiento</h1>')
    html.append('    <p class="subtitle" data-i18n-html="header_subtitle" data-distro="' + get_distro_name() + '" data-timestamp="' + timestamp_str + '">' + get_distro_name() + ' - Analizado: ' + timestamp_str + '</p>')
    html.append('    </div>')
    
    # Resumen General
    html.append('    <div class="grid">')
    html.append('        <div class="card">')
    html.append('            <h2 data-i18n="main_disk">Disco Principal (/)</h2>')
    html.append('            <div class="stat">')
    html.append('                <span class="stat-name" data-i18n="total">Total</span>')
    html.append('                <span class="stat-value">' + root_disk['total'] + '</span>')
    html.append('            </div>')
    html.append('            <div class="stat">')
    html.append('                <span class="stat-name" data-i18n="used">Usado</span>')
    html.append('                <span class="stat-value">' + root_disk['used'] + ' (' + root_disk['use_pct'] + ')</span>')
    html.append('            </div>')
    html.append('            <div class="stat">')
    html.append('                <span class="stat-name" data-i18n="available">Disponible</span>')
    html.append('                <span class="stat-value">' + root_disk['avail'] + '</span>')
    html.append('            </div>')
    html.append('            <div class="progress-bar">')
    html.append('                <div class="progress-fill" style="width: ' + root_disk['use_pct'] + '"></div>')
    html.append('            </div>')
    html.append('        </div>')
    
    html.append('        <div class="card">')
    html.append('            <h2 data-i18n-html="home_user" data-user="' + USER_NAME + '">Home (' + USER_NAME + ')</h2>')
    html.append('            <div class="stat">')
    html.append('                <span class="stat-name" data-i18n="total">Total usado</span>')
    html.append('                <span class="stat-value">' + home_total + '</span>')
    html.append('            </div>')
    html.append('            <div class="stat">')
    html.append('                <span class="stat-name" data-i18n="used">Home partition</span>')
    html.append('                <span class="stat-value">' + home_disk['used'] + ' (' + home_disk['use_pct'] + ')</span>')
    html.append('            </div>')
    html.append('            <div class="stat">')
    html.append('                <span class="stat-name" data-i18n="available">Disponible en /home</span>')
    html.append('                <span class="stat-value">' + home_disk['avail'] + '</span>')
    html.append('            </div>')
    html.append('            <div class="stat">')
    html.append('                <span class="stat-name" data-i18n="boot">Boot</span>')
    html.append('                <span class="stat-value">' + boot_disk['used'] + ' (' + boot_disk['use_pct'] + ')</span>')
    html.append('            </div>')
    html.append('        </div>')
    
    html.append('        <div class="card">')
    html.append('            <h2 data-i18n="critical_spaces">Espacios Criticos</h2>')
    html.append('            <span class="badge badge-danger" data-i18n-attr="title" data-title="/boot">/boot: ' + boot_disk['use_pct'] + '</span>')
    html.append('            <span class="badge badge-warning" data-i18n-attr="title" data-title="/var">/var: ' + (var_size if var_size else 'N/A') + '</span>')
    html.append('            <span class="badge badge-info" data-i18n-attr="title" data-title="Flatpak">Flatpak: ' + (flatpak_size if flatpak_size else 'N/A') + '</span>')
    html.append('            <span class="badge badge-info" data-i18n-attr="title" data-title="Steam">Steam: ' + (steam_size if steam_size else 'N/A') + '</span>')
    html.append('        </div>')
    html.append('    </div>')
    
    html.append('    <div class="card">')
    html.append('        <h2 data-i18n-html="top_dirs" data-home="' + USER_HOME + '">Top Directorios en ' + USER_HOME + '</h2>')
    html.append('        <pre>' + (home_dirs if home_dirs else 'No data') + '</pre>')
    html.append('    </div>')
    
    html.append('    <div class="card">')
    html.append('        <h2 data-i18n-html="largest_files" data-home="' + USER_HOME + '">Archivos Mas Grandes en ' + USER_HOME + '</h2>')
    html.append('        <table>')
    html.append('            <tr><th data-i18n="size">Tamano</th><th data-i18n="location">Ubicacion</th></tr>')
    html.append(top_files_rows)
    html.append('        </table>')
    html.append('    </div>')
    
    html.append('    <div class="card">')
    html.append('        <h2 data-i18n-html="workspace" data-home="' + USER_HOME + '">Workspace (' + USER_HOME + '/workspace)</h2>')
    html.append('        <pre>' + (workspace_dirs if workspace_dirs else 'No data') + '</pre>')
    html.append('    </div>')
    
    html.append('    <div class="card">')
    html.append('        <h2 data-i18n="local_share">~/.local/share - Top directorios</h2>')
    html.append('        <pre>' + (local_share if local_share else 'No data') + '</pre>')
    html.append('    </div>')
    
    html.append('    <div class="card">')
    html.append('        <h2 data-i18n="system_dirs">Sistema - Top directorios</h2>')
    html.append('        <table>')
    html.append('            <tr><th data-i18n="directory">Directorio</th><th data-i18n="size">Tamano</th></tr>')
    html.append(system_rows)
    html.append('        </table>')
    html.append('    </div>')
    
    html.append('    <div class="warning-box">')
    html.append('        <strong data-i18n="warning_title">Atencion:</strong> <span data-i18n-html="warning_boot" data-pct="' + boot_disk['use_pct'] + '" data-used="' + boot_disk['used'] + '" data-total="' + boot_disk['total'] + '">/boot esta al ' + boot_disk['use_pct'] + ' (' + boot_disk['used'] + ' / ' + boot_disk['total'] + '). Considera limpiar kernels antiguos.</span>')
    html.append('    </div>')
    
    html.append('    <div class="tip-box">')
    html.append('        <strong data-i18n="tips_title">Recomendaciones:</strong>')
    html.append('        <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">')
    html.append('            <li data-i18n="tip1">Limpia ~/.local/share/Trash (revisa archivos grandes en papelera)</li>')
    html.append('            <li data-i18n="tip2">Revisa ~/nvidia-all (archivos .run y .pkg antiguos)</li>')
    html.append('            <li data-i18n="tip3">Limpia cache de yay: ~/.cache/yay/</li>')
    html.append('            <li data-i18n="tip4">Considera mover ISOs grandes a almacenamiento externo</li>')
    html.append('        </ul>')
    html.append('    </div>')
    
    html.append('    <p style="text-align:center; color:var(--muted); margin-top:2rem; font-size:0.85rem;" data-i18n="footer">')
    html.append('        Powered by mjunez - Copyright 2026')
    html.append('    </p>')
    html.append('</div>')
    html.append('    <div class="lang-switch" role="group" aria-label="Idioma" style="position:fixed;top:12px;right:56px;z-index:9999;display:flex;gap:0.35rem;">')
    html.append('        <button data-lang="en" aria-label="English" style="width:auto;padding:0.35rem 0.75rem;font-size:0.7rem;font-weight:700;background:transparent;color:var(--muted);border:1px solid var(--border);border-radius:6px;cursor:pointer;">EN</button>')
    html.append('        <button data-lang="es" aria-label="Español" style="width:auto;padding:0.35rem 0.75rem;font-size:0.7rem;font-weight:700;background:transparent;color:var(--muted);border:1px solid var(--border);border-radius:6px;cursor:pointer;">ESP</button>')
    html.append('    </div>')
    html.append('    <button id="exitBtn" style="position:fixed;top:12px;right:12px;z-index:9999;width:36px;height:36px;padding:0;line-height:36px;text-align:center;border-radius:9px;border:1px solid var(--fail);background:rgba(255,107,107,0.18);color:var(--fail);cursor:pointer;">X</button>')
    html.append('    <script>')
    html.append('// i18n Engine')
    html.append('(function(){')
    html.append('  const TR = JSON.parse(document.getElementById("i18n-data").textContent);')
    html.append('  let currentLang = localStorage.getItem("storage-report-lang") || "es";')
    html.append('  ')
    html.append('  function interpolate(template, data) {')
    html.append('    return template.replace(/\{(\w+)\}/g, (_, key) => data[key] || "{" + key + "}");')
    html.append('  }')
    html.append('  ')
    html.append('  function applyI18n(root = document) {')
    html.append('    const t = TR[currentLang] || TR.en;')
    html.append('    document.documentElement.lang = currentLang;')
    html.append('    document.title = t.title;')
    html.append('    ')
    html.append('    // Text content')
    html.append('    root.querySelectorAll("[data-i18n]").forEach(el => {')
    html.append('      const key = el.getAttribute("data-i18n");')
    html.append('      if (t[key]) el.textContent = t[key];')
    html.append('    });')
    html.append('    ')
    html.append('    // HTML content with interpolation')
    html.append('    root.querySelectorAll("[data-i18n-html]").forEach(el => {')
    html.append('      const key = el.getAttribute("data-i18n-html");')
    html.append('      if (t[key]) {')
    html.append('        const data = {};')
    html.append('        for (const attr of el.attributes) {')
    html.append('          if (attr.name.startsWith("data-") && attr.name !== "data-i18n-html") {')
    html.append('            data[attr.name.slice(5)] = attr.value;')
    html.append('          }')
    html.append('        }')
    html.append('        el.innerHTML = interpolate(t[key], data);')
    html.append('      }')
    html.append('    });')
    html.append('    ')
    html.append('    // Attribute interpolation (e.g., title)')
    html.append('    root.querySelectorAll("[data-i18n-attr]").forEach(el => {')
    html.append('      const key = el.getAttribute("data-i18n-attr");')
    html.append('      if (t[key]) {')
    html.append('        const data = {};')
    html.append('        for (const attr of el.attributes) {')
    html.append('          if (attr.name.startsWith("data-") && attr.name !== "data-i18n-attr") {')
    html.append('            data[attr.name.slice(5)] = attr.value;')
    html.append('          }')
    html.append('        }')
    html.append('        Object.entries(data).forEach(([attrName, val]) => {')
    html.append('          el.setAttribute(attrName, interpolate(t[key], {[attrName]: val}));')
    html.append('        });')
    html.append('      }')
    html.append('    });')
    html.append('    ')
    html.append('    // Language switcher buttons')
    html.append('    document.querySelectorAll(".lang-switch button").forEach(btn => {')
    html.append('      btn.classList.toggle("active", btn.dataset.lang === currentLang);')
    html.append('    });')
    html.append('  }')
    html.append('  ')
    html.append('  function setLang(lang) {')
    html.append('    if (TR[lang]) {')
    html.append('      currentLang = lang;')
    html.append('      localStorage.setItem("storage-report-lang", lang);')
    html.append('      applyI18n();')
    html.append('    }')
    html.append('  }')
    html.append('  ')
    html.append('  // Language switcher click handlers')
    html.append('  document.addEventListener("click", e => {')
    html.append('    const btn = e.target.closest(".lang-switch button[data-lang]");')
    html.append('    if (btn) setLang(btn.dataset.lang);')
    html.append('  });')
    html.append('  ')
    html.append('  // Expose for refresh')
    html.append('  window.applyI18n = applyI18n;')
    html.append('  window.setLang = setLang;')
    html.append('  ')
    html.append('  // Initial apply')
    html.append('  document.addEventListener("DOMContentLoaded", () => {')
    html.append('    applyI18n();')
    html.append('    const s = document.getElementById("splash");')
    html.append('    if (s) { setTimeout(() => { s.style.opacity = "0"; s.style.transition = "opacity 0.5s"; setTimeout(() => s.remove(), 500); }, 3000); }')
    html.append('  });')
    html.append('})();')
    html.append('')
    html.append('// Exit button & shortcuts')
    html.append('document.getElementById("exitBtn").onclick = () => window.close();')
    html.append('window.addEventListener("keydown", e => { if(e.ctrlKey && e.key==="q") window.close(); });')
    html.append('(function(){')
    html.append('  const REFRESH_MS = 60000;')
    html.append('  async function refresh(){')
    html.append('    try{')
    html.append('      const resp = await fetch(location.href, {cache:"no-store"});')
    html.append('      if(!resp.ok) return;')
    html.append('      const html = await resp.text();')
    html.append('      const parser = new DOMParser();')
    html.append('      const doc = parser.parseFromString(html, "text/html");')
    html.append('      const newContainer = doc.querySelector(".container");')
    html.append('      const oldContainer = document.querySelector(".container");')
    html.append('      if(newContainer && oldContainer){')
    html.append('        oldContainer.replaceWith(newContainer);')
    html.append('        history.replaceState(null,"",location.href);')
    html.append('        // Re-apply i18n after partial refresh')
    html.append('        if (window.applyI18n) window.applyI18n();')
    html.append('      }')
    html.append('    }catch(e){ console.warn("Auto-refresh failed", e); }')
    html.append('  }')
    html.append('  setInterval(refresh, REFRESH_MS);')
    html.append('})();')
    html.append('    </script>')
    html.append('</body>')
    html.append('</html>')
    
    return '\n'.join(html)

if __name__ == "__main__":
    output_path = "/tmp/storage_report.html"
    html = generate_html()
    Path(output_path).write_text(html)
    print(f"Reporte visual con datos ACTUALIZADOS generado: {output_path}")
    print(f"Abre http://localhost:8888/storage_report.html (requiere servidor)")
