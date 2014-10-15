# -*- mode: python -*-
a = Analysis(['GAMSexport.py'],
             pathex=[],
             hiddenimports=['..\\lib\\'],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='GAMSexport.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
