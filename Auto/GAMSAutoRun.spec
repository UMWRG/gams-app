# -*- mode: python -*-
a = Analysis(['GAMSAutoRun.py'],
             pathex=['..\\lib\\'],
             hiddenimports=['..\\lib\\'],
             hookspath=None,
             runtime_hooks=None,
             excludes=['_tkinter'])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
		  a.binaries,
          a.zipfiles,
		  a.datas,
          name='GAMSAutoRun.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )