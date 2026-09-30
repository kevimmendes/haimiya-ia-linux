import json
import os
import re
from Arcana.Tools.computer_control import ComputerControl
from Arcana.Tools.file_system import FileSystem
from Arcana.Tools.games import Games
from Arcana.Tools.music_production import MusicProduction
from Arcana.Tools.photoshop_integration import PhotoshopIntegration
from Arcana.Tools.screen_vision import ScreenVision
from Arcana.Tools.task_planner import TaskPlanner


def _pesquisa_web(termo):
    """Chama o motor de busca DDG ja existente no projeto (import tardio)."""
    from Arcana.Net import search_ddg
    return search_ddg.search_ddg(termo)


class ToolsSystem:
    def __init__(self, output_callback=None, vision_client=None, searcher=None, vision_model=None):
        self.output_callback = output_callback
        self.computer = ComputerControl(output_callback)
        self.files = FileSystem(output_callback)
        self.screen = ScreenVision(output_callback, vision_client, vision_model)
        self.planner = TaskPlanner()
        self.searcher = searcher or _pesquisa_web
        self.photoshop = PhotoshopIntegration(output_callback, self.computer)
        self.music = MusicProduction(output_callback, self.searcher, self.files)
        self.games = Games(output_callback, self.searcher, self.screen)
        self.enabled = True
    
    def log(self, message):
        if self.output_callback:
            self.output_callback(message)
        else:
            print(message)
    
    # === COMPUTER CONTROL ===
    
    def move_mouse(self, x, y, duration=0.1):
        """Move mouse to position"""
        if not self.enabled: return False
        return self.computer.move_mouse(x, y, duration)
    
    def click(self, button="left", clicks=1, duration=0.1):
        """Click with specified button"""
        if not self.enabled: return False
        return self.computer.click_mouse(button, clicks, duration)
    
    def double_click(self, button="left"):
        """Double click"""
        if not self.enabled: return False
        return self.computer.double_click(button)
    
    def right_click(self):
        """Right click"""
        if not self.enabled: return False
        return self.computer.right_click()
    
    def type_text(self, text, interval=0.01):
        """Type text"""
        if not self.enabled: return False
        return self.computer.type_text(text, interval)
    
    def press_key(self, key):
        """Press a key"""
        if not self.enabled: return False
        return self.computer.press_key(key)
    
    def hotkey(self, *keys):
        """Press hotkey combination"""
        if not self.enabled: return False
        return self.computer.hotkey(*keys)
    
    # === FILE SYSTEM ===
    
    def search_files(self, pattern, extension=None, directory=None):
        """Search for files"""
        if not self.enabled: return []
        return self.files.search_files(pattern, extension, directory)
    
    def search_by_name(self, name, directory=None):
        """Search file by name"""
        if not self.enabled: return []
        return self.files.search_by_name(name, directory)
    
    def create_folder(self, folder_path):
        """Create folder"""
        if not self.enabled: return False
        return self.files.create_folder(folder_path)
    
    def rename_file(self, old_path, new_path, confirmar=False):
        """Rename file. DESTRUCTIVO: so executa se confirmar=True."""
        if not self.enabled: return False
        nome = os.path.basename(old_path)
        if not confirmar:
            self.log(f"Atencao: confirmar renomear '{nome}' para '{os.path.basename(new_path)}'? Responde 'sim' para executar.")
            return "AGUARDA_CONFIRMACAO"
        self.log(f"[OK] Renomeado: {nome} -> {os.path.basename(new_path)}")
        return self.files.rename_file(old_path, new_path)
    
    def move_file(self, source, destination, confirmar=False):
        """Move file. DESTRUCTIVO: so executa se confirmar=True."""
        if not self.enabled: return False
        nome = os.path.basename(source)
        if not confirmar:
            self.log(f"Atencao: confirmar mover '{nome}' para '{os.path.basename(destination)}'? Responde 'sim' para executar.")
            return "AGUARDA_CONFIRMACAO"
        self.log(f"[OK] Movido: {nome} -> {os.path.basename(destination)}")
        return self.files.move_file(source, destination)
    
    def copy_file(self, source, destination):
        """Copy file"""
        if not self.enabled: return False
        return self.files.copy_file(source, destination)
    
    def open_file(self, file_path):
        """Open file"""
        if not self.enabled: return False
        return self.files.open_file(file_path)
    
    def list_directory(self, path=None):
        """List directory"""
        if not self.enabled: return []
        return self.files.list_directory(path)
    
    # === SCREEN VISION ===
    
    def capture_screen(self):
        """Capture screen"""
        if not self.enabled: return None
        return self.screen.capture_screen_b64()
    
    def analyze_screen(self, user_query=None):
        """Analyze screen"""
        if not self.enabled: return None
        return self.screen.analyze_screen(user_query)
    
    def detect_elements(self, target_description):
        """Detect elements on screen"""
        if not self.enabled: return None
        return self.screen.detect_elements(target_description)
    
    # === PLANNING ===
    
    def start_task(self, task_name, steps=None):
        """Start a task planning"""
        if not self.enabled: return False
        self.planner.start_task(task_name, steps)
        return True
    
    def get_task_status(self):
        """Get current task progress"""
        if not self.enabled: return None
        return self.planner.get_status()
    
    def complete_current_step(self):
        """Mark current step as completed"""
        if not self.enabled: return False
        self.planner.complete_step()
        return True
    
    # === PHOTOSHOP ===
    
    def ps_abrir(self):
        if not self.enabled: return False
        return self.photoshop.abrir()
    
    def ps_documento(self, largura=1920, altura=1080, resolucao=72, nome="Documento"):
        if not self.enabled: return False
        return self.photoshop.criar_documento(largura, altura, resolucao, nome)
    
    def ps_layer(self, nome="Layer"):
        if not self.enabled: return False
        return self.photoshop.criar_layer(nome)
    
    def ps_estado(self):
        if not self.enabled: return None
        return self.photoshop.estado()
    
    def ps_ferramenta(self, nome):
        if not self.enabled: return False
        return self.photoshop.ferramenta(nome)
    
    # === MUSICA ===
    
    def mus_escala(self, tonica="C", tipo="menor"):
        if not self.enabled: return None
        return self.music.escala(tonica, tipo)
    
    def mus_acorde(self, tonica="C", tipo="menor"):
        if not self.enabled: return None
        return self.music.acorde(tonica, tipo)
    
    def mus_progressao(self, tom="C", tipo="menor", genero="pop"):
        if not self.enabled: return None
        return self.music.progressao(tom, tipo, genero)
    
    def mus_estrutura(self, genero="pop", bpm=120, compasso=4):
        if not self.enabled: return None
        return self.music.estrutura(genero, bpm, compasso)
    
    def mus_mix(self, fonte="voz"):
        if not self.enabled: return None
        return self.music.chain_mix(fonte)
    
    def mus_master(self, genero="pop", plataforma="spotify"):
        if not self.enabled: return None
        return self.music.chain_master(genero, plataforma)
    
    # === JOGOS ===
    
    def jogos_pesquisa(self, jogo, topico="dica", contexto=""):
        if not self.enabled: return None
        return self.games.pesquisa(jogo, topico, contexto)
    
    def jogos_correr(self):
        if not self.enabled: return {}
        return self.games.jogos_a_correr()
    
    def jogos_ajuda(self, texto):
        if not self.enabled: return None
        return self.games.ajuda(texto)
    
    # === INTEGRATION HELPERS ===
    
    def get_app_names(self):
        """Get list of known apps for LLM context"""
        # This is a simplified version - in real use, would query the launcher
        return ["Bloco de Notas", "Calculadora", "YouTube", "Navegador", 
                "Minecraft", "Cyberpunk 2077"]
    
    def enable(self, state=True):
        """Enable/disable the tools system"""
        self.enabled = state
        self.log(f"🔧 Sistema de ferramentas {'ativado' if state else 'desativado'}")
    
    def to_dict(self):
        """Convert to dictionary for saving/loading state"""
        return {
            "enabled": self.enabled,
            "planner_state": self.planner.get_status()
        }
    
    @classmethod
    def from_dict(cls, data, output_callback=None, vision_client=None, vision_model=None):
        """Create from dictionary state"""
        instance = cls(output_callback, vision_client, vision_model=vision_model)
        instance.enabled = data.get("enabled", True)
        return instance