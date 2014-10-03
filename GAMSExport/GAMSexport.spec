# -*- mode: python -*-
a = Analysis(['GAMSexport.py'],
             pathex=['F:\\work\\HYDRA\\svn\\HYDRA\\HydraPlugins\\GAMSplugin\\trunk'],
             hiddenimports=[],
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
