# -*- mode: python -*-
a = Analysis(['GAMSAutoRun.py'],
             pathex=['..\\lib'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,        
		  exclude_binaries=True,		  
          name='GAMSAutoRun.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='GAMSAutoRun')
