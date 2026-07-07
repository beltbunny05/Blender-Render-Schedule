import datetime
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

from .config import (
    APP_TITLE,
    COLORS,
    DEFAULT_BLENDER_PATH,
    ICON_FILENAME,
    MIN_WINDOW_SIZE,
    WINDOW_SIZE,
)
from .helpers import (
    apply_windows_modern_effect,
    clean_path,
    get_subprocess_kwargs,
    get_ui_font,
    normalize_time_input,
    resource_path,
)
from .rendering import (
    extract_output_folder_from_blender_line,
    get_scene_names_from_blend,
)


class BlenderRenderQueueApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")

        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(*MIN_WINDOW_SIZE)
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

    def setup_icon(self):
        try:
            ico_path = resource_path(ICON_FILENAME)
            if ico_path.exists():
                self.iconbitmap(str(ico_path))
        except Exception:
            pass

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
            self.queue_box.insert("end", "No files in queue.")
        else:
            for i, file in enumerate(self.blend_files, start=1):
                marker = "-> " if file == self.current_blend_file else "   "
                self.queue_box.insert("end", f"{marker}{i:02d}. {file}\n")

                if file == self.current_blend_file and self.current_scene_name:
                    self.queue_box.insert("end", f"      Current scene: {self.current_scene_name}\n")

        self.queue_box.configure(state="disabled")
        self.count_label.configure(text=f"{len(self.blend_files)} file(s) in queue")

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
                messagebox.showerror("Invalid time", str(error))
            return False

    def create_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        font_name = get_ui_font()

        header = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"],
        )
        header.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=APP_TITLE,
            font=ctk.CTkFont(family=font_name, size=28, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, padx=22, pady=(18, 4), sticky="w")

        ctk.CTkLabel(
            header,
            text="A cleaner render queue for multiple .blend files and scenes",
            font=ctk.CTkFont(family=font_name, size=13),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, padx=24, pady=(0, 18), sticky="w")

        top_area = ctk.CTkFrame(self, fg_color="transparent")
        top_area.grid(row=1, column=0, padx=18, pady=8, sticky="ew")
        top_area.grid_columnconfigure(0, weight=3)
        top_area.grid_columnconfigure(1, weight=2)

        path_card = ctk.CTkFrame(
            top_area,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"],
        )
        path_card.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        path_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            path_card,
            text="Blender executable",
            font=ctk.CTkFont(family=font_name, size=14, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, columnspan=2, padx=18, pady=(18, 8), sticky="w")

        self.blender_entry = ctk.CTkEntry(
            path_card,
            height=40,
            corner_radius=12,
            fg_color=COLORS["card_2"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13),
        )
        self.blender_entry.insert(0, DEFAULT_BLENDER_PATH)
        self.blender_entry.grid(row=1, column=0, padx=(18, 10), pady=(0, 18), sticky="ew")

        ctk.CTkButton(
            path_card,
            text="Browse",
            height=40,
            corner_radius=12,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.select_blender,
        ).grid(row=1, column=1, padx=(0, 18), pady=(0, 18))

        schedule_card = ctk.CTkFrame(
            top_area,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"],
        )
        schedule_card.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        schedule_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            schedule_card,
            text="Start time",
            font=ctk.CTkFont(family=font_name, size=14, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, padx=18, pady=(18, 8), sticky="w")

        self.time_entry = ctk.CTkEntry(
            schedule_card,
            height=40,
            corner_radius=12,
            placeholder_text="Ex: 1648, 930, or 16:48",
            fg_color=COLORS["card_2"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13),
        )
        self.time_entry.grid(row=1, column=0, padx=18, pady=(0, 10), sticky="ew")
        self.time_entry.bind("<FocusOut>", self.format_time_on_focus_out)
        self.time_entry.bind("<Return>", self.format_time_on_enter)

        ctk.CTkLabel(
            schedule_card,
            text="Use Render Now to ignore the scheduled time.",
            font=ctk.CTkFont(family=font_name, size=12),
            text_color=COLORS["muted"],
        ).grid(row=2, column=0, padx=18, pady=(0, 18), sticky="w")

        actions = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"],
        )
        actions.grid(row=2, column=0, padx=18, pady=8, sticky="ew")
        actions.grid_columnconfigure((0, 1, 2), weight=1)

        self._build_queue_actions(actions, font_name)
        self._build_render_actions(actions, font_name)
        self._build_control_actions(actions, font_name)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=3, column=0, padx=18, pady=8, sticky="nsew")
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=3)
        content.grid_rowconfigure(0, weight=1)

        self._build_queue_card(content, font_name)
        self._build_log_card(content, font_name)
        self._build_footer(font_name)

        self.update_queue_box()

    def _build_queue_actions(self, parent, font_name):
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["card_2"],
            corner_radius=18,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid(row=0, column=0, padx=(18, 10), pady=18, sticky="nsew")
        card.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            card,
            text="1. Build queue",
            font=ctk.CTkFont(family=font_name, size=14, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 4), sticky="w")

        ctk.CTkLabel(
            card,
            text="Add files, review the queue, and open the current .blend location.",
            font=ctk.CTkFont(family=font_name, size=12),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 14), sticky="w")

        ctk.CTkButton(
            card,
            text="Add files",
            height=40,
            corner_radius=12,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.add_blend_files,
        ).grid(row=2, column=0, padx=(16, 8), pady=(0, 8), sticky="ew")

        ctk.CTkButton(
            card,
            text="Add folder",
            height=40,
            corner_radius=12,
            fg_color=COLORS["accent_soft"],
            hover_color="#3A2417",
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.add_blend_folder,
        ).grid(row=2, column=1, padx=(8, 16), pady=(0, 8), sticky="ew")

        ctk.CTkButton(
            card,
            text="Open queue file location",
            height=38,
            corner_radius=12,
            fg_color="#262A30",
            hover_color="#2E333A",
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.open_queue_file_location,
        ).grid(row=3, column=0, padx=(16, 8), pady=(0, 16), sticky="ew")

        ctk.CTkButton(
            card,
            text="Clear queue",
            height=38,
            corner_radius=12,
            fg_color="#262A30",
            hover_color="#2E333A",
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.clear_queue,
        ).grid(row=3, column=1, padx=(8, 16), pady=(0, 16), sticky="ew")

    def _build_render_actions(self, parent, font_name):
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["card_2"],
            corner_radius=18,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid(row=0, column=1, padx=10, pady=18, sticky="nsew")
        card.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            card,
            text="2. Start render",
            font=ctk.CTkFont(family=font_name, size=14, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 4), sticky="w")

        ctk.CTkLabel(
            card,
            text="Choose whether to render now or follow the time set above.",
            font=ctk.CTkFont(family=font_name, size=12),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 14), sticky="w")

        ctk.CTkButton(
            card,
            text="Render now",
            height=42,
            corner_radius=12,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.start_now_render_thread,
        ).grid(row=2, column=0, padx=(16, 8), pady=(0, 8), sticky="ew")

        ctk.CTkButton(
            card,
            text="Start scheduled",
            height=42,
            corner_radius=12,
            fg_color="#D06A24",
            hover_color="#B95C1D",
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.start_scheduled_render_thread,
        ).grid(row=2, column=1, padx=(8, 16), pady=(0, 8), sticky="ew")

        self.render_all_scenes_checkbox = ctk.CTkCheckBox(
            card,
            text="Render all scenes in the .blend",
            variable=self.render_all_scenes_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            checkmark_color="#FFFFFF",
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13),
        )
        self.render_all_scenes_checkbox.grid(row=3, column=0, columnspan=2, padx=16, pady=(4, 16), sticky="w")

    def _build_control_actions(self, parent, font_name):
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["card_2"],
            corner_radius=18,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid(row=0, column=2, padx=(10, 18), pady=18, sticky="nsew")
        card.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            card,
            text="3. Control and power",
            font=ctk.CTkFont(family=font_name, size=14, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 4), sticky="w")

        ctk.CTkLabel(
            card,
            text="Stop the render when needed and manage automatic shutdown.",
            font=ctk.CTkFont(family=font_name, size=12),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 14), sticky="w")

        ctk.CTkButton(
            card,
            text="Stop render",
            height=42,
            corner_radius=12,
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.stop_render,
        ).grid(row=2, column=0, padx=(16, 8), pady=(0, 8), sticky="ew")

        ctk.CTkButton(
            card,
            text="Cancel shutdown",
            height=42,
            corner_radius=12,
            fg_color="#262A30",
            hover_color="#2E333A",
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13, weight="bold"),
            command=self.cancel_shutdown,
        ).grid(row=2, column=1, padx=(8, 16), pady=(0, 8), sticky="ew")

        self.shutdown_checkbox = ctk.CTkCheckBox(
            card,
            text="Shut down PC when finished",
            variable=self.shutdown_after_finish_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            checkmark_color="#FFFFFF",
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=font_name, size=13),
        )
        self.shutdown_checkbox.grid(row=3, column=0, columnspan=2, padx=16, pady=(4, 16), sticky="w")

    def _build_queue_card(self, parent, font_name):
        queue_card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"],
        )
        queue_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        queue_card.grid_rowconfigure(2, weight=1)
        queue_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            queue_card,
            text="File queue",
            font=ctk.CTkFont(family=font_name, size=16, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, padx=18, pady=(18, 4), sticky="w")

        self.count_label = ctk.CTkLabel(
            queue_card,
            text="0 file(s) in queue",
            font=ctk.CTkFont(family=font_name, size=12),
            text_color=COLORS["muted"],
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
            wrap="none",
        )
        self.queue_box.grid(row=2, column=0, padx=18, pady=(0, 18), sticky="nsew")
        self.queue_box.configure(state="disabled")

    def _build_log_card(self, parent, font_name):
        log_card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"],
        )
        log_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        log_card.grid_rowconfigure(1, weight=1)
        log_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_card,
            text="Integrated terminal",
            font=ctk.CTkFont(family=font_name, size=16, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, padx=18, pady=(18, 8), sticky="w")

        self.log_box = ctk.CTkTextbox(
            log_card,
            corner_radius=14,
            fg_color=COLORS["terminal_bg"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["terminal_text"],
            font=ctk.CTkFont(family="Cascadia Mono", size=12),
            wrap="none",
        )
        self.log_box.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        self.log_box.configure(state="disabled")

    def _build_footer(self, font_name):
        footer = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"],
        )
        footer.grid(row=4, column=0, padx=18, pady=(8, 18), sticky="ew")
        footer.grid_columnconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(
            footer,
            text="Ready.",
            font=ctk.CTkFont(family=font_name, size=13),
            text_color=COLORS["muted"],
        )
        self.status_label.grid(row=0, column=0, padx=18, pady=14, sticky="w")

        self.progress = ctk.CTkProgressBar(
            footer,
            fg_color="#262A30",
            progress_color=COLORS["accent"],
            corner_radius=100,
        )
        self.progress.set(0)
        self.progress.grid(row=0, column=1, padx=18, pady=14, sticky="ew")

    def select_blender(self):
        file_path = filedialog.askopenfilename(
            title="Select blender.exe",
            filetypes=[
                ("Blender executable", "blender.exe"),
                ("Executables", "*.exe"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            self.blender_entry.delete(0, "end")
            self.blender_entry.insert(0, file_path)

    def add_blend_files(self):
        files = filedialog.askopenfilenames(
            title="Select .blend files",
            filetypes=[
                ("Blender Files", "*.blend *.blend1"),
                ("All files", "*.*"),
            ],
        )

        for file in files:
            path = Path(file).resolve()
            if path not in self.blend_files:
                self.blend_files.append(path)

        self.update_queue_box()

    def add_blend_folder(self):
        folder = filedialog.askdirectory(title="Select a folder with .blend files")

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
                "Render in progress",
                "You cannot clear the queue while rendering.",
            )
            return

        self.blend_files.clear()
        self.current_blend_file = None
        self.current_scene_name = None
        self.current_render_output_folder = None
        self.last_render_output_folder = None
        self.update_queue_box()
        self.log("Queue cleared.")

    def validate_inputs(self, require_time):
        blender_path = clean_path(self.blender_entry.get())

        if not os.path.isfile(blender_path):
            messagebox.showerror("Error", "Invalid Blender path.")
            return None

        if not self.blend_files:
            messagebox.showerror("Error", "No .blend files were added.")
            return None

        if require_time:
            if not self.try_format_time(show_error=True):
                return None
            target_time = self.time_entry.get().strip()
        else:
            target_time = ""

        return blender_path, target_time

    def start_scheduled_render_thread(self):
        self.start_render_thread(require_time=True)

    def start_now_render_thread(self):
        self.start_render_thread(require_time=False)

    def start_render_thread(self, require_time):
        if self.is_rendering:
            messagebox.showwarning(
                "Render in progress",
                "The queue is already rendering.",
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
            daemon=True,
        )
        thread.start()

    def build_render_jobs(self, blender_path, render_all_scenes):
        jobs = []

        if not render_all_scenes:
            for blend_file in self.blend_files:
                jobs.append({"blend_file": blend_file, "scene_name": None})
            return jobs

        self.log("")
        self.log("Multi-scene mode enabled.")
        self.log("Reading scenes from .blend files...")
        self.log("")

        for blend_file in self.blend_files:
            if not self.is_rendering:
                break

            self.safe_ui(self.set_status, f"Reading scenes: {blend_file.name}")
            self.log(f"Reading scenes from: {blend_file.name}")

            try:
                scenes = get_scene_names_from_blend(blender_path, blend_file)
            except Exception as error:
                self.log(f"Error reading scenes from {blend_file.name}: {error}")
                scenes = []

            if not scenes:
                self.log("No scenes found. Rendering the active/saved scene from the file.")
                jobs.append({"blend_file": blend_file, "scene_name": None})
                continue

            for scene_name in scenes:
                self.log(f"  Scene found: {scene_name}")
                jobs.append({"blend_file": blend_file, "scene_name": scene_name})

        self.log("")
        self.log(f"Total render jobs: {len(jobs)}")
        return jobs

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
                "Error",
                f"Could not open folder:\n{folder}\n\n{error}",
            )

    def get_queue_focus_file(self):
        if self.current_blend_file and self.current_blend_file in self.blend_files:
            return self.current_blend_file
        if self.blend_files:
            return self.blend_files[0]
        return None

    def open_queue_file_location(self):
        target_file = self.get_queue_focus_file()

        if not target_file:
            messagebox.showinfo(
                "Empty queue",
                "Add at least one file to open the queue folder.",
            )
            return

        folder = Path(target_file).parent
        self.log(f"Opening queue file location: {target_file.name}")
        self.set_status(f"Opened location: {target_file.name}")
        self.open_folder(folder)

    def get_output_cache_key(self, blend_file, scene_name=None):
        return f"{str(blend_file)}::{scene_name or '__ACTIVE_SCENE__'}"

    def schedule_shutdown(self):
        if os.name != "nt":
            self.log("Automatic shutdown is only configured for Windows in this version.")
            return

        try:
            command = [
                "shutdown",
                "/s",
                "/t",
                "60",
                "/c",
                "BRender finished all renders. The computer will shut down in 60 seconds.",
            ]

            subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                **get_subprocess_kwargs(),
            )

            self.log("")
            self.log("Shutdown scheduled: the computer will shut down in 60 seconds.")
            self.log("Use the 'Cancel shutdown' button to abort.")
            self.safe_ui(self.set_status, "Shutdown scheduled in 60 seconds.")
        except Exception as error:
            self.log(f"Error scheduling shutdown: {error}")

    def cancel_shutdown(self):
        if os.name != "nt":
            self.log("Canceling automatic shutdown is only configured for Windows in this version.")
            return

        try:
            subprocess.Popen(
                ["shutdown", "/a"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                **get_subprocess_kwargs(),
            )

            self.log("Command sent: shutdown canceled.")
            self.set_status("Shutdown canceled.")
        except Exception as error:
            self.log(f"Error canceling shutdown: {error}")

    def wait_until_target_time(self, target_time):
        if not target_time:
            self.log("Immediate render selected.")
            return True

        now = datetime.datetime.now()
        target_hour, target_minute = map(int, target_time.split(":"))
        target_datetime = now.replace(
            hour=target_hour,
            minute=target_minute,
            second=0,
            microsecond=0,
        )

        if target_datetime <= now:
            target_datetime += datetime.timedelta(days=1)

        self.log(f"Render scheduled for: {target_datetime.strftime('%d/%m/%Y %H:%M')}")

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
                f"Waiting to start: {hours:02d}:{minutes:02d}:{seconds:02d}",
            )

            time.sleep(1)

        return True

    def render_queue(self, blender_path, target_time, render_all_scenes, shutdown_after_finish):
        self.is_rendering = True
        interrupted = False

        self.safe_ui(self.progress.set, 0)
        self.safe_ui(self.set_status, "Queue started.")

        self.log("==========================================")
        self.log("Render queue started.")
        self.log("==========================================")

        can_start = self.wait_until_target_time(target_time)

        if not can_start:
            self.log("Render canceled before start.")
            self.safe_ui(self.set_status, "Render canceled.")
            self.is_rendering = False
            return

        jobs = self.build_render_jobs(blender_path, render_all_scenes)

        if not jobs:
            self.log("No render jobs were created.")
            self.safe_ui(self.set_status, "No render jobs.")
            self.is_rendering = False
            return

        total = len(jobs)

        for index, job in enumerate(jobs, start=1):
            if not self.is_rendering:
                self.log("Queue interrupted by user.")
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
                status_text = f"Rendering {index}/{total}: {blend_file.name} | Scene: {scene_name}"
            else:
                status_text = f"Rendering {index}/{total}: {blend_file.name}"

            self.safe_ui(self.set_status, status_text)
            self.log("")
            self.log("==========================================")
            self.log(f"Rendering {index}/{total}")
            self.log(f"File: {blend_file}")
            if scene_name:
                self.log(f"Scene: {scene_name}")
            self.log("==========================================")

            command = [blender_path, "-b", str(blend_file)]
            if scene_name:
                command.extend(["-S", scene_name])
            command.append("-a")

            self.log("Command:")
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
                    **get_subprocess_kwargs(),
                )

                for line in self.current_process.stdout:
                    line = line.rstrip()

                    parsed_folder = extract_output_folder_from_blender_line(line)
                    if parsed_folder:
                        self.current_render_output_folder = parsed_folder
                        self.last_render_output_folder = parsed_folder
                        self.output_folder_cache[cache_key] = parsed_folder

                    if not self.is_rendering:
                        try:
                            self.current_process.terminate()
                        except Exception:
                            pass

                        self.log("Blender process interrupted.")
                        interrupted = True
                        break

                    self.log(line)

                self.current_process.wait()

                if self.current_process.returncode == 0:
                    self.log("")
                    self.log(f"Render finished successfully: {blend_file.name}")
                    if scene_name:
                        self.log(f"Scene finished: {scene_name}")
                else:
                    self.log("")
                    self.log(f"Render error: {blend_file.name}")
                    if scene_name:
                        self.log(f"Scene with error: {scene_name}")
                    self.log(f"Error code: {self.current_process.returncode}")
            except Exception as error:
                self.log(f"Error rendering {blend_file.name}: {error}")
            finally:
                self.current_process = None

            self.safe_ui(self.progress.set, index / total)

        self.is_rendering = False
        self.current_process = None

        self.safe_ui(self.progress.set, 1)
        self.safe_ui(self.update_queue_box)

        if interrupted:
            self.safe_ui(self.set_status, "Queue interrupted.")
            self.log("")
            self.log("==========================================")
            self.log("Queue interrupted by user.")
            self.log("==========================================")
            return

        self.safe_ui(self.set_status, "Queue finished.")
        self.log("")
        self.log("==========================================")
        self.log("All renders were processed.")
        self.log("==========================================")

        if shutdown_after_finish:
            self.schedule_shutdown()

    def stop_render(self):
        if not self.is_rendering:
            self.log("No render in progress.")
            return

        self.is_rendering = False

        if self.current_process:
            try:
                self.current_process.terminate()
            except Exception:
                pass

        self.set_status("Stopping render...")
        self.log("Stop request sent.")


def main():
    app = BlenderRenderQueueApp()
    app.mainloop()


if __name__ == "__main__":
    main()
