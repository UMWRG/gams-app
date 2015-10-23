# -*- mode: python -*-
a = Analysis(['GAMSAutoRun.py'],
             pathex=['..\\lib'],
             hiddenimports=['filecmp', 'gams'],
             hookspath=None,
             runtime_hooks=None,
             excludes=['_tkinter', 'IPython', 'win32ui', 'cPickle', 'win32com', 'sqlalchemy', 'sqlite3', 'pyexpat', 'gams'] )
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
