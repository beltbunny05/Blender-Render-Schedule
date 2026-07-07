import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
from pathlib import Path
import subprocess
import threading
import datetime
import time
import os
import sys
import ctypes
import re


DEFAULT_BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"


# =========================
# THEME
# =========================

COLORS = {
    "bg": "#0D0E10",
    "card": "#14161A",
    "card_2": "#101215",
    "border": "#23262D",
    "text": "#F3F4F6",
    "muted": "#A6ADB8",
    "accent": "#F5792A",
    "accent_hover": "#D9671D",
    "accent_soft": "#2B1C12",
    "danger": "#B3472D",
    "danger_hover": "#963A24",
    "terminal_bg": "#0A0B0D",
    "terminal_text": "#E8EAF0"
}


# =========================
# HELPERS
# =========================

def resource_path(relative_path):
    """
    Funciona tanto em .py quanto em .exe gerado pelo PyInstaller.
    """
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).parent

    return base_path / relative_path


def get_ui_font():
    return "Segoe UI Variable"


def clean_path(path):
    return path.strip().strip('"').strip("'")


def normalize_time_input(value):
    """
    Aceita:
    1648 -> 16:48
    930  -> 09:30
    8    -> 08:00
    16:48 -> 16:48
    """
    value = value.strip()

    if value == "":
        return ""

    value = value.replace(" ", "")

    if ":" in value:
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError("Formato inválido.")

        hour = int(parts[0])
        minute = int(parts[1])

    else:
        if not value.isdigit():
            raise ValueError("Digite apenas números ou HH:MM.")

        if len(value) in [1, 2]:
            hour = int(value)
            minute = 0
        elif len(value) == 3:
            hour = int(value[0])
            minute = int(value[1:])
        elif len(value) == 4:
            hour = int(value[:2])
            minute = int(value[2:])
        else:
            raise ValueError("Use algo como 1648, 930, 8 ou 16:48.")

    if not 0 <= hour <= 23:
        raise ValueError("Hora inválida. Use 00 a 23.")

    if not 0 <= minute <= 59:
        raise ValueError("Minuto inválido. Use 00 a 59.")

    return f"{hour:02d}:{minute:02d}"


def apply_windows_modern_effect(window):
    """
    Aplica dark title bar e tenta usar Mica no Windows 11.
    """
    if os.name != "nt":
        return

    try:
        window.update_idletasks()
        hwnd = window.winfo_id()

        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            20,
            ctypes.byref(value),
            ctypes.sizeof(value)
        )

        backdrop_type = ctypes.c_int(2)  # 2 = Mica
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            38,
            ctypes.byref(backdrop_type),
            ctypes.sizeof(backdrop_type)
        )
    except Exception:
        pass


def get_subprocess_kwargs():
    """
    Impede terminal flutuante no Windows.
    """
    if os.name != "nt":
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    return {
        "creationflags": subprocess.CREATE_NO_WINDOW,
        "startupinfo": startupinfo
    }


# =========================
# APP
# =========================

class BlenderRenderQueueApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")

        self.title("Blender Render Queue")
        self.geometry("1240x800")
        self.minsize(1050, 700)
        self.configure(fg_color=COLORS["bg"])

        self.blend_files = []
        self.is_rendering = False
        self.current_process = None

        self.current_blend_file = None
        self.current_scene_name = None
        self.current_render_output_folder = None
        self.last_render_output_folder = None
        self.output_folder_cache = {}

        self.render_all_scenes_var = tk.BooleanVar(value=False)
        self.shutdown_after_finish_var = tk.BooleanVar(value=False)

        self.setup_icon()
        self.create_ui()

        self.after(200, lambda: apply_windows_modern_effect(self))

    # =========================
    # ICON
    # =========================

    def setup_icon(self):
        """
        Coloque blender.ico na mesma pasta do script.
        """
        try:
            ico_path = resource_path("blender.ico")
            if ico_path.exists():
                self.iconbitmap(str(ico_path))
        except Exception:
            pass

    # =========================
    # UI HELPERS
    # =========================

    def safe_ui(self, func, *args, **kwargs):
        self.after(0, lambda: func(*args, **kwargs))

    def set_status(self, text):
        self.status_label.configure(text=text)

    def log(self, text):
        self.safe_ui(self._log, text)

    def _log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def update_queue_box(self):
        self.queue_box.configure(state="normal")
        self.queue_box.delete("1.0", "end")

        if not self.blend_files:
            self.queue_box.insert("end", "Nenhum arquivo na fila.")
        else:
            for i, file in enumerate(self.blend_files, start=1):
                marker = "▶ " if file == self.current_blend_file else "   "
                self.queue_box.insert("end", f"{marker}{i:02d}. {file}\n")

                if file == self.current_blend_file and self.current_scene_name:
                    self.queue_box.insert("end", f"      Cena atual: {self.current_scene_name}\n")

        self.queue_box.configure(state="disabled")
        self.count_label.configure(text=f"{len(self.blend_files)} arquivo(s) na fila")

    def format_time_on_focus_out(self, event=None):
        self.try_format_time(show_error=False)

    def format_time_on_enter(self, event=None):
        self.try_format_time(show_error=True)

    def try_format_time(self, show_error=True):
        value = self.time_entry.get().strip()

        if value == "":
            return True

        try:
            normalized = normalize_time_input(value)
            self.time_entry.delete(0, "end")
            self.time_entry.insert(0, normalized)
            return True
        except ValueError as error:
            if show_error:
                messagebox.showerror("Horário inválido", str(error))
            return False

    # =========================
    # UI
    # =========================

    def create_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        font_name = get_ui_font()

        # HEADER
        header = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"]
        )
        header.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Blender Render Queue",
            font=ctk.CTkFont(family=font_name, size=28, weight="bold"),
            text_color=COLORS["text"]
        ).grid(row=0, column=0, padx=22, pady=(18, 4), sticky="w")

        ctk.CTkLabel(
            header,
            text="Fila de render moderna para múltiplos arquivos .blend e múltiplas cenas",
            font=ctk.CTkFont(family=font_name, size=13),
            text_color=COLORS["muted"]
        ).grid(row=1, column=0, padx=24, pady=(0, 18), sticky="w")

        # TOP AREA
        top_area = ctk.CTkFrame(self, fg_color="transparent")
        top_area.grid(row=1, column=0, padx=18, pady=8, sticky="ew")
        top_area.grid_columnconfigure(0, weight=3)
        top_area.grid_columnconfigure(1, weight=2)

        # BLENDER PATH CARD
        path_card = ctk.CTkFrame(
            top_area,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"]
        )
        path_card.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        path_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            path_card,
            text="Blender executable",
            font=ctk.CTkFont(family=font_name, size=14, weight="bold"),
            text_color=COLORS["text"]
        ).grid(row=0, column=0, columnspan=2, padx=18, pady=(18, 8), sticky="w")

        self.blender_entry = ctk.CTkEntry(
            path_card,
            height=40,
            corner_radius=12,
            fg_color=COLORS["card_2"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13)
        )
        self.blender_entry.insert(0, DEFAULT_BLENDER_PATH)
        self.blender_entry.grid(row=1, column=0, padx=(18, 10), pady=(0, 18), sticky="ew")

        ctk.CTkButton(
            path_card,
            text="Procurar",
            height=40,
            corner_radius=12,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.select_blender
        ).grid(row=1, column=1, padx=(0, 18), pady=(0, 18))

        # SCHEDULE CARD
        schedule_card = ctk.CTkFrame(
            top_area,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"]
        )
        schedule_card.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        schedule_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            schedule_card,
            text="Horário de início",
            font=ctk.CTkFont(family=font_name, size=14, weight="bold"),
            text_color=COLORS["text"]
        ).grid(row=0, column=0, padx=18, pady=(18, 8), sticky="w")

        self.time_entry = ctk.CTkEntry(
            schedule_card,
            height=40,
            corner_radius=12,
            placeholder_text="Ex: 1648, 930 ou 16:48",
            fg_color=COLORS["card_2"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13)
        )
        self.time_entry.grid(row=1, column=0, padx=18, pady=(0, 10), sticky="ew")
        self.time_entry.bind("<FocusOut>", self.format_time_on_focus_out)
        self.time_entry.bind("<Return>", self.format_time_on_enter)

        ctk.CTkLabel(
            schedule_card,
            text="Use Renderizar agora para ignorar o horário.",
            font=ctk.CTkFont(family=font_name, size=12),
            text_color=COLORS["muted"]
        ).grid(row=2, column=0, padx=18, pady=(0, 18), sticky="w")

        # ACTIONS
        actions = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"]
        )
        actions.grid(row=2, column=0, padx=18, pady=8, sticky="ew")

        ctk.CTkButton(
            actions,
            text="Adicionar arquivos",
            height=40,
            corner_radius=12,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.add_blend_files
        ).grid(row=0, column=0, padx=(18, 8), pady=(18, 8))

        ctk.CTkButton(
            actions,
            text="Adicionar pasta",
            height=40,
            corner_radius=12,
            fg_color=COLORS["accent_soft"],
            hover_color="#3A2417",
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.add_blend_folder
        ).grid(row=0, column=1, padx=8, pady=(18, 8))

        ctk.CTkButton(
            actions,
            text="Limpar fila",
            height=40,
            corner_radius=12,
            fg_color="#262A30",
            hover_color="#2E333A",
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.clear_queue
        ).grid(row=0, column=2, padx=8, pady=(18, 8))

        ctk.CTkButton(
            actions,
            text="Iniciar agendado",
            height=40,
            corner_radius=12,
            fg_color="#D06A24",
            hover_color="#B95C1D",
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.start_scheduled_render_thread
        ).grid(row=0, column=3, padx=(20, 8), pady=(18, 8))

        ctk.CTkButton(
            actions,
            text="Renderizar agora",
            height=40,
            corner_radius=12,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.start_now_render_thread
        ).grid(row=0, column=4, padx=8, pady=(18, 8))

        ctk.CTkButton(
            actions,
            text="Parar render",
            height=40,
            corner_radius=12,
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.stop_render
        ).grid(row=0, column=5, padx=(8, 18), pady=(18, 8))

        self.render_all_scenes_checkbox = ctk.CTkCheckBox(
            actions,
            text="Renderizar todas as cenas do .blend",
            variable=self.render_all_scenes_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            checkmark_color="#FFFFFF",
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13)
        )
        self.render_all_scenes_checkbox.grid(row=1, column=0, columnspan=2, padx=(18, 8), pady=(8, 18), sticky="w")

        self.shutdown_checkbox = ctk.CTkCheckBox(
            actions,
            text="Desligar PC ao finalizar",
            variable=self.shutdown_after_finish_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            checkmark_color="#FFFFFF",
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13)
        )
        self.shutdown_checkbox.grid(row=1, column=2, padx=8, pady=(8, 18), sticky="w")

        ctk.CTkButton(
            actions,
            text="Abrir local do render atual",
            height=38,
            corner_radius=12,
            fg_color=COLORS["accent_soft"],
            hover_color="#3A2417",
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.open_current_render_location
        ).grid(row=1, column=3, padx=(20, 8), pady=(8, 18), sticky="ew")

        ctk.CTkButton(
            actions,
            text="Cancelar shutdown",
            height=38,
            corner_radius=12,
            fg_color="#262A30",
            hover_color="#2E333A",
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.cancel_shutdown
        ).grid(row=1, column=4, padx=8, pady=(8, 18), sticky="ew")

        # CONTENT
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=3, column=0, padx=18, pady=8, sticky="nsew")
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=3)
        content.grid_rowconfigure(0, weight=1)

        # QUEUE CARD
        queue_card = ctk.CTkFrame(
            content,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"]
        )
        queue_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        queue_card.grid_rowconfigure(2, weight=1)
        queue_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            queue_card,
            text="Fila de arquivos",
            font=ctk.CTkFont(family=font_name, size=16, weight="bold"),
            text_color=COLORS["text"]
        ).grid(row=0, column=0, padx=18, pady=(18, 4), sticky="w")

        self.count_label = ctk.CTkLabel(
            queue_card,
            text="0 arquivo(s) na fila",
            font=ctk.CTkFont(family=font_name, size=12),
            text_color=COLORS["muted"]
        )
        self.count_label.grid(row=1, column=0, padx=18, pady=(0, 8), sticky="w")

        self.queue_box = ctk.CTkTextbox(
            queue_card,
            corner_radius=14,
            fg_color=COLORS["card_2"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13),
            wrap="none"
        )
        self.queue_box.grid(row=2, column=0, padx=18, pady=(0, 18), sticky="nsew")
        self.queue_box.configure(state="disabled")

        # LOG CARD
        log_card = ctk.CTkFrame(
            content,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"]
        )
        log_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        log_card.grid_rowconfigure(1, weight=1)
        log_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_card,
            text="Terminal integrado",
            font=ctk.CTkFont(family=font_name, size=16, weight="bold"),
            text_color=COLORS["text"]
        ).grid(row=0, column=0, padx=18, pady=(18, 8), sticky="w")

        self.log_box = ctk.CTkTextbox(
            log_card,
            corner_radius=14,
            fg_color=COLORS["terminal_bg"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["terminal_text"],
            font=ctk.CTkFont(family="Cascadia Mono", size=12),
            wrap="none"
        )
        self.log_box.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        self.log_box.configure(state="disabled")

        # FOOTER
        footer = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"]
        )
        footer.grid(row=4, column=0, padx=18, pady=(8, 18), sticky="ew")
        footer.grid_columnconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(
            footer,
            text="Pronto.",
            font=ctk.CTkFont(family=font_name, size=13),
            text_color=COLORS["muted"]
        )
        self.status_label.grid(row=0, column=0, padx=18, pady=14, sticky="w")

        self.progress = ctk.CTkProgressBar(
            footer,
            fg_color="#262A30",
            progress_color=COLORS["accent"],
            corner_radius=100
        )
        self.progress.set(0)
        self.progress.grid(row=0, column=1, padx=18, pady=14, sticky="ew")

        self.update_queue_box()

    # =========================
    # FILE ACTIONS
    # =========================

    def select_blender(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o blender.exe",
            filetypes=[
                ("Executável do Blender", "blender.exe"),
                ("Executáveis", "*.exe"),
                ("Todos os arquivos", "*.*")
            ]
        )

        if file_path:
            self.blender_entry.delete(0, "end")
            self.blender_entry.insert(0, file_path)

    def add_blend_files(self):
        files = filedialog.askopenfilenames(
            title="Selecione arquivos .blend",
            filetypes=[
                ("Blender Files", "*.blend *.blend1"),
                ("Todos os arquivos", "*.*")
            ]
        )

        for file in files:
            path = Path(file).resolve()
            if path not in self.blend_files:
                self.blend_files.append(path)

        self.update_queue_box()

    def add_blend_folder(self):
        folder = filedialog.askdirectory(
            title="Selecione uma pasta com arquivos .blend"
        )

        if not folder:
            return

        folder_path = Path(folder)

        blend_files = list(folder_path.glob("*.blend"))
        blend_files += list(folder_path.glob("*.blend1"))

        for file in blend_files:
            path = file.resolve()
            if path not in self.blend_files:
                self.blend_files.append(path)

        self.update_queue_box()

    def clear_queue(self):
        if self.is_rendering:
            messagebox.showwarning(
                "Render em andamento",
                "Não é possível limpar a fila durante o render."
            )
            return

        self.blend_files.clear()
        self.current_blend_file = None
        self.current_scene_name = None
        self.current_render_output_folder = None
        self.last_render_output_folder = None
        self.update_queue_box()
        self.log("Fila limpa.")

    # =========================
    # VALIDATION
    # =========================

    def validate_inputs(self, require_time):
        blender_path = clean_path(self.blender_entry.get())

        if not os.path.isfile(blender_path):
            messagebox.showerror("Erro", "Caminho do Blender inválido.")
            return None

        if not self.blend_files:
            messagebox.showerror("Erro", "Nenhum arquivo .blend foi adicionado.")
            return None

        if require_time:
            if not self.try_format_time(show_error=True):
                return None

            target_time = self.time_entry.get().strip()
        else:
            target_time = ""

        return blender_path, target_time

    # =========================
    # RENDER START BUTTONS
    # =========================

    def start_scheduled_render_thread(self):
        self.start_render_thread(require_time=True)

    def start_now_render_thread(self):
        self.start_render_thread(require_time=False)

    def start_render_thread(self, require_time):
        if self.is_rendering:
            messagebox.showwarning(
                "Render em andamento",
                "A fila já está renderizando."
            )
            return

        data = self.validate_inputs(require_time=require_time)
        if data is None:
            return

        blender_path, target_time = data

        render_all_scenes = bool(self.render_all_scenes_var.get())
        shutdown_after_finish = bool(self.shutdown_after_finish_var.get())

        self.clear_log()

        thread = threading.Thread(
            target=self.render_queue,
            args=(blender_path, target_time, render_all_scenes, shutdown_after_finish),
            daemon=True
        )
        thread.start()

    # =========================
    # MULTI-SCENE SUPPORT
    # =========================

    def get_scene_names_from_blend(self, blender_path, blend_file):
        python_expr = (
            "import bpy\n"
            "for scene in bpy.data.scenes:\n"
            "    print('__BRENDER_SCENE__' + scene.name)\n"
        )

        command = [
            blender_path,
            "-b",
            str(blend_file),
            "--python-expr",
            python_expr
        ]

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
                **get_subprocess_kwargs()
            )

            scenes = []

            for line in result.stdout.splitlines():
                if line.startswith("__BRENDER_SCENE__"):
                    scene_name = line.replace("__BRENDER_SCENE__", "").strip()
                    if scene_name:
                        scenes.append(scene_name)

            return scenes

        except Exception as error:
            self.log(f"Erro ao ler cenas de {blend_file.name}: {error}")
            return []

    def build_render_jobs(self, blender_path, render_all_scenes):
        """
        Retorna lista de jobs:
        {
            "blend_file": Path,
            "scene_name": str ou None
        }
        """
        jobs = []

        if not render_all_scenes:
            for blend_file in self.blend_files:
                jobs.append({
                    "blend_file": blend_file,
                    "scene_name": None
                })

            return jobs

        self.log("")
        self.log("Modo multi-cenas ativado.")
        self.log("Lendo cenas dos arquivos .blend...")
        self.log("")

        for blend_file in self.blend_files:
            if not self.is_rendering:
                break

            self.safe_ui(self.set_status, f"Lendo cenas: {blend_file.name}")
            self.log(f"Lendo cenas de: {blend_file.name}")

            scenes = self.get_scene_names_from_blend(blender_path, blend_file)

            if not scenes:
                self.log("Nenhuma cena encontrada. Renderizando cena ativa/salva do arquivo.")
                jobs.append({
                    "blend_file": blend_file,
                    "scene_name": None
                })
                continue

            for scene_name in scenes:
                self.log(f"  Cena encontrada: {scene_name}")
                jobs.append({
                    "blend_file": blend_file,
                    "scene_name": scene_name
                })

        self.log("")
        self.log(f"Total de jobs de render: {len(jobs)}")
        return jobs

    # =========================
    # RENDER LOCATION
    # =========================

    def extract_output_folder_from_blender_line(self, line):
        extensions = r"(png|jpg|jpeg|exr|tif|tiff|bmp|webp|mp4|avi|mov|mkv)"

        quoted_match = re.search(
            rf"[\"']([^\"']+\.{extensions})[\"']",
            line,
            flags=re.IGNORECASE
        )

        if quoted_match:
            file_path = Path(quoted_match.group(1))
            return file_path.parent

        drive_match = re.search(
            rf"([A-Za-z]:\\.*?\.{extensions})",
            line,
            flags=re.IGNORECASE
        )

        if drive_match:
            file_path = Path(drive_match.group(1))
            return file_path.parent

        return None

    def get_render_output_folder_from_blender(self, blender_path, blend_file, scene_name=None):
        scene_repr = repr(scene_name or "")

        python_expr = f"""
import bpy, os
scene_name = {scene_repr}

if scene_name:
    scene = bpy.data.scenes.get(scene_name)
else:
    scene = bpy.context.scene

if scene is None:
    scene = bpy.context.scene

p = bpy.path.abspath(scene.render.filepath)

if not p:
    p = bpy.path.abspath('//')

if p.endswith('/') or p.endswith('\\\\'):
    folder = p
else:
    folder = os.path.dirname(p)

print('__BRENDER_OUTPUT__' + folder)
"""

        command = [
            blender_path,
            "-b",
            str(blend_file),
            "--python-expr",
            python_expr
        ]

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
                **get_subprocess_kwargs()
            )

            for line in result.stdout.splitlines():
                if line.startswith("__BRENDER_OUTPUT__"):
                    folder = line.replace("__BRENDER_OUTPUT__", "").strip()
                    if folder:
                        return Path(folder)

        except Exception as error:
            self.log(f"Erro ao descobrir local de render: {error}")

        return None

    def open_folder(self, folder):
        folder = Path(folder)

        try:
            folder.mkdir(parents=True, exist_ok=True)

            if os.name == "nt":
                os.startfile(str(folder))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])

        except Exception as error:
            self.safe_ui(
                messagebox.showerror,
                "Erro",
                f"Não foi possível abrir a pasta:\n{folder}\n\n{error}"
            )

    def open_current_render_location(self):
        if not self.current_blend_file:
            messagebox.showinfo(
                "Nenhum render atual",
                "Ainda não existe um arquivo atual em renderização."
            )
            return

        if self.current_render_output_folder:
            self.open_folder(self.current_render_output_folder)
            return

        cache_key = self.get_output_cache_key(self.current_blend_file, self.current_scene_name)
        cached = self.output_folder_cache.get(cache_key)

        if cached:
            self.open_folder(cached)
            return

        blender_path = clean_path(self.blender_entry.get())

        if not os.path.isfile(blender_path):
            messagebox.showerror("Erro", "Caminho do Blender inválido.")
            return

        self.log("Descobrindo local de render configurado no arquivo atual...")

        thread = threading.Thread(
            target=self.resolve_and_open_current_render_location,
            args=(blender_path, self.current_blend_file, self.current_scene_name),
            daemon=True
        )
        thread.start()

    def resolve_and_open_current_render_location(self, blender_path, blend_file, scene_name):
        folder = self.get_render_output_folder_from_blender(
            blender_path,
            blend_file,
            scene_name
        )

        if folder:
            self.current_render_output_folder = folder
            self.last_render_output_folder = folder
            self.output_folder_cache[self.get_output_cache_key(blend_file, scene_name)] = folder

            self.log(f"Local de render encontrado: {folder}")
            self.open_folder(folder)
        else:
            self.safe_ui(
                messagebox.showwarning,
                "Local não encontrado",
                "Não consegui descobrir o local de render desse arquivo."
            )

    def get_output_cache_key(self, blend_file, scene_name=None):
        return f"{str(blend_file)}::{scene_name or '__ACTIVE_SCENE__'}"

    # =========================
    # SHUTDOWN
    # =========================

    def schedule_shutdown(self):
        if os.name != "nt":
            self.log("Shutdown automático só foi configurado para Windows nesta versão.")
            return

        try:
            command = [
                "shutdown",
                "/s",
                "/t",
                "60",
                "/c",
                "BRender finalizou todos os renders. O computador será desligado em 60 segundos."
            ]

            subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                **get_subprocess_kwargs()
            )

            self.log("")
            self.log("Shutdown agendado: o computador será desligado em 60 segundos.")
            self.log("Use o botão 'Cancelar shutdown' para abortar.")
            self.safe_ui(self.set_status, "Shutdown agendado em 60 segundos.")

        except Exception as error:
            self.log(f"Erro ao agendar shutdown: {error}")

    def cancel_shutdown(self):
        if os.name != "nt":
            self.log("Cancelar shutdown automático só foi configurado para Windows nesta versão.")
            return

        try:
            subprocess.Popen(
                ["shutdown", "/a"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                **get_subprocess_kwargs()
            )

            self.log("Comando enviado: shutdown cancelado.")
            self.set_status("Shutdown cancelado.")

        except Exception as error:
            self.log(f"Erro ao cancelar shutdown: {error}")

    # =========================
    # RENDER CONTROL
    # =========================

    def wait_until_target_time(self, target_time):
        if not target_time:
            self.log("Render imediato selecionado.")
            return True

        now = datetime.datetime.now()
        target_hour, target_minute = map(int, target_time.split(":"))

        target_datetime = now.replace(
            hour=target_hour,
            minute=target_minute,
            second=0,
            microsecond=0
        )

        if target_datetime <= now:
            target_datetime += datetime.timedelta(days=1)

        self.log(f"Render agendado para: {target_datetime.strftime('%d/%m/%Y %H:%M')}")

        while datetime.datetime.now() < target_datetime:
            if not self.is_rendering:
                return False

            remaining = target_datetime - datetime.datetime.now()
            total_seconds = int(remaining.total_seconds())

            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            self.safe_ui(
                self.set_status,
                f"Aguardando início: {hours:02d}:{minutes:02d}:{seconds:02d}"
            )

            time.sleep(1)

        return True

    def render_queue(self, blender_path, target_time, render_all_scenes, shutdown_after_finish):
        self.is_rendering = True
        interrupted = False

        self.safe_ui(self.progress.set, 0)
        self.safe_ui(self.set_status, "Fila iniciada.")

        self.log("==========================================")
        self.log("Fila de render iniciada.")
        self.log("==========================================")

        can_start = self.wait_until_target_time(target_time)

        if not can_start:
            self.log("Render cancelado antes do início.")
            self.safe_ui(self.set_status, "Render cancelado.")
            self.is_rendering = False
            return

        jobs = self.build_render_jobs(blender_path, render_all_scenes)

        if not jobs:
            self.log("Nenhum job de render foi criado.")
            self.safe_ui(self.set_status, "Nenhum job de render.")
            self.is_rendering = False
            return

        total = len(jobs)

        for index, job in enumerate(jobs, start=1):
            if not self.is_rendering:
                self.log("Fila interrompida pelo usuário.")
                interrupted = True
                break

            blend_file = job["blend_file"]
            scene_name = job["scene_name"]

            self.current_blend_file = blend_file
            self.current_scene_name = scene_name

            cache_key = self.get_output_cache_key(blend_file, scene_name)
            self.current_render_output_folder = self.output_folder_cache.get(cache_key)

            self.safe_ui(self.update_queue_box)
            self.safe_ui(self.progress.set, (index - 1) / total)

            if scene_name:
                status_text = f"Renderizando {index}/{total}: {blend_file.name} | Cena: {scene_name}"
            else:
                status_text = f"Renderizando {index}/{total}: {blend_file.name}"

            self.safe_ui(self.set_status, status_text)

            self.log("")
            self.log("==========================================")
            self.log(f"Renderizando {index}/{total}")
            self.log(f"Arquivo: {blend_file}")

            if scene_name:
                self.log(f"Cena: {scene_name}")

            self.log("==========================================")

            command = [
                blender_path,
                "-b",
                str(blend_file)
            ]

            if scene_name:
                command.extend(["-S", scene_name])

            command.append("-a")

            self.log("Comando:")
            self.log(" ".join(command))
            self.log("")

            try:
                self.current_process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    **get_subprocess_kwargs()
                )

                for line in self.current_process.stdout:
                    line = line.rstrip()

                    parsed_folder = self.extract_output_folder_from_blender_line(line)
                    if parsed_folder:
                        self.current_render_output_folder = parsed_folder
                        self.last_render_output_folder = parsed_folder
                        self.output_folder_cache[cache_key] = parsed_folder

                    if not self.is_rendering:
                        try:
                            self.current_process.terminate()
                        except Exception:
                            pass

                        self.log("Processo do Blender interrompido.")
                        interrupted = True
                        break

                    self.log(line)

                self.current_process.wait()

                if self.current_process.returncode == 0:
                    self.log("")
                    self.log(f"Render finalizado com sucesso: {blend_file.name}")
                    if scene_name:
                        self.log(f"Cena finalizada: {scene_name}")
                else:
                    self.log("")
                    self.log(f"Erro no render: {blend_file.name}")
                    if scene_name:
                        self.log(f"Cena com erro: {scene_name}")
                    self.log(f"Código de erro: {self.current_process.returncode}")

            except Exception as error:
                self.log(f"Erro ao renderizar {blend_file.name}: {error}")

            finally:
                self.current_process = None

            self.safe_ui(self.progress.set, index / total)

        self.is_rendering = False
        self.current_process = None

        self.safe_ui(self.progress.set, 1)
        self.safe_ui(self.update_queue_box)

        if interrupted:
            self.safe_ui(self.set_status, "Fila interrompida.")
            self.log("")
            self.log("==========================================")
            self.log("Fila interrompida pelo usuário.")
            self.log("==========================================")
            return

        self.safe_ui(self.set_status, "Fila finalizada.")

        self.log("")
        self.log("==========================================")
        self.log("Todos os renders foram processados.")
        self.log("==========================================")

        if shutdown_after_finish:
            self.schedule_shutdown()

    def stop_render(self):
        if not self.is_rendering:
            self.log("Nenhum render em andamento.")
            return

        self.is_rendering = False

        if self.current_process:
            try:
                self.current_process.terminate()
            except Exception:
                pass

        self.set_status("Parando render...")
        self.log("Solicitação de parada enviada.")


if __name__ == "__main__":
    app = BlenderRenderQueueApp()
    app.mainloop()