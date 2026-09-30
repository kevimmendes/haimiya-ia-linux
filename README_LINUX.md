# Haimiya IA — Linux

Versão Linux da Haimiya, em repositório próprio. O código Windows continua
intacto no repositório original ([`kevimmendes/haimiya-ia`](https://github.com/kevimmendes/haimiya-ia),
branch `master`).

## O que funciona

- 🧠 Cérebro (Groq) e memória persistente
- 🎙️ Voz: microfone → Whisper →(edge-tts
- 👁️ Visão do ecrã (mss)
- 🖱️ Rato e teclado (pyautogui)
- 📂 Ficheiros: criar, mover, renomear, abrir, listar
- 🔍 Pesquisa web (DuckDuckGo)
- 🧮 Teoria musical e planeador de tarefas
- 🪟 Painel de configuração (tkinter)

## O que NÃO funciona (e porquê)

| Funcionalidade | Motivo |
|---|---|
| 🎨 Overlay VTuber | Usa `win32gui`/`win32ui`/`ctypes.windll` — Win32 API pura |
| 🎨 Photoshop | Automação via COM (`win32com.client`), que não existe no Linux |
| Atalhos F2/F3/F4 e tecla `home` | O pacote `keyboard` exige root no Linux (ver abaixo) |

O Photoshop também não tem versão oficial para Linux, portanto mesmo com
ponte wouldn’t help.

## Instalação

```bash
git clone https://github.com/kevimmendes/haimiya-ia-linux
cd haimiya-ia-linux

./setup_linux.sh
```

O script instala as libs de sistema (precisa de `sudo`), cria o `.venv`,
instala as dependências e copia o `.env.example` para `.env`.

Depois preenche a chave:

```bash
nano .env
```

```ini
GROQ_API_KEY_LLM=aquela_a_tua_chave
```

## Correr

```bash
./run_ia.sh
```

## Aviso importante: Wayland

A captura de ecrã em Wayland só vê janelas **X11** (via XWayland). Se usares
GNOME em Wayland, a visão do ecrã vai devolver vazio.

Opções, por ordem de esforço:

1. **Muda a sessão para Xorg** —GNOME: Definições → Utilizadores →
   Desbloquear → Tipo de sessão → *Ubuntu on Xorg*. Funciona logo.
2. **Faz login numa sessão X11**.
3. **Desliga a visão** e usa só a voz.

Confirma em que modo estás:

```bash
echo $XDG_SESSION_TYPE     # x11, wayland ou tty
echo $DISPLAY              # vazio se for Wayland puro
```

## Atalhos de teclado (opcional)

Para ativar F2/F3/F4 e a tecla `home` para parar de ouvir:

```bash
sudo usermod -aG input "$USER"
```

Depois **reinicia a sessão** (logout/login, não só fechar o terminal).
Sem isto a Haimiya arranca na mesma, mas os atalhos ficam desligados —
é aviso amarelo no arranque, não erro.

## Visão local (recomendado)

Mandar screenshots do teu desktop para a Groq é enviar o teu ecrã para fora.
Para ficar tudo na tua máquina, usa o Ollama:

```bash
# noutro terminal
ollama serve
ollama pull qwen2.5vl:3b
```

```ini
# .env
VISAO_PROVEDOR=local
VISAO_MODELO=qwen2.5vl:3b
```

Modelos que cabem em 16 GB sem GPU NVIDIA:

| Modelo | Peso | Nota |
|---|---|---|
| `qwen2.5vl:3b` | ~3 GB | Recomendado |
| `moondream` | ~1.7 GB | Mais leve, pior |
| `llama3.2-vision:11b` | ~8 GB | Pesado |

## Diagnóstico

```bash
source .venv/bin/activate
python3 -c "
import sys; sys.path.insert(0,'.')
from Arcana import platform_shim as ps
print(ps.descrever_ambiente())
"
```

O arranque também imprime isto. Se aparecer `ecra: nao`, é falta de sessão
gráfica — a voz continua a funcionar, a visão não.

## Como foi portado

Um único ficheiro novo, `Arcana/platform_shim.py`, concentra as diferenças
de plataforma. Ele deteta o sistema e o servidor gráfico e expõe:

- `capturar_ecra()` — `mss` no Linux, `PIL.ImageGrab` no Windows
- `abrir_caminho()` — `xdg-open` no Linux, `os.startfile` no Windows
- `lancar_comando()` — executa do PATH, com URLs via `xdg-open`
- `CAPACIDADES` — o que está disponível, para desligar o resto com aviso

Alterações nos ficheiros existentes:

| Ficheiro | Alteração |
|---|---|
| `Arcana/platform_shim.py` | **Novo.** Deteção e wrappers portáteis |
| `Arcana/Tools/screen_vision.py` | `ImageGrab` → `platform_shim.capturar_ecra()` |
| `Arcana/Tools/file_system.py` | `os.startfile` → `platform_shim.abrir_caminho()` |
| `Arcana/Aura/app_launcher.py` | `start {target}` → shim; dicionário Linux; `winsound` removido; `keyboard` opcional |
| `run.py` | `ImageGrab` → shim; overlay gateado; `keyboard` opcional; aviso de ambiente |

### Detalhe de segurança

`subprocess.Popen(f'start {target}', shell=True)` no Windows tinha
`shell=True`. No ramo Linux **não há `shell=True`**: o alvo é dividido em
tokens e cada um é procurado no `PATH` com `shutil.which`. O `target`
continua a vir do dicionário fechado, nunca do texto do LLM — mas evita
uma superfície de injeção desnecessária.

## Instalar apps do dicionário Linux

Os alvos do dicionário são os standards do GNOME. Em KDE, XFCE ou noutra
distro, edita `Arcana/Aura/app_launcher.py` → `_apps_linux()`. Cada entrada
aceita um `fallback`, tentado se o primeiro alvo não existir:

```python
"calculadora": {
    "target": "gnome-calculator",
    "fallback": "kcalc",
    ...
}
```

## Regressões conhecidas

- **Perde Photoshop** e o overlay VTuber (dependem de Win32).
- **Perde os teus jogos** — o dicionário Windows tinha Minecraft e Cyberpunk
  com caminhos `D:\SteamLibrary`. No Linux ficam de fora; tenta o Lutris
  ou o Heroic e depois ajusta o `target`.
- **Wayland** limita a visão a janelas X11.
- **`abrir_pasta` já não devolve a listagem** ao cérebro. Bug que existia
  também no Windows (`run.py`, o return era ignorado). Não foi corrigido
  aqui para não misturar portagem com correção.
