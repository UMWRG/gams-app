# -*- mode: python -*-
a = Analysis(['GAMSimport.py'],
             pathex=[],
             hiddenimports=['..\\lib'],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='GAMSimport.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
