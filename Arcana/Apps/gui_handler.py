import json
import os

try:
    import tkinter as tk
    from tkinter import ttk
    TEM_PAINEL = True
except ImportError:
    # python3-tk nao vem no Python oficial. Sem isto, o import deste modulo
    # rebentava e derrubava o run.py inteiro — o painel e opcional.
    tk = None
    ttk = None
    TEM_PAINEL = False

MOTIVO_SEM_PAINEL = "o modulo 'tkinter' nao esta instalado (no Ubuntu/Debian: sudo apt install python3-tk)"

# PADRÃO ABSOLUTO E CORRETO: brain.json
BRAIN_FILE = "Arcana/armazen/brain.json"

# Paleta de Cores 
BG_COLOR = "#11111b"       
SURFACE_COLOR = "#1e1e2e"  
HIGHLIGHT_COLOR = "#313244" 
REM_BLUE = "#89b4fa"       
REM_PINK = "#f5c2e7"       
TEXT_COLOR = "#cdd6f4"     
TEXT_DIM = "#a6adc8"

class RemCard(tk.Frame if TEM_PAINEL else object):
    # Sem tkinter esta classe nao e usada: o painel nunca arranca. A base fica
    # `object` para o ficheiro continuar a importar, e `iniciar_gui_loop` e um
    # no-op nesse caso.
    def __init__(self, master, text, value, variable, icon="", color=REM_BLUE, **kwargs):
        super().__init__(master, bg=SURFACE_COLOR, cursor="hand2", bd=0, **kwargs)
        self.text, self.value, self.variable, self.color = text, value, variable, color
        
        # Botões menores para caberem lado a lado organizados
        self.lbl_icon = tk.Label(self, text=icon, font=("Segoe UI Emoji", 12), bg=SURFACE_COLOR, fg=color)
        self.lbl_icon.pack(side="left", padx=(10, 5), pady=8)
        self.lbl_text = tk.Label(self, text=text, font=("Segoe UI", 9, "bold"), bg=SURFACE_COLOR, fg=TEXT_COLOR)
        self.lbl_text.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        for w in (self, self.lbl_icon, self.lbl_text):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", lambda e: self._on_hover())
            w.bind("<Leave>", lambda e: self._update_style())
        self._update_style()

    def _on_click(self, event):
        self.variable.set(self.value)
        for sibling in self.master.winfo_children():
            if isinstance(sibling, RemCard): sibling._update_style()

    def _on_hover(self):
        if self.variable.get() != self.value: self.configure(bg=HIGHLIGHT_COLOR)

    def _update_style(self):
        is_selected = self.variable.get() == self.value
        bg = self.color if is_selected else SURFACE_COLOR
        fg = BG_COLOR if is_selected else TEXT_COLOR
        self.configure(bg=bg)
        self.lbl_icon.configure(bg=bg, fg=BG_COLOR if is_selected else self.color)
        self.lbl_text.configure(bg=bg, fg=fg)

def criar_checkbutton(master, text, variable, fg_color=TEXT_COLOR):
    return tk.Checkbutton(
        master, text=text, variable=variable, 
        bg=SURFACE_COLOR, fg=fg_color, selectcolor=BG_COLOR,
        activebackground=SURFACE_COLOR, activeforeground=REM_PINK,
        font=("Segoe UI", 10), cursor="hand2", bd=0, highlightthickness=0
    )

