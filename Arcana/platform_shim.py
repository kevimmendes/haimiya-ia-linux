import os
import platform
import shutil
import subprocess
import sys
import importlib.util

IS_WINDOWS = os.name == "nt"
IS_MAC = platform.system() == "Darwin"
IS_LINUX = sys.platform.startswith("linux")


def _detectar_servidor_grafico():
    if IS_WINDOWS or IS_MAC:
        return "nativo"
    wayland = os.environ.get("WAYLAND_DISPLAY")
    x11 = os.environ.get("DISPLAY")
    if wayland and not x11:
        return "wayland"
    if x11:
        return "x11"
    return "headless"


SERVIDOR_GRAFICO = _detectar_servidor_grafico()
TEM_ECRA = SERVIDOR_GRAFICO in ("x11", "wayland", "nativo")


def tem_ferramenta(nome):
    return shutil.which(nome) is not None


def detetar_backend_ecra():
    if IS_WINDOWS or IS_MAC:
        return "pil"
    try:
        import mss
        return "mss"
    except ImportError:
        return "pyautogui"


def capturas_disponiveis():
    motivos = []
    if not TEM_ECRA:
        motivos.append(
            "sem sessao grafica (DISPLAY e WAYLAND_DISPLAY por definir)"
        )
    if not (IS_WINDOWS or IS_MAC) and detetar_backend_ecra() != "mss":
        motivos.append("backend de captura indisponivel (instale 'mss')")
    return motivos


def abrir_caminho(caminho):
    """Abre um ficheiro/pasta com a aplicacao por omissao do sistema."""
    if not caminho:
        return False
    try:
        if IS_WINDOWS:
            os.startfile(caminho)
        elif IS_MAC:
            subprocess.Popen(["open", caminho])
        else:
            xdg = shutil.which("xdg-open")
            if not xdg:
                return False
            subprocess.Popen([xdg, caminho], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def lancar_comando(alvo):
    """Executa um alvo do dicionario de apps."""
    if not alvo:
        return False
    try:
        if IS_WINDOWS:
            subprocess.Popen(f"start {alvo}", shell=True)
            return True

        if str(alvo).startswith(("http://", "https://")):
            return abrir_caminho(alvo)

        if os.path.isfile(alvo) and os.access(alvo, os.X_OK):
            subprocess.Popen([alvo])
            return True

        separador = alvo.count(">") or 1
        if separador > 1:
            partes = [p.strip() for p in alvo.split(">") if p.strip()]
        else:
            partes = [alvo.strip()]

        for parte in partes:
            tokens = parte.split()
            if not tokens:
                continue
            exe = shutil.which(tokens[0])
            if not exe:
                return False
            subprocess.Popen([exe] + tokens[1:])

        return True
    except Exception:
        return False


def capturar_ecra():
    """Devolve uma imagem PIL do ecra inteiro, ou None se nao for possivel."""
    try:
        if IS_WINDOWS or IS_MAC:
            from PIL import ImageGrab
            return ImageGrab.grab()

        backend = detetar_backend_ecra()
        if backend == "mss":
            import mss
            from PIL import Image
            with mss.mss() as sct:
                bruto = sct.grab(sct.monitors[1])
                return Image.frombytes("RGB", bruto.size, bruto.bgra, "raw", "BGRX")

        import pyautogui
        return pyautogui.screenshot()
    except Exception:
        return None


DEPENDENCIAS_OPCIONAIS = {
    "pyaudio": "microfone (modos de voz)",
    "pygame": "reproducao de audio e bipes",
    "torch": "deteccao de voz (VAD silero); sem ele, deteccao por energia",
    "pyautogui": "rato e teclado",
    "pygetwindow": "gestao de janelas (so Windows; no Linux o pacote aborta)",
    "cv2": "overlay VTuber",
    "keyboard": "atalhos F2/F3/F4 e tecla 'home'",
    "mss": "captura de ecra no Linux",
}


def dependencia_disponivel(nome):
    """Se o interpretador encontraria o modulo, sem o importar.

    Importar serve para quase nada aqui: o `pyautogui` no Linux sem sessao
    grafica levanta KeyError, e o `pygetwindow` levanta NotImplementedError.
    Perguntar ao `find_spec` evita esses dois ao mesmo tempo.
    """
    try:
        return importlib.util.find_spec(nome) is not None
    except (ImportError, ValueError):
        return False


def dependencias_em_falta():
    """[(pacote, para que serve)] do que falta, em ordem de declaracao."""
    return [
        (nome, para)
        for nome, para in DEPENDENCIAS_OPCIONAIS.items()
        if not dependencia_disponivel(nome)
    ]


def avisar_dependencias(msg=None):
    """Imprime o que falta e o que deixa de funcionar. Devolve as linhas."""
    faltam = dependencias_em_falta()
    if not faltam:
        return []
    linhas = ["[OPCIONAL] Pacotes em falta — a Haimiya arranca na mesma, mas:"] + [
        f"    - {nome}: {para}" for nome, para in faltam
    ]
    emitir = msg or print
    for linha in linhas:
        emitir(linha)
    return linhas


CAPACIDADES = {
    "photoshop": IS_WINDOWS,
    "overlay_vtuber": IS_WINDOWS,
    "autohotkey": IS_WINDOWS,
    "ecra": TEM_ECRA,
    "rato_teclado": TEM_ECRA,
    "ficheiros": True,
}


def desativar_por_plataforma(log=None):
    """Desliga as ferramentas que dependem de Win32/COM e avisa o utilizador."""
    msg = log or (lambda m: print(m))

    if not CAPACIDADES["overlay_vtuber"]:
        msg("[PLATAFORMA] Overlay VTuber desativado: depende de win32gui/win32ui.")
    if not CAPACIDADES["photoshop"]:
        msg("[PLATAFORMA] Photoshop desativado: depende de COM (win32com).")
    if not CAPACIDADES["ecra"]:
        motivos = ", ".join(capturas_disponiveis())
        msg(f"[PLATAFORMA] Visao e rato/teclado desativados: {motivos}.")
    if CAPACIDADES["ecra"] and SERVIDOR_GRAFICO == "wayland":
        msg("[PLATAFORMA] Wayland detetado via XWayland: so captura janelas X11.")


def descrever_ambiente():
    linhas = [
        f"sistema      : {platform.system()} {platform.release()}",
        f"python       : {platform.python_version()}",
        f"ecra         : {SERVIDOR_GRAFICO}",
        f"backend ecra : {detetar_backend_ecra()}",
        f"xdg-open     : {'sim' if tem_ferramenta('xdg-open') else 'nao'}",
        f"deps opcionais: {len(DEPENDENCIAS_OPCIONAIS) - len(dependencias_em_falta())}/{len(DEPENDENCIAS_OPCIONAIS)} instaladas",
    ]
    for nome, ok in CAPACIDADES.items():
        linhas.append(f"{nome:<12}: {'sim' if ok else 'nao'}")
    return "\n".join(linhas)
