# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Importar bibliotecas para encontrar sus rutas
import customtkinter
import CTkMessagebox

# Encontrar directorios de módulos
ctk_dir = os.path.dirname(customtkinter.__file__)
mb_dir = os.path.dirname(CTkMessagebox.__file__)

# Rutas de datos necesarias
datas = [
    (os.path.join(ctk_dir, 'assets'), 'customtkinter/assets'),
    (os.path.join(mb_dir, 'icons'), 'CTkMessagebox/icons'),
]

# Si el proyecto necesita otros archivos específicos (imágenes locales, etc), se agregarían aquí:
# datas += [('mi_logo.ico', '.')]

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=['customtkinter', 'CTkMessagebox', 'database', 'openpyxl', 'tkcalendar', 'babel.numbers'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GestionMensajeria',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,         # Cambiar a True si se quiere ver consola de errores
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GestionMensajeria',
)
