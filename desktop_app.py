"""Desktop interface for Blog AI Agent; the existing CLI remains available."""
import logging
import os
import queue
import shutil
import sys
import threading
import tkinter as tk
import json
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from dotenv import dotenv_values, set_key, unset_key

ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
EXAMPLE_ENV_FILE = Path(getattr(sys, "_MEIPASS", ROOT)) / ".env.example"


class QueueLogHandler(logging.Handler):
    def __init__(self, messages):
        super().__init__()
        self.messages = messages

    def emit(self, record):
        self.messages.put(self.format(record))


class QueueTextStream:
    """Give console-oriented libraries a writable stream in the windowed app."""
    encoding = "utf-8"

    def __init__(self, messages, prefix=""):
        self.messages = messages
        self.prefix = prefix
        self._buffer = ""

    def write(self, text):
        if not text:
            return 0
        self._buffer += str(text)
        lines = self._buffer.splitlines(keepends=True)
        self._buffer = ""
        for line in lines:
            if line.endswith(("\n", "\r")):
                clean = line.strip()
                if clean:
                    self.messages.put(self.prefix + clean)
            else:
                self._buffer = line
        return len(text)

    def flush(self):
        if self._buffer.strip():
            self.messages.put(self.prefix + self._buffer.strip())
        self._buffer = ""

    def isatty(self):
        return False


class BlogAgentDesktop:
    def __init__(self, root):
        self.root = root
        self.root.title("Blog AI Agent")
        self.root.geometry("900x680")
        self.root.minsize(720, 520)
        self.messages = queue.Queue()
        self.running = False
        self.abort_event = threading.Event()
        package_name = Path(sys.executable).stem.lower() if getattr(sys, "frozen", False) else os.getenv("BLOG_AGENT_EDITION", "social").lower()
        self.edition = "basic" if "basic" in package_name else "video" if "video" in package_name else "social"
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
        ttk.Label(outer, text=f"{self.edition.title()} edition", style="Sub.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Create content and choose what happens after generation.", style="Sub.TLabel").pack(anchor="w", pady=(3, 18))

        source = ttk.LabelFrame(outer, text="Content", padding=12)
        source.pack(fill="x", pady=(0, 12))
        ttk.Label(source, text="Topic (leave blank to use your topics file / topic discovery)").pack(anchor="w")
        self.topic = tk.StringVar()
        ttk.Entry(source, textvariable=self.topic).pack(fill="x", pady=(5, 0))

        options = ttk.LabelFrame(outer, text="Workflow options", padding=12)
        options.pack(fill="x", pady=(0, 12))
        self.publish = tk.BooleanVar(value=True)
        self.video = tk.BooleanVar(value=False)
        self.social = tk.BooleanVar(value=False)
        ttk.Checkbutton(options, text="Generate and publish blog post", variable=self.publish).grid(row=0, column=0, sticky="w", padx=(0, 24), pady=3)
        video_option = ttk.Checkbutton(options, text="Generate a YouTube video", variable=self.video)
        video_option.grid(row=1, column=0, sticky="w", padx=(0, 24), pady=3)
        social_option = ttk.Checkbutton(options, text="Generate social media posts", variable=self.social)
        social_option.grid(row=2, column=0, sticky="w", padx=(0, 24), pady=3)
        if self.edition not in ("video", "social"):
            video_option.configure(state="disabled")
        if self.edition != "social":
            social_option.configure(state="disabled")

        controls = ttk.Frame(outer)
        controls.pack(fill="x", pady=(0, 8))
        self.run_button = ttk.Button(controls, text="Generate", style="Run.TButton", command=self._run)
        self.run_button.pack(side="left")
        self.abort_button = ttk.Button(controls, text="Abort", command=self._abort, state="disabled")
        self.abort_button.pack(side="left", padx=(8, 0))
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
        self.abort_event.clear()
        self.run_button.configure(state="disabled")
        self.abort_button.configure(state="normal")
        self._append("\n--- Starting workflow ---")
        options = {
            "topic": self.topic.get().strip(),
            "blog": self.publish.get(),
            "video": self.video.get() and self.edition in ("video", "social"),
            "social": self.social.get() and self.edition == "social",
        }
        threading.Thread(target=self._execute, args=(options,), daemon=True).start()

    def _abort(self):
        if self.running:
            self.abort_event.set()
            self.abort_button.configure(state="disabled")
            self._append("Abort requested; the current API or rendering step will finish before stopping.")

    def _execute(self, options):
        handler = QueueLogHandler(self.messages)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s  %(message)s", "%H:%M:%S"))
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = QueueTextStream(self.messages)
        sys.stderr = QueueTextStream(self.messages, "[stderr] ")
        try:
            if not options["blog"] and options["video"]:
                from config import config
                from youtube_video_generator import YouTubeVideoGenerator
                title = options["topic"]
                if not title:
                    raise ValueError("Enter a title or topic to generate a video.")
                self.messages.put("Generating a video directly from the entered title; blog generation is skipped.")
                video_result = YouTubeVideoGenerator().generate_video(
                    blog_title=title,
                    blog_content=f"Create an educational explainer about this topic: {title}",
                    output_filename=f"{title[:50].replace(' ', '_')}_video.mp4",
                    abort_event=self.abort_event,
                    channel_name=config.youtube_channel_name,
                    channel_url=config.youtube_channel_url,
                )
                self.messages.put(f"Video created: {video_result.get('video_path')}")
                return
            if not options["blog"] and options["social"]:
                raise ValueError("Social posts need a generated blog post. Select the blog option or turn social generation off.")
            if not options["blog"]:
                raise ValueError("Select at least one enabled output.")
            from blog_agent import BlogAIAgent
            agent = BlogAIAgent(abort_event=self.abort_event)
            # Product generation is deliberately disabled in these app editions.
            agent.gumroad_client.enabled = False
            if options["topic"]:
                result = agent.create_from_topic(options["topic"], True, options["video"], True, True, options["social"])
            else:
                from config import config
                result = agent.run_full_workflow(num_topics=1, generate_images=True, generate_youtube_video=options["video"], publish_immediately=True, topics_file=config.topics_file_path, publish_post=True, generate_social_media=options["social"])
            self.messages.put(f"Workflow finished: {result.get('status', 'completed') if isinstance(result, dict) else 'completed'}")
            self.messages.put(str(result))
        except InterruptedError as exc:
            self.messages.put(f"Generation aborted: {exc}")
        except Exception:
            logging.getLogger(__name__).exception("Workflow failed")
        finally:
            sys.stdout.flush()
            sys.stderr.flush()
            sys.stdout, sys.stderr = old_stdout, old_stderr
            root_logger.removeHandler(handler)
            self.messages.put("--- Run finished ---")
            self.root.after(0, self._finished)

    def _finished(self):
        self.running = False
        self.run_button.configure(state="normal")
        self.abort_button.configure(state="disabled")

    def _settings(self):
        current = dict(dotenv_values(ENV_FILE)) if ENV_FILE.exists() else {}
        example = dict(dotenv_values(EXAMPLE_ENV_FILE))
        keys = list(dict.fromkeys([*example.keys(), *current.keys()]))
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("760x700")
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
            is_secret = any(word in key for word in secret_markers)
            default_value = "" if is_secret else example.get(key, "")
            value = tk.StringVar(value=current.get(key) or default_value)
            entry = ttk.Entry(form, textvariable=value, width=48, show="●" if is_secret else "")
            entry.grid(row=row, column=1, sticky="ew", pady=4)
            vars_by_key[key] = value
        form.columnconfigure(1, weight=1)

        credentials_frame = ttk.LabelFrame(body, text="Blogger OAuth credentials", padding=10)
        credentials_frame.pack(fill="x", pady=(10, 0))
        credentials_dest = ROOT / "data" / "credentials.json"
        credentials_source = tk.StringVar(value=str(credentials_dest) if credentials_dest.exists() else "")
        ttk.Label(credentials_frame, text="Select the OAuth Desktop App JSON from Google Cloud Console.").pack(anchor="w")
        credentials_row = ttk.Frame(credentials_frame)
        credentials_row.pack(fill="x", pady=(5, 0))
        ttk.Entry(credentials_row, textvariable=credentials_source).pack(side="left", fill="x", expand=True)
        def browse_credentials():
            selected = filedialog.askopenfilename(
                parent=win,
                title="Choose Google OAuth credentials.json",
                filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
            )
            if selected:
                credentials_source.set(selected)
        ttk.Button(credentials_row, text="Browse…", command=browse_credentials).pack(side="left", padx=(8, 0))
        ttk.Label(credentials_frame, text=f"Stored at {credentials_dest}", style="Sub.TLabel").pack(anchor="w", pady=(5, 0))

        def save():
            source = credentials_source.get().strip()
            if source:
                source_path = Path(source)
                try:
                    payload = json.loads(source_path.read_text(encoding="utf-8"))
                    oauth_config = payload.get("installed") or payload.get("web")
                    if not oauth_config or not oauth_config.get("client_id") or not oauth_config.get("client_secret"):
                        raise ValueError("This JSON does not look like Google OAuth client credentials.")
                    if source_path.resolve() != credentials_dest.resolve():
                        credentials_dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path, credentials_dest)
                except Exception as exc:
                    messagebox.showerror("Could not save OAuth credentials", str(exc), parent=win)
                    return
            ENV_FILE.touch(exist_ok=True)
            for key, value in vars_by_key.items():
                setting = value.get().strip()
                if setting:
                    set_key(str(ENV_FILE), key, setting)
                    os.environ[key] = setting
                else:
                    unset_key(str(ENV_FILE), key)
                    os.environ.pop(key, None)
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