class RemGUI:
    janela = None

    @classmethod
    def disponivel(cls):
        """O painel so existe com tkinter e sessao grafica (DISPLAY/Wayland)."""
        from Arcana import platform_shim
        if not TEM_PAINEL:
            return False, MOTIVO_SEM_PAINEL
        if not platform_shim.TEM_ECRA:
            return False, "nao ha sessao grafica (DISPLAY/WAYLAND_DISPLAY por definir)"
        return True, ""

    @classmethod
    def iniciar_gui_loop(cls, nome_ai_override=None):
        pode, motivo = cls.disponivel()
        if not pode:
            print(f"🎨 Painel de Configurações ignorado: {motivo}.")
            return
        if cls.janela is not None: return
        
        try:
            with open(BRAIN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                modelos = data.get("modelos_ativos", {"local": "nvidia", "discord": "groq"})
                vtuber_ativo = data.get("vtuber_overlay_ativo", False)
                nome_ai = data.get("personality", {}).get("name", "IA")
        except:
            modelos = {"local": "nvidia", "discord": "groq"}
            vtuber_ativo = False
            nome_ai = "IA"

        if nome_ai_override: nome_ai = nome_ai_override
        
        cls.janela = tk.Tk()
        cls.janela.title(f"Rem System - {nome_ai}")
        cls.janela.geometry("680x560")
        cls.janela.configure(bg=BG_COLOR)
        
        # --- CABEÇALHO COM A FOTO ---
        header = tk.Frame(cls.janela, bg=BG_COLOR)
        header.pack(fill="x", pady=(20, 10))
        try:
            from PIL import Image, ImageTk
            img_path = "Arcana/Apps/rem_theme.jpg"
            if not os.path.exists(img_path): img_path = "Arcana/Apps/rem_theme.png"
            if os.path.exists(img_path):
                img = Image.open(img_path).resize((90, 90), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                lbl_img = tk.Label(header, image=photo, bg=BG_COLOR, bd=2, highlightbackground=REM_BLUE, highlightthickness=2)
                lbl_img.image = photo
                lbl_img.pack()
        except: tk.Label(header, text="💠", font=("Segoe UI", 40), bg=BG_COLOR, fg=REM_BLUE).pack()
        
        tk.Label(cls.janela, text="Painel de Controlo Arcana", font=("Segoe UI", 16, "bold"), bg=BG_COLOR, fg=TEXT_COLOR).pack()
        
        # --- GRELHA PRINCIPAL ---
        grid_frame = tk.Frame(cls.janela, bg=BG_COLOR)
        grid_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        var_local = tk.StringVar(value=modelos.get("local", "nvidia"))
        var_discord = tk.StringVar(value=modelos.get("discord", "groq"))
        var_vtuber = tk.BooleanVar(value=vtuber_ativo)
        
        # Coluna Esquerda: Modelos Cognitivos (Cérebros)
        col_esq = tk.Frame(grid_frame, bg=BG_COLOR)
        col_esq.pack(side="left", fill="both", expand=True, padx=10)
        
        tk.Label(col_esq, text="🧠 MODELO LOCAL (PC)", font=("Segoe UI", 9, "bold"), bg=BG_COLOR, fg=REM_PINK).pack(anchor="w", pady=(0, 5))
        f_local = tk.Frame(col_esq, bg=BG_COLOR)
        f_local.pack(fill="x", pady=0)
        RemCard(f_local, "NVIDIA", "nvidia", var_local, icon="🚀", color=REM_PINK).pack(side="left", fill="x", expand=True, padx=(0, 2))
        RemCard(f_local, "GROQ", "groq", var_local, icon="⚡", color=REM_PINK).pack(side="left", fill="x", expand=True, padx=(2, 0))

        tk.Label(col_esq, text="🌐 MODELO DISCORD", font=("Segoe UI", 9, "bold"), bg=BG_COLOR, fg="#a6e3a1").pack(anchor="w", pady=(20, 5))
        f_disc = tk.Frame(col_esq, bg=BG_COLOR)
        f_disc.pack(fill="x", pady=0)
        RemCard(f_disc, "NVIDIA", "nvidia", var_discord, icon="🚀", color="#a6e3a1").pack(side="left", fill="x", expand=True, padx=(0, 2))
        RemCard(f_disc, "GROQ", "groq", var_discord, icon="⚡", color="#a6e3a1").pack(side="left", fill="x", expand=True, padx=(2, 0))
        
        # Coluna Direita: Avatar
        col_dir = tk.Frame(grid_frame, bg=BG_COLOR)
        col_dir.pack(side="right", fill="both", expand=True, padx=10)
        
        tk.Label(col_dir, text="🎭 AVATAR VIRTUAL", font=("Segoe UI", 9, "bold"), bg=BG_COLOR, fg=REM_BLUE).pack(anchor="w", pady=(0, 5))
        RemCard(col_dir, "Ativar Overlay", True, var_vtuber, icon="✨", color=REM_BLUE).pack(fill="x", pady=(0, 4))
        RemCard(col_dir, "Desativar", False, var_vtuber, icon="🌑", color=REM_BLUE).pack(fill="x", pady=0)
        
        # --- RODAPÉ COM BOTÕES DE AÇÃO ---
        footer = tk.Frame(cls.janela, bg=BG_COLOR)
        footer.pack(fill="x", side="bottom", pady=25)
        
        tk.Button(footer, text="💬 DISCORD SETUP", command=lambda: cls.abrir_gui_discord(cls.janela), bg=BG_COLOR, fg=REM_PINK, font=("Segoe UI", 9, "bold"), activebackground=REM_PINK, activeforeground=BG_COLOR, bd=1, relief="solid", cursor="hand2", padx=20, pady=10).pack(side="left", padx=(40, 10))
        
        def salvar():
            if os.path.exists(BRAIN_FILE):
                with open(BRAIN_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
                data.update({"vtuber_overlay_ativo": var_vtuber.get()})
                if "modelos_ativos" not in data: data["modelos_ativos"] = {}
                data["modelos_ativos"]["local"] = var_local.get()
                data["modelos_ativos"]["discord"] = var_discord.get()
                with open(BRAIN_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)
            cls.janela.withdraw()
            
        tk.Button(footer, text="💾 GUARDAR ALTERAÇÕES", command=salvar, bg=REM_BLUE, fg=BG_COLOR, font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2", padx=30, pady=10).pack(side="right", padx=(10, 40))
        
        cls.janela.protocol("WM_DELETE_WINDOW", lambda: cls.janela.withdraw())
        cls.janela.mainloop()

    @classmethod
    def abrir_gui_discord(cls, parent_janela):
        janela_discord = tk.Toplevel(parent_janela)
        janela_discord.title("💙 Painel Mestre do Discord")
        janela_discord.geometry("1100x850") 
        janela_discord.configure(bg=BG_COLOR)
        
        try:
            from PIL import Image, ImageTk
            img_p = "Arcana/Apps/rem_theme.jpg"
            if not os.path.exists(img_p): img_p = "Arcana/Apps/rem_theme.png"
            if os.path.exists(img_p):
                img = Image.open(img_p).resize((100, 100), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(janela_discord, image=photo, bg=BG_COLOR, bd=2, highlightbackground=REM_BLUE, highlightthickness=2)
                lbl.image = photo
                lbl.pack(pady=10)
        except: pass
        
        try:
            with open(BRAIN_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
        except: data = {}

        var_discord_on = tk.BooleanVar(value=data.get("discord_active", False))
        var_music_on = tk.BooleanVar(value=data.get("discord_music_mode", False))
        var_server = tk.BooleanVar(value=data.get("discord_server_active", True))
        var_mentions = tk.BooleanVar(value=data.get("discord_mentions", True))
        var_dinamismo = tk.BooleanVar(value=data.get("discord_dinamismo", True))
        var_autopost = tk.IntVar(value=data.get("discord_auto_post", 0))
        var_unit = tk.StringVar(value=data.get("discord_auto_post_unit", "Minutos"))
        var_target_on = tk.BooleanVar(value=data.get("discord_target_user_active", False))
        var_dm = tk.BooleanVar(value=data.get("discord_dm_active", False))
        var_dm_dono = tk.BooleanVar(value=data.get("discord_dm_dono_always", False))
        target_name = data.get("discord_target_user_name", "")
        
        disabled_guilds = data.get("discord_disabled_guilds", [])
        guilds_list = data.get("discord_guilds_cache", [])

        container = tk.Frame(janela_discord, bg=BG_COLOR)
        container.pack(fill="both", expand=True, padx=20, pady=10)
        
        left_col = tk.Frame(container, bg=BG_COLOR)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        right_col = tk.Frame(container, bg=BG_COLOR)
        right_col.pack(side="right", fill="both", expand=True, padx=(15, 0))

        tk.Label(left_col, text="⚙️ GERAL E OPERAÇÃO", font=("Segoe UI", 10, "bold"), bg=BG_COLOR, fg=REM_PINK).pack(anchor="w", pady=(0, 5))
        f_main = tk.Frame(left_col, bg=SURFACE_COLOR, padx=15, pady=10)
        f_main.pack(fill="x", pady=5)
        criar_checkbutton(f_main, " 🔴 LIGAR A IA NO DISCORD", var_discord_on, fg_color="#f38ba8").pack(anchor="w", pady=2)
        criar_checkbutton(f_main, " 🎵 Ativar Modo Música (Bloqueia Escuta de Voz)", var_music_on).pack(anchor="w", pady=2)

        tk.Label(left_col, text="🛡️ REGRAS DE SERVIDOR", font=("Segoe UI", 10, "bold"), bg=BG_COLOR, fg=REM_PINK).pack(anchor="w", pady=(15, 5))
        f_server = tk.Frame(left_col, bg=SURFACE_COLOR, padx=15, pady=10)
        f_server.pack(fill="x", pady=5)
        criar_checkbutton(f_server, " Responder livremente (Texto e Voz)", var_server).pack(anchor="w", pady=2)
        criar_checkbutton(f_server, " Permitir que responda a Menções (@)", var_mentions).pack(anchor="w", pady=2)
        criar_checkbutton(f_server, " Ativar Dinamismo (Zoações e Offline)", var_dinamismo).pack(anchor="w", pady=2)

        tk.Label(left_col, text="⏱️ INTERVALO AUTO-POST (0 = Desligado)", font=("Segoe UI", 10, "bold"), bg=BG_COLOR, fg=TEXT_DIM).pack(anchor="w", pady=(15, 5))
        f_tempo = tk.Frame(left_col, bg=SURFACE_COLOR, padx=15, pady=10)
        f_tempo.pack(fill="x", pady=5)
        frame_t_inner = tk.Frame(f_tempo, bg=SURFACE_COLOR)
        frame_t_inner.pack(anchor="w")
        e_time = tk.Entry(frame_t_inner, textvariable=var_autopost, width=8, bg=HIGHLIGHT_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 11), insertbackground=TEXT_COLOR, relief="flat")
        e_time.pack(side="left", padx=(0, 10), ipady=3)
        cb_unit = ttk.Combobox(frame_t_inner, textvariable=var_unit, values=["Segundos", "Minutos"], width=12, state="readonly", font=("Segoe UI", 10))
        cb_unit.pack(side="left", ipady=2)

        tk.Label(left_col, text="🎯 FOCO EM USUÁRIO", font=("Segoe UI", 10, "bold"), bg=BG_COLOR, fg=REM_PINK).pack(anchor="w", pady=(15, 5))
        f_alvo = tk.Frame(left_col, bg=SURFACE_COLOR, padx=15, pady=10)
        f_alvo.pack(fill="x", pady=5)
        criar_checkbutton(f_alvo, " Responder a TODAS as mensagens da pessoa", var_target_on).pack(anchor="w", pady=2)
        tk.Label(f_alvo, text="Nome (@ ou Nick):", bg=SURFACE_COLOR, fg=TEXT_DIM, font=("Segoe UI", 9)).pack(anchor="w", pady=(5,2))
        entry_target = tk.Entry(f_alvo, bg=HIGHLIGHT_COLOR, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, relief="flat", font=("Segoe UI", 11))
        entry_target.insert(0, target_name)
        entry_target.pack(fill="x", pady=2, ipady=4)

        tk.Label(left_col, text="🔒 PRIVADO (DM)", font=("Segoe UI", 10, "bold"), bg=BG_COLOR, fg=REM_PINK).pack(anchor="w", pady=(15, 5))
        f_dm = tk.Frame(left_col, bg=SURFACE_COLOR, padx=15, pady=10)
        f_dm.pack(fill="x", pady=5)
        criar_checkbutton(f_dm, " Responder Mensagens no Privado", var_dm).pack(anchor="w", pady=2)
        criar_checkbutton(f_dm, " IGNORAR TRAVA: Sempre responder ao Dono", var_dm_dono).pack(anchor="w", pady=2)

        tk.Label(right_col, text="📡 SERVIDORES ATIVOS (Ligue o Bot primeiro)", font=("Segoe UI", 11, "bold"), bg=BG_COLOR, fg=REM_BLUE).pack(anchor="w", pady=(0, 10))
        
        canvas_bg = tk.Frame(right_col, bg=SURFACE_COLOR, bd=0)
        canvas_bg.pack(fill="both", expand=True)

        canvas = tk.Canvas(canvas_bg, bg=SURFACE_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_bg, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=SURFACE_COLOR)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=450)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        guild_vars = {}
        
        def toggle_all(state):
            for v in guild_vars.values(): v.set(state)

        btn_all = tk.Frame(right_col, bg=BG_COLOR)
        btn_all.pack(fill="x", pady=(10, 0))
        tk.Button(btn_all, text="✅ Ativar Todos", command=lambda: toggle_all(True), bg=SURFACE_COLOR, fg=REM_BLUE, font=("Segoe UI", 9, "bold"), bd=0, padx=15, pady=5, cursor="hand2").pack(side="left")
        tk.Button(btn_all, text="❌ Desativar Todos", command=lambda: toggle_all(False), bg=SURFACE_COLOR, fg=REM_PINK, font=("Segoe UI", 9, "bold"), bd=0, padx=15, pady=5, cursor="hand2").pack(side="left", padx=10)

        if not guilds_list:
            tk.Label(scroll_frame, text="Aguardando a conexão do Bot para ler os servidores...\nFeche esta janela, certifique-se que a IA está online\ne abra novamente.", bg=SURFACE_COLOR, fg=TEXT_DIM, font=("Segoe UI", 10)).pack(pady=40)
        else:
            for guild in guilds_list:
                g_id = str(guild['id'])
                is_active = g_id not in disabled_guilds
                var = tk.BooleanVar(value=is_active)
                guild_vars[g_id] = var
                
                f_guild = tk.Frame(scroll_frame, bg=HIGHLIGHT_COLOR, pady=8, padx=15)
                f_guild.pack(fill="x", pady=3, padx=5)
                tk.Label(f_guild, text=f"🌐 {guild['name']}", bg=HIGHLIGHT_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).pack(side="left")
                tk.Checkbutton(f_guild, text="Ativo", variable=var, bg=HIGHLIGHT_COLOR, fg=REM_PINK, selectcolor=BG_COLOR, activebackground=HIGHLIGHT_COLOR, bd=0, cursor="hand2").pack(side="right")

        def salvar_discord():
            try:
                with open(BRAIN_FILE, 'r', encoding='utf-8') as f: d = json.load(f)
            except: d = {}
            
            new_disabled = [gid for gid, var in guild_vars.items() if not var.get()]
            
            d.update({
                "discord_active": var_discord_on.get(),
                "discord_music_mode": var_music_on.get(),
                "discord_mentions": var_mentions.get(),
                "discord_dinamismo": var_dinamismo.get(),
                "discord_server_active": var_server.get(),
                "discord_dm_active": var_dm.get(),
                "discord_dm_dono_always": var_dm_dono.get(),
                "discord_auto_post": var_autopost.get(),
                "discord_auto_post_unit": var_unit.get(),
                "discord_target_user_active": var_target_on.get(),
                "discord_target_user_name": entry_target.get().strip(),
                "discord_disabled_guilds": new_disabled
            })
            
            with open(BRAIN_FILE, 'w', encoding='utf-8') as f: json.dump(d, f, indent=4, ensure_ascii=False)
            print(" [SISTEMA] Configurações do Discord Atualizadas e Salvas!")
            janela_discord.destroy()

        tk.Button(janela_discord, text="💾 APLICAR CONFIGURAÇÕES DO DISCORD", command=salvar_discord, 
                  bg=REM_BLUE, fg=BG_COLOR, font=("Segoe UI", 11, "bold"), 
                  bd=0, cursor="hand2", padx=40, pady=12).pack(pady=(0, 20))
        
        janela_discord.transient(parent_janela)
        janela_discord.grab_set()
        janela_discord.focus_force()

    @classmethod
    def toggle(cls):
        if cls.janela:
            cls.janela.after(0, lambda: cls.janela.deiconify() if cls.janela.state() != "normal" else cls.janela.withdraw())