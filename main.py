# DOOMXTLAG — main.py placeholder
# Este arquivo serve apenas como redirect para o executavel principal.
# Nao contém logica de automacao.

import os
import sys
import subprocess

def get_base():
    return os.path.dirname(os.path.abspath(__file__))

def launch_exe():
    base = get_base()
    exe = os.path.join(base, 'mainrev.exe')
    if not os.path.exists(exe):
        input('[ERRO] mainrev.exe nao encontrado na pasta. Pressione Enter para sair.')
        sys.exit(1)
    subprocess.Popen([exe, '--updated'], cwd=base)
    sys.exit(0)

if __name__ == '__main__':
    launch_exe()
