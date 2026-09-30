import sys
import math
import ctypes
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

try:
    import cv2
    import win32gui
    import win32ui
    import win32con
except ImportError as e:
    sys.exit(
        f"O overlay VTuber e so Windows: falta '{e.name}'.\n"
        "O run.py nunca o arranca no Linux (ver platform_shim.CAPACIDADES)."
    )

import keyboard

import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets

VTUBE_WINDOW_TITLE_PART = "VTube Studio"

# Ajustes principais
FPS = 30
CAPTURE_SCALE = 0.55
BASE_SCALE = 1.06

LOWER_BLUE = np.array([0, 0, 0], dtype=np.uint8)
UPPER_BLUE = np.array([0, 0, 0], dtype=np.uint8)

LOCAL_API_HOST = "127.0.0.1"
LOCAL_API_PORT = 8765


def find_window():
    result = []

    def enum(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if title and VTUBE_WINDOW_TITLE_PART.lower() in title.lower():
            result.append(hwnd)

    win32gui.EnumWindows(enum, None)
    return result[0] if result else None


def capture(hwnd, scale=1.0):
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        full_w, full_h = right - left, bottom - top

        client_rect = win32gui.GetClientRect(hwnd)
        client_w = client_rect[2] - client_rect[0]
        client_h = client_rect[3] - client_rect[1]

        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(mfc_dc, full_w, full_h)
        save_dc.SelectObject(bmp)

        result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)
        if result != 1:
            win32gui.DeleteObject(bmp.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            return None

        bmpinfo = bmp.GetInfo()
        bmpstr = bmp.GetBitmapBits(True)

        img = np.frombuffer(bmpstr, dtype=np.uint8)
        img.shape = (bmpinfo["bmHeight"], bmpinfo["bmWidth"], 4)

        win32gui.DeleteObject(bmp.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)

        img = np.ascontiguousarray(img)

        border_x = max(0, (full_w - client_w) // 2)
        titlebar_h = max(0, full_h - client_h - border_x)

        x1 = border_x
        y1 = titlebar_h
        x2 = x1 + client_w
        y2 = y1 + client_h

        img = img[y1:y2, x1:x2]

        if img.size == 0:
            return None

        bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        if scale != 1.0:
            new_w = max(1, int(bgr.shape[1] * scale))
            new_h = max(1, int(bgr.shape[0] * scale))
            bgr = cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)

        return bgr

    except Exception as e:
        print("Erro no capture:", e)
        return None


class CaptureWorker(QtCore.QThread):
    frame_ready = QtCore.pyqtSignal(QtGui.QPixmap)

    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.running = True

    def run(self):
        target_delay = 1.0 / FPS

        while self.running:
            start_time = time.time()

            hwnd = self.overlay.hwnd
            if not hwnd:
                hwnd = find_window()
                self.overlay.hwnd = hwnd
                time.sleep(0.3)
                continue

            frame = capture(hwnd, CAPTURE_SCALE)
            if frame is not None:
                try:
                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    mask = cv2.inRange(hsv, LOWER_BLUE, UPPER_BLUE)
                    mask = cv2.bitwise_not(mask)

                    rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                    rgba[:, :, 3] = mask

                    h, w, _ = rgba.shape
                    img = QtGui.QImage(
                        rgba.data,
                        w,
                        h,
                        4 * w,
                        QtGui.QImage.Format_RGBA8888
                    ).copy()

                    pix = QtGui.QPixmap.fromImage(img)
                    self.frame_ready.emit(pix)

                except Exception as e:
                    print("Erro processando frame:", e)

            elapsed = time.time() - start_time
            sleep_time = max(0.001, target_delay - elapsed)
            time.sleep(sleep_time)

    def stop(self):
        self.running = False
        self.wait()


class Overlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.Tool
        )

        self.pix = None
        self.hwnd = None
        self.locked = False

        # --- TAMANHO DA JANELA INVISÍVEL ---
        w_inicial, h_inicial = 900, 1300
        self.resize(w_inicial, h_inicial)
        
        # Posicionamento absoluto no eixo X=0 para não ocultar as bordas.
        # Você usará o deslocamento interno no paintEvent.
        desktop = QtWidgets.QApplication.desktop().availableGeometry()
        self.move(0, desktop.height() - h_inicial)
        # ---------------------------------------

        self.anim = QtCore.QTimer(self)
        self.anim.timeout.connect(self.animate)
        self.anim.start(30)

        keyboard.add_hotkey("ctrl+q", lambda: QtCore.QTimer.singleShot(0, self.toggle_click))
        keyboard.add_hotkey("ctrl+r", lambda: QtCore.QTimer.singleShot(0, self.find))
        keyboard.add_hotkey("ctrl+x", lambda: QtCore.QTimer.singleShot(0, self.close))
        keyboard.add_hotkey("f8", lambda: QtCore.QTimer.singleShot(0, self.toggle_lock))
        keyboard.add_hotkey("ctrl+w", lambda: QtCore.QTimer.singleShot(0, self.move_up))
        keyboard.add_hotkey("ctrl+s", lambda: QtCore.QTimer.singleShot(0, self.move_down))
        keyboard.add_hotkey("ctrl+a", lambda: QtCore.QTimer.singleShot(0, self.move_left))
        keyboard.add_hotkey("ctrl+d", lambda: QtCore.QTimer.singleShot(0, self.move_right))
        keyboard.add_hotkey("ctrl+e", lambda: QtCore.QTimer.singleShot(0, self.resize_up))
        keyboard.add_hotkey("ctrl+z", lambda: QtCore.QTimer.singleShot(0, self.resize_down))

        self.capture_worker = CaptureWorker(self)
        self.capture_worker.frame_ready.connect(self.set_frame)
        self.capture_worker.start()

    def showEvent(self, event):
        super().showEvent(event)
        self.apply_window_style()

    def closeEvent(self, event):
        keyboard.unhook_all_hotkeys()
        if hasattr(self, "capture_worker") and self.capture_worker.isRunning():
            self.capture_worker.stop()
        super().closeEvent(event)

    def apply_window_style(self):
        hwnd = int(self.winId())
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        style |= win32con.WS_EX_LAYERED
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)

    def set_frame(self, pix):
        self.pix = pix
        self.update()

    def find(self):
        self.hwnd = find_window()
        if self.hwnd:
            print("Janela encontrada.")
        else:
            print("Janela do VTube Studio não encontrada.")

    def toggle_lock(self):
        self.locked = not self.locked
        estado = "TRAVADA" if self.locked else "DESTRAVADA"
        print(f"[SISTEMA] Posição e Tamanho do Modelo: {estado}")

    def move_up(self):
        if not self.locked: self.move(self.x(), self.y() - 20)

    def move_down(self):
        if not self.locked: self.move(self.x(), self.y() + 20)

    def move_left(self):
        if not self.locked: self.move(self.x() - 20, self.y())

    def move_right(self):
        if not self.locked: self.move(self.x() + 20, self.y())

    def resize_up(self):
        if not self.locked: self.resize(self.width() + 30, self.height() + 30)

    def resize_down(self):
        if not self.locked: self.resize(max(120, self.width() - 30), max(120, self.height() - 30))

    # Mantemos as funções para o run.py não dar erro ao chamar o /speak/start, 
    # mas elas não fazem mais nada visualmente.
    def start_speaking(self):
        pass

    def stop_speaking(self):
        pass

    def animate(self):
        pass # Sem animação

    def paintEvent(self, e):
        if not self.pix:
            return

        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)

        scale = BASE_SCALE

        pix_w = self.pix.width()
        pix_h = self.pix.height()

        fitted = min(self.width() / pix_w, self.height() / pix_h)
        final_scale = fitted * scale

        target_w = int(pix_w * final_scale)
        target_h = int(pix_h * final_scale)

        # 🔥 DESLOCAMENTO INTERNO NA JANELA 🔥
        # Empurra a imagem gerada para a esquerda e para baixo (ex: -150) dentro da janela visível.
        deslocamento_interno_X = -250
        deslocamento_interno_Y = 15

        x = 0 + deslocamento_interno_X
        y = (self.height() - target_h) + deslocamento_interno_Y

        rect = QtCore.QRect(x, y, target_w, target_h)
        p.drawPixmap(rect, self.pix)

    def toggle_click(self):
        hwnd = int(self.winId())
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        style |= win32con.WS_EX_LAYERED
        if style & win32con.WS_EX_TRANSPARENT:
            style &= ~win32con.WS_EX_TRANSPARENT
            print("Click-through desligado")
        else:
            style |= win32con.WS_EX_TRANSPARENT
            print("Click-through ligado")
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)


class API(BaseHTTPRequestHandler):
    overlay = None

    def do_POST(self):
        if self.path == "/speak/start":
            API.overlay.start_speaking()
        elif self.path == "/speak/stop":
            API.overlay.stop_speaking()
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        return


def run_api(overlay):
    API.overlay = overlay
    s = HTTPServer((LOCAL_API_HOST, LOCAL_API_PORT), API)
    threading.Thread(target=s.serve_forever, daemon=True).start()


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = Overlay()
    w.show()

    run_api(w)

    print("🔥 Overlay rodando EXATAMENTE no Canto Inferior Esquerdo (Estático)")
    print("F8 = Travar/Destravar Modelo na Tela")
    print("Ctrl+Q = click-through")
    print("Ctrl+R = reencontrar VTube Studio")
    print("Ctrl+X = fechar")
    print("Ctrl+WASD = mover")
    print("Ctrl+E = aumentar")
    print("Ctrl+Z = diminuir")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()