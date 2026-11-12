"""Desktop interface for Blog AI Agent; the existing CLI remains available."""
import logging
import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from dotenv import dotenv_values, set_key

ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
EXAMPLE_ENV_FILE = Path(getattr(sys, "_MEIPASS", ROOT)) / ".env.example"


class QueueLogHandler(logging.Handler):
    def __init__(self, messages):
        super().__init__()
        self.messages = messages

    def emit(self, record):
        self.messages.put(self.format(record))


class BlogAgentDesktop:
    def __init__(self, root):
        self.root = root
        self.root.title("Blog AI Agent")
        self.root.geometry("900x680")
        self.root.minsize(720, 520)
        self.messages = queue.Queue()
        self.running = False
        self._style()
        self._build()
        self.root.after(100, self._drain_logs)

    def _style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Sub.TLabel", foreground="#526174")
        style.configure("Run.TButton", font=("Segoe UI", 10, "bold"), padding=9)

    def _build(self):
        outer = ttk.Frame(self.root, padding=22)
        outer.pack(fill="both", expand=True)
        heading = ttk.Frame(outer)
        heading.pack(fill="x")
        ttk.Label(heading, text="Blog AI Agent", style="Title.TLabel").pack(side="left")
        ttk.Button(heading, text="⚙ Settings", command=self._settings).pack(side="right")
        ttk.Label(outer, text="Create content and choose what happens after generation.", style="Sub.TLabel").pack(anchor="w", pady=(3, 18))

        source = ttk.LabelFrame(outer, text="Content", padding=12)
        source.pack(fill="x", pady=(0, 12))
        ttk.Label(source, text="Topic (leave blank to use your topics file / topic discovery)").pack(anchor="w")
        self.topic = tk.StringVar()
        ttk.Entry(source, textvariable=self.topic).pack(fill="x", pady=(5, 0))

        options = ttk.LabelFrame(outer, text="Workflow options", padding=12)
        options.pack(fill="x", pady=(0, 12))
        self.publish = tk.BooleanVar(value=False)
        self.images = tk.BooleanVar(value=True)
        self.video = tk.BooleanVar(value=False)
        self.social = tk.BooleanVar(value=True)
        self.immediate = tk.BooleanVar(value=False)
        ttk.Checkbutton(options, text="Publish blog post to Blogger", variable=self.publish).grid(row=0, column=0, sticky="w", padx=(0, 24), pady=3)
        ttk.Checkbutton(options, text="Generate relevant images", variable=self.images).grid(row=0, column=1, sticky="w", pady=3)
        ttk.Checkbutton(options, text="Generate a video", variable=self.video).grid(row=1, column=0, sticky="w", padx=(0, 24), pady=3)
        ttk.Checkbutton(options, text="Generate social media posts", variable=self.social).grid(row=1, column=1, sticky="w", pady=3)
        ttk.Checkbutton(options, text="Publish immediately (otherwise save as draft)", variable=self.immediate).grid(row=2, column=0, columnspan=2, sticky="w", pady=3)

        controls = ttk.Frame(outer)
        controls.pack(fill="x", pady=(0, 8))
        self.run_button = ttk.Button(controls, text="Generate blog post", style="Run.TButton", command=self._run)
        self.run_button.pack(side="left")
        ttk.Label(controls, text="Execution progress", style="Sub.TLabel").pack(side="left", padx=14)

        logs = ttk.LabelFrame(outer, text="Run log", padding=8)
        logs.pack(fill="both", expand=True)
        self.log = tk.Text(logs, wrap="word", state="disabled", bg="#101827", fg="#dce6f2", insertbackground="white", font=("Consolas", 9), padx=10, pady=9)
        scrollbar = ttk.Scrollbar(logs, command=self.log.yview)
        self.log.configure(yscrollcommand=scrollbar.set)
        self.log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _append(self, line):
        self.log.configure(state="normal")
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _drain_logs(self):
        while True:
            try:
                self._append(self.messages.get_nowait())
            except queue.Empty:
                break
        self.root.after(100, self._drain_logs)

    def _run(self):
        if self.running:
            return
        self.running = True
        self.run_button.configure(state="disabled")
        self._append("\n--- Starting workflow ---")
        options = {
            "topic": self.topic.get().strip(),
            "images": self.images.get(),
            "video": self.video.get(),
            "publish": self.publish.get(),
            "immediate": self.immediate.get(),
            "social": self.social.get(),
        }
        threading.Thread(target=self._execute, args=(options,), daemon=True).start()

    def _execute(self, options):
        handler = QueueLogHandler(self.messages)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s  %(message)s", "%H:%M:%S"))
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
        try:
            from blog_agent import BlogAIAgent
            agent = BlogAIAgent()
            if options["topic"]:
                result = agent.create_from_topic(options["topic"], options["images"], options["video"], options["immediate"], options["publish"], options["social"])
            else:
                from config import config
                result = agent.run_full_workflow(num_topics=1, generate_images=options["images"], generate_youtube_video=options["video"], publish_immediately=options["immediate"], topics_file=config.topics_file_path, publish_post=options["publish"], generate_social_media=options["social"])
            self.messages.put(f"Workflow finished: {result.get('status', 'completed') if isinstance(result, dict) else 'completed'}")
            self.messages.put(str(result))
        except Exception:
            logging.getLogger(__name__).exception("Workflow failed")
        finally:
            root_logger.removeHandler(handler)
            self.messages.put("--- Run finished ---")
            self.root.after(0, self._finished)

    def _finished(self):
        self.running = False
        self.run_button.configure(state="normal")

    def _settings(self):
        current = dict(dotenv_values(ENV_FILE)) if ENV_FILE.exists() else {}
        example = dict(dotenv_values(EXAMPLE_ENV_FILE))
        keys = list(dict.fromkeys([*example.keys(), *current.keys()]))
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("700x650")
        win.transient(self.root)
        body = ttk.Frame(win, padding=16)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Provider and application settings", font=("Segoe UI", 15, "bold")).pack(anchor="w")
        ttk.Label(body, text=f"Saved locally to {ENV_FILE}. Keep this file private.", style="Sub.TLabel").pack(anchor="w", pady=(3, 12))
        canvas = tk.Canvas(body, highlightthickness=0)
        scroll = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        form = ttk.Frame(canvas)
        form.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=form, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        vars_by_key = {}
        secret_markers = ("KEY", "SECRET", "TOKEN", "PASSWORD")
        for row, key in enumerate(keys):
            ttk.Label(form, text=key.replace("_", " ").title()).grid(row=row, column=0, sticky="w", padx=(0, 14), pady=4)
            value = tk.StringVar(value=current.get(key) or "")
            entry = ttk.Entry(form, textvariable=value, width=48, show="●" if any(word in key for word in secret_markers) else "")
            entry.grid(row=row, column=1, sticky="ew", pady=4)
            vars_by_key[key] = value
        form.columnconfigure(1, weight=1)
        def save():
            ENV_FILE.touch(exist_ok=True)
            for key, value in vars_by_key.items():
                set_key(str(ENV_FILE), key, value.get())
                os.environ[key] = value.get()
            try:
                import config as config_module
                fresh_config = config_module.Config()
                for field in fresh_config.model_fields:
                    setattr(config_module.config, field, getattr(fresh_config, field))
            except Exception:
                pass
            messagebox.showinfo("Settings saved", "Configuration saved to .env.", parent=win)
            win.destroy()
        ttk.Button(body, text="Save settings", command=save).pack(anchor="e", pady=(12, 0))


def main():
    os.chdir(ROOT)
    root = tk.Tk()
    BlogAgentDesktop(root)
    root.mainloop()


if __name__ == "__main__":
    main()
