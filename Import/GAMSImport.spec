# -*- mode: python -*-
a = Analysis(['GAMSImport.py'],
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
          name='GAMSImport.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )

