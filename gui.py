#!/usr/bin/env python3
"""
gui.py - PDF Compressor GUI with drag-and-drop support.
Requires: pip install pikepdf Pillow tkinterdnd2
"""
import os, sys, threading, tkinter as tk
from tkinter import filedialog, ttk
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from compress_pdf import compress_pdf
except ImportError:
    import tkinter.messagebox as mb
    mb.showerror("Missing file", "compress_pdf.py must be in the same folder as gui.py.")
    sys.exit(1)

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

# ── Palette ───────────────────────────────────────────────────────────────────
BG           = "#f0f2f8"
WHITE        = "#ffffff"
BORDER       = "#dde1f0"
SEC_FILES    = "#eef3ff"
SEC_OUT      = "#f0faf4"
SEC_LOG      = "#fdf8f0"
BORDER_FILES = "#c7d4f8"
BORDER_OUT   = "#bbe8cc"
BORDER_LOG   = "#f2dfa8"
BLUE         = "#3b82f6"
BLUE_HOV     = "#2563eb"
BLUE_LT      = "#dbeafe"
BLUE_DROP    = "#bfdbfe"
GREEN        = "#16a34a"
GREEN_LT     = "#dcfce7"
GREEN_HDR    = "#15803d"
AMBER        = "#d97706"
AMBER_LT     = "#fef3c7"
AMBER_HDR    = "#b45309"
RED          = "#dc2626"
RED_LT       = "#fee2e2"
TEXT         = "#1e2235"
SUBTEXT      = "#6b7280"
LABEL_FILE   = "#1d4ed8"
LABEL_OUT    = "#166534"

FONT_H    = ("Segoe UI Semibold", 15)
FONT_SUB  = ("Segoe UI", 9)
FONT_SEC  = ("Segoe UI Semibold", 8)
FONT_UI   = ("Segoe UI", 10)
FONT_SM   = ("Segoe UI", 9)
FONT_BTN  = ("Segoe UI Semibold", 10)
FONT_MONO = ("Consolas", 9)

W, H = 540, 590


class App(TkinterDnD.Tk if HAS_DND else tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Compressor")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._center()
        self.files: list[str] = []
        self.out_dir = tk.StringVar(value="")
        self._build()
        if HAS_DND:
            self._setup_dnd()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - W) // 2
        y = (self.winfo_screenheight() - H) // 2
        self.geometry(f"{W}x{H}+{x}+{y}")

    def _card(self, parent, bg, border):
        return tk.Frame(parent, bg=bg,
                        highlightbackground=border, highlightthickness=1)

    def _section_header(self, card, text, bg, fg):
        tk.Frame(card, bg=fg, height=3).pack(fill="x")
        tk.Label(card, text=text, font=FONT_SEC,
                 bg=bg, fg=fg, padx=10, pady=5).pack(anchor="w")

    def _ghost_btn(self, parent, text, cmd, fg, bg=WHITE):
        return tk.Button(parent, text=text, command=cmd,
                         bg=bg, fg=fg,
                         activebackground=BLUE_LT, activeforeground=BLUE,
                         font=FONT_SM, relief="flat", cursor="hand2",
                         borderwidth=0, padx=8, pady=3)

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self):
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=22, pady=18)

        # Header
        hdr = tk.Frame(outer, bg=BG)
        hdr.pack(fill="x", pady=(0, 12))
        tk.Label(hdr, text="PDF Compressor", font=FONT_H,
                 bg=BG, fg=TEXT).pack(side="left")
        badge = tk.Frame(hdr, bg=BLUE_LT,
                         highlightbackground=BORDER_FILES, highlightthickness=1)
        badge.pack(side="right", pady=4)
        tk.Label(badge, text="UKVCAS  |  max 6 MB", font=("Segoe UI", 8),
                 bg=BLUE_LT, fg=LABEL_FILE, padx=8, pady=3).pack()

        # ── Drop zone / file list ─────────────────────────────────────────────
        files_card = self._card(outer, SEC_FILES, BORDER_FILES)
        files_card.pack(fill="x", pady=(0, 10))
        self._section_header(files_card, "PDF FILES", SEC_FILES, LABEL_FILE)

        # Drop zone frame (shown when list is empty)
        self.drop_zone = tk.Frame(
            files_card, bg=WHITE,
            highlightbackground=BORDER_FILES, highlightthickness=2,
            height=90,
        )
        self.drop_zone.pack(fill="x", padx=10, pady=(0, 4))
        self.drop_zone.pack_propagate(False)

        dz_inner = tk.Frame(self.drop_zone, bg=WHITE)
        dz_inner.place(relx=0.5, rely=0.5, anchor="center")
        self.drop_icon = tk.Label(dz_inner, text="[ + ]", font=("Segoe UI", 18),
                                  bg=WHITE, fg=BORDER_FILES)
        self.drop_icon.pack()
        dnd_hint = "Drag & drop PDFs here" if HAS_DND else "Click '+ Add PDFs' below"
        self.drop_label = tk.Label(dz_inner, text=dnd_hint,
                                   font=FONT_SM, bg=WHITE, fg=SUBTEXT)
        self.drop_label.pack()

        # Listbox (shown once files are added, hidden when empty)
        list_wrap = tk.Frame(files_card, bg=SEC_FILES)
        list_wrap.pack(fill="x", padx=10, pady=(0, 4))
        sb = tk.Scrollbar(list_wrap, orient="vertical")
        self.listbox = tk.Listbox(
            list_wrap, bg=WHITE, fg=TEXT,
            selectbackground=BLUE_LT, selectforeground=BLUE,
            font=FONT_MONO, height=4,
            relief="flat", borderwidth=0,
            highlightbackground=BORDER_FILES, highlightthickness=1,
            activestyle="none", yscrollcommand=sb.set,
        )
        sb.config(command=self.listbox.yview)
        self.listbox.pack(side="left", fill="x", expand=True)
        sb.pack(side="right", fill="y")
        list_wrap.pack_forget()   # hidden until files added
        self.list_wrap = list_wrap

        btn_row = tk.Frame(files_card, bg=SEC_FILES)
        btn_row.pack(fill="x", padx=10, pady=(4, 10))
        self._ghost_btn(btn_row, "+ Add PDFs",      self._add,    LABEL_FILE, SEC_FILES).pack(side="left", padx=(0,6))
        self._ghost_btn(btn_row, "Remove selected", self._remove, SUBTEXT,    SEC_FILES).pack(side="left")
        self._ghost_btn(btn_row, "Clear all",       self._clear,  SUBTEXT,    SEC_FILES).pack(side="right")

        # ── Output folder ─────────────────────────────────────────────────────
        out_card = self._card(outer, SEC_OUT, BORDER_OUT)
        out_card.pack(fill="x", pady=(0, 10))
        self._section_header(out_card, "OUTPUT FOLDER", SEC_OUT, GREEN_HDR)

        out_row = tk.Frame(out_card, bg=SEC_OUT)
        out_row.pack(fill="x", padx=10, pady=(0, 10))
        self.out_entry = tk.Entry(
            out_row, textvariable=self.out_dir,
            font=FONT_UI, bg=WHITE, fg=TEXT,
            insertbackground=TEXT, relief="flat",
            highlightbackground=BORDER_OUT, highlightthickness=1,
        )
        self.out_entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 8))
        self._set_placeholder()
        self._ghost_btn(out_row, "Browse...", self._browse_out, GREEN_HDR, SEC_OUT).pack(side="right")

        # ── Compress button ───────────────────────────────────────────────────
        self.run_btn = tk.Button(
            outer, text="Compress PDFs",
            command=self._start,
            bg=BLUE, fg=WHITE,
            activebackground=BLUE_HOV, activeforeground=WHITE,
            font=FONT_BTN, relief="flat", pady=11,
            cursor="hand2", borderwidth=0,
        )
        self.run_btn.pack(fill="x", pady=(0, 6))

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Blue.Horizontal.TProgressbar",
                        troughcolor=BORDER, background=BLUE,
                        bordercolor=BG, lightcolor=BLUE, darkcolor=BLUE)
        self.progress = ttk.Progressbar(outer, mode="determinate",
                                        style="Blue.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(0, 10))

        # ── Results ───────────────────────────────────────────────────────────
        log_card = self._card(outer, SEC_LOG, BORDER_LOG)
        log_card.pack(fill="both", expand=True)
        self._section_header(log_card, "RESULTS", SEC_LOG, AMBER_HDR)

        self.log = tk.Text(
            log_card, bg=WHITE, fg=TEXT, font=FONT_MONO,
            relief="flat", borderwidth=0,
            highlightthickness=0,
            state="disabled", wrap="word", height=5,
            padx=10, pady=8,
        )
        self.log.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log.tag_config("ok",   foreground=GREEN,  background=GREEN_LT)
        self.log.tag_config("warn", foreground=AMBER,  background=AMBER_LT)
        self.log.tag_config("err",  foreground=RED,    background=RED_LT)
        self.log.tag_config("dim",  foreground=SUBTEXT)
        self.log.tag_config("bold", font=("Consolas", 9, "bold"), foreground=TEXT)

        self._log("Ready. Add your PDFs above and hit Compress.", "dim")

    # ── Drag and drop ─────────────────────────────────────────────────────────
    def _setup_dnd(self):
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind("<<DragEnter>>", self._drag_enter)
        self.drop_zone.dnd_bind("<<DragLeave>>", self._drag_leave)
        self.drop_zone.dnd_bind("<<Drop>>",      self._on_drop)
        # Also allow dropping onto the listbox once files exist
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind("<<Drop>>", self._on_drop)

    def _drag_enter(self, event):
        self.drop_zone.config(bg=BLUE_DROP, highlightbackground=BLUE)
        self.drop_icon.config(bg=BLUE_DROP, fg=BLUE)
        self.drop_label.config(bg=BLUE_DROP, fg=BLUE)
        for w in self.drop_zone.winfo_children():
            w.config(bg=BLUE_DROP)

    def _drag_leave(self, event):
        self.drop_zone.config(bg=WHITE, highlightbackground=BORDER_FILES)
        self.drop_icon.config(bg=WHITE, fg=BORDER_FILES)
        self.drop_label.config(bg=WHITE, fg=SUBTEXT)
        for w in self.drop_zone.winfo_children():
            w.config(bg=WHITE)

    def _on_drop(self, event):
        self._drag_leave(None)
        # tkinterdnd2 returns paths wrapped in {} if they contain spaces
        raw = event.data
        paths = self.tk.splitlist(raw)
        for p in paths:
            p = p.strip()
            if p.lower().endswith(".pdf") and p not in self.files:
                self.files.append(p)
                self.listbox.insert("end", "  " + Path(p).name)
        self._sync_view()

    # ── Placeholder helpers ───────────────────────────────────────────────────
    def _set_placeholder(self):
        self.out_entry.insert(0, "Save next to original files (default)")
        self.out_entry.config(fg=SUBTEXT)
        self.out_entry.bind("<FocusIn>",  self._clear_ph)
        self.out_entry.bind("<FocusOut>", self._restore_ph)

    def _clear_ph(self, _=None):
        if self.out_entry.get() == "Save next to original files (default)":
            self.out_entry.delete(0, "end")
            self.out_entry.config(fg=TEXT)

    def _restore_ph(self, _=None):
        if not self.out_entry.get():
            self.out_entry.insert(0, "Save next to original files (default)")
            self.out_entry.config(fg=SUBTEXT)

    def _get_out_dir(self):
        v = self.out_entry.get()
        if v == "Save next to original files (default)" or not v.strip():
            return None
        return v.strip()

    # ── View sync ────────────────────────────────────────────────────────────
    def _sync_view(self):
        if self.files:
            self.drop_zone.pack_forget()
            self.list_wrap.pack(fill="x", padx=10, pady=(0, 4),
                                before=self.list_wrap.master.winfo_children()[2])
        else:
            self.list_wrap.pack_forget()
            self.drop_zone.pack(fill="x", padx=10, pady=(0, 4))

    # ── Log ───────────────────────────────────────────────────────────────────
    def _log(self, msg, tag=""):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")

    # ── File actions ──────────────────────────────────────────────────────────
    def _add(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.listbox.insert("end", "  " + Path(p).name)
        self._sync_view()

    def _remove(self):
        for i in reversed(self.listbox.curselection()):
            self.listbox.delete(i); self.files.pop(i)
        self._sync_view()

    def _clear(self):
        self.listbox.delete(0, "end"); self.files.clear()
        self._sync_view()

    def _browse_out(self):
        d = filedialog.askdirectory(title="Choose output folder")
        if d:
            self.out_dir.set(d)
            self.out_entry.config(fg=TEXT)

    # ── Compression ───────────────────────────────────────────────────────────
    def _start(self):
        if not self.files:
            self.log.config(state="normal"); self.log.delete("1.0","end")
            self.log.config(state="disabled")
            self._log("No PDFs added yet. Drag files in or click '+ Add PDFs'.", "warn")
            return
        self.run_btn.config(state="disabled", text="Compressing, please wait...")
        self.log.config(state="normal"); self.log.delete("1.0","end")
        self.log.config(state="disabled")
        self.progress.config(maximum=len(self.files), value=0)
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        import io as _io
        out_dir = self._get_out_dir()
        errors  = 0
        for i, inp in enumerate(self.files, 1):
            name = Path(inp).name
            self._log(f"[{i}/{len(self.files)}]  {name}", "bold")
            if out_dir:
                out = os.path.join(out_dir, Path(inp).stem + "_compressed.pdf")
            else:
                out = str(Path(inp).with_stem(Path(inp).stem + "_compressed"))
            old = sys.stdout; sys.stdout = buf = _io.StringIO()
            try:
                stats = compress_pdf(inp, out, jpeg_quality=75, max_dpi=300, max_size_mb=6.0)
                sys.stdout = old
            except Exception as exc:
                sys.stdout = old
                self._log(f"   Error: {exc}", "err")
                errors += 1; self.progress["value"] = i; continue

            out_mb = stats["output_size_kb"] / 1024
            in_mb  = stats["input_size_kb"]  / 1024
            saved  = stats["overall_saving_pct"]
            tag    = "ok" if out_mb <= 6.0 else "warn"
            status = "fits UKVCAS limit" if out_mb <= 6.0 else "exceeds 6 MB!"
            self._log(f"   {in_mb:.2f} MB  ->  {out_mb:.2f} MB  ({saved:.0f}% smaller)  -  {status}", tag)
            self._log(f"   Saved: {out}", "dim")
            self.progress["value"] = i

        total = len(self.files)
        if errors == 0:
            self._log(f"\nAll {total} file(s) compressed successfully.", "ok")
        else:
            self._log(f"\n{total-errors}/{total} files completed. {errors} had errors.", "warn")
        self.after(0, lambda: self.run_btn.config(state="normal", text="Compress PDFs"))


if __name__ == "__main__":
    App().mainloop()
