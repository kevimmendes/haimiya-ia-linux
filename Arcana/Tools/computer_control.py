import os
import time

try:
    import pyautogui
except Exception:
    # No Linux sem sessao grafica o pyautogui levanta KeyError('DISPLAY') ao
    # ser importado. Se este import rebentasse, derrubava o ToolsSystem
    # inteiro e com ele o cerebro — a visao e o rato sao opcionais, o
    # dispatch de ferramentas nao.
    pyautogui = None

SEM_ECRA = "sem sessao grafica (pyautogui indisponivel)"


class ComputerControl:
    def __init__(self, output_callback=None):
        self.output_callback = output_callback
        self.disponivel = pyautogui is not None
        if self.disponivel:
            pyautogui.FAILSAFE = True

    def log(self, message):
        if self.output_callback:
            self.output_callback(message)
        else:
            print(message)

    def _recusa(self, accao):
        """Cada acao comeca por aqui. Sem ecra, recusa com motivo em vez de
        rebentar com um AttributeError dentro do try/except."""
        if self.disponivel:
            return False
        self.log(f"[RATO/TECLADO] {accao}: {SEM_ECRA}")
        return True

    # Mouse control
    def move_mouse(self, x, y, duration=0.1):
        """Move mouse to position (x, y) over duration seconds"""
        if self._recusa("Mover o rato"): return False
        try:
            pyautogui.moveTo(x, y, duration=duration)
            self.log(f"🖱️ Mouse movido para ({x}, {y})")
            return True
        except Exception as e:
            self.log(f"❌ Erro ao mover mouse: {e}")
            return False
    
    def click_mouse(self, button="left", clicks=1, duration=0.1):
        """Click with specified button (left/right), clicks count, and duration"""
        if self._recusa("Clique do rato"): return False
        try:
            if button == "right":
                pyautogui.rightClick()
            elif button == "left":
                pyautogui.click()
            
            for _ in range(clicks - 1):
                pyautogui.click(button=button, interval=duration)
            
            if clicks >= 1:
                pyautogui.click(button=button)
            
            self.log(f"🖱️ Clique {button} ({clicks}x) executado")
            return True
        except Exception as e:
            self.log(f"❌ Erro ao clicar mouse: {e}")
            return False
    
    def double_click(self, button="left"):
        """Double click with specified button"""
        if self._recusa("Duplo clique"): return False
        try:
            pyautogui.doubleClick(button=button)
            self.log(f"🖱️ Duplo clique {button} executado")
            return True
        except Exception as e:
            self.log(f"❌ Erro ao dar duplo clique: {e}")
            return False
    
    def right_click(self):
        """Right click"""
        return self.click_mouse(button="right", clicks=1)
    
    # Keyboard control
    def type_text(self, text, interval=0.01):
        """Type text character by character"""
        if self._recusa("Digitar texto"): return False
        try:
            pyautogui.typewrite(text, interval=interval)
            self.log(f"💰 Texto digitado: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            return True
        except Exception as e:
            self.log(f"❌ Erro ao digitar texto: {e}")
            return False
    
    def press_key(self, key):
        """Press a single key"""
        if self._recusa(f"Pressionar a tecla '{key}'"): return False
        try:
            pyautogui.press(key)
            self.log(f"⌨️ Tecla '{key}' pressionada")
            return True
        except Exception as e:
            self.log(f"❌ Erro ao pressionar tecla '{key}': {e}")
            return False
    
    def hotkey(self, *keys):
        """Press a hotkey combination (e.g., ctrl+c, win+r)"""
        if self._recusa(f"Atalho '{'+'.join(keys)}'"): return False
        try:
            pyautogui.hotkey(*keys)
            keys_str = '+'.join(keys)
            self.log(f"⌨️ Atalho '{keys_str}' executado")
            return True
        except Exception as e:
            self.log(f"❌ Erro ao executar atalho '{keys}': {e}")
            return False
    
    # Screen capture
    def capture_screen(self, region=None):
        """Capture screen, optionally a region (x, y, width, height)"""
        if region is None:
            from Arcana import platform_shim
            imagem = platform_shim.capturar_ecra()
            if imagem is None:
                self.log(f"[ECRA] Captura de ecra: {SEM_ECRA}.")
                return None
            self.log(f"📸 Tela capturada ({imagem.size[0]}x{imagem.size[1]})")
            return imagem
        if self._recusa("Capturar uma zona do ecra"): return None
        try:
            img = pyautogui.screenshot(region=region)
            self.log(f"📸 Tela capturada ({img.size[0]}x{img.size[1]})")
            return img
        except Exception as e:
            self.log(f"❌ Erro ao capturar tela: {e}")
            return None
    
    # Window management
    #
    # pygetwindow e so Windows: no Linux o pacote aborta com
    # NotImplementedError ao ser importado. Por isso a importacao e tentada
    # uma vez e o resultado fica em _gw; no Linux vale None e estas funcoes
    # recusam com motivo em vez de rebentar.
    _gw = None
    _gw_em_tentado = False

    @classmethod
    def _gwt(cls):
        if not cls._gw_em_tentado:
            cls._gw_em_tentado = True
            try:
                import pygetwindow as gw
                cls._gw = gw
            except Exception:
                cls._gw = None
        return cls._gw

    def get_windows(self):
        """Get list of window titles"""
        if self._gwt() is None:
            self.log("[JANELAS] Listar janelas: pygetwindow so funciona no Windows.")
            return []
        try:
            windows = self._gw.getAllTitles()
            return [w for w in windows if w]
        except Exception as e:
            self.log(f"❌ Erro ao obter janelas: {e}")
            return []
    
    def find_window(self, title_pattern):
        """Find a window by title pattern"""
        if self._gwt() is None:
            self.log(f"[JANELAS] Procurar '{title_pattern}': pygetwindow so funciona no Windows.")
            return None
        try:
            matches = self._gw.getWindowsWithTitle(title_pattern)
            return matches[0] if matches else None
        except Exception as e:
            self.log(f"❌ Erro ao encontrar janela: {e}")
            return None
    
    def activate_window(self, title_pattern):
        """Activate a window by title pattern"""
        try:
            window = self.find_window(title_pattern)
            if window:
                window.activate()
                self.log(f"🪟 Janela '{title_pattern}' ativada")
                return True
            self.log(f"⚠️ Janela '{title_pattern}' não encontrada")
            return False
        except Exception as e:
            self.log(f"❌ Erro ao ativar janela: {e}")
            return False