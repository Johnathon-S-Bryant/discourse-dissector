# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import argparse
import requests
import logging
import trafilatura
from pydantic import BaseModel
import instructor
from ollama import Client
from tavily import TavilyClient
import os
import random
from dotenv import load_dotenv
import threading
import queue
import tkinter as tk
from tkinter import ttk
from urllib.parse import urlparse

load_dotenv()

THEME_BG = "#e8f1f5"
THEME_FG = "#0b3954"
THEME_ACCENT = "#087e8b"
THEME_ACCENT_FG = "#ffffff"
THEME_FIELD_BG = "#ffffff"
THEME_FONT = ("Segoe UI", 10)


def apply_theme(root):
    """Apply the project theme as defaults; per-widget options override these."""
    root.configure(bg=THEME_BG)
    root.option_add("*background", THEME_BG)
    root.option_add("*foreground", THEME_FG)
    root.option_add("*font", THEME_FONT)
    root.option_add("*Entry.background", THEME_FIELD_BG)
    root.option_add("*Text.background", THEME_FIELD_BG)
    root.option_add("*Listbox.background", THEME_FIELD_BG)
    root.option_add("*Button.background", THEME_ACCENT)
    root.option_add("*Button.foreground", THEME_ACCENT_FG)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(
        ".",
        background=THEME_BG,
        foreground=THEME_FG,
        fieldbackground=THEME_FIELD_BG,
        font=THEME_FONT,
    )
    style.configure("Accent.TButton", background=THEME_ACCENT, foreground=THEME_ACCENT_FG)


class Statement(BaseModel):
    text: str


class StatementList(BaseModel):
    statements: list[str]


def validate_article_url(source):
    """Accept article URLs only and reject YouTube links."""
    source = source.strip()
    if source.startswith("www."):
        source = "https://" + source

    parsed = urlparse(source)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Enter a valid article URL.")

    hostname = parsed.hostname.lower().rstrip(".")
    if (
        hostname == "youtu.be"
        or hostname.endswith(".youtu.be")
        or hostname == "youtube.com"
        or hostname.endswith(".youtube.com")
        or hostname == "youtube-nocookie.com"
        or hostname.endswith(".youtube-nocookie.com")
    ):
        raise ValueError("YouTube links are not supported. Enter an article URL.")

    return source


def SearchAndArgue(client, statement, searchPrompt, maxNumTexts, argueTrue):
    searchResults = client.search(searchPrompt, max_results=maxNumTexts)
    urls = []
    texts = ""
    for r in searchResults['results']:
        urls.append(r['url'])

    numTexts = maxNumTexts
    for url in urls:
        downloaded = trafilatura.fetch_url(url)
        extracted = trafilatura.extract(downloaded)
        if extracted is not None:
            texts += extracted + "+++++"

    tf = ""
    if argueTrue:
        tf = "true"
    else:
        tf = "false"

    promptForward = (
        f"I am going to feed you 1 evaluation statement and {maxNumTexts} texts. "
        f"Argue that the evaluation statement is {tf} based solely on those {maxNumTexts} texts. "
        "Present the argument as distinct, individual points supporting this position. "
        "For each point, state the specific claim and explain the reasoning behind it, showing how the relevant information in the texts supports the point and the overall position. "
        "Do not summarize the texts or provide a general recap; analyze the evidence and explain why it matters to the evaluation statement. "
        "Keep the points separate, avoid repeating the same argument, and do not introduce facts or assumptions that are not supported by the texts."
    )
    argument = ollamaClient.chat(
        model=modelName,
        messages=[
            {
                'role': 'user',
                'content': f"{promptForward} | Evaluation statement: {statement} | Texts: {texts}"
            }
        ]
    )
    return argument.message.content


def run_analysis(source, selected_model, numSources):
    """Run the original extraction, search, and argument workflow for the GUI."""
    global modelName, ollamaClient

    modelName = selected_model
    ollamaClient = Client(host='http://localhost:11434')

    source = validate_article_url(source)

    download = trafilatura.fetch_url(source)
    extractedText = trafilatura.extract(download)
    if extractedText is None:
        raise ValueError("No article text could be extracted from that link.")

    delimiter = '$$$'
    howToFormatOutputSubPrompt = (f"Delimit statements by putting {delimiter} at the end of each individual statement")
    howToExtractSubPrompt = ("I am going to feed you a news article. Extract from the following text statements that may be true or false, but do not make a"
                             " decision if those statements are true or false:")
    extractedStatementsText = ollamaClient.chat(
        model=modelName,
        messages=[
            {
                'role': 'user',
                'content': f"{howToFormatOutputSubPrompt} {howToExtractSubPrompt} {extractedText}"
            }
        ]
    )
    statementsText = extractedStatementsText.message.content
    tokens = statementsText.split(delimiter)

    # Grab a statement at random --> for now
    chosenStatement = random.choice(tokens)

    defenseSearchPrompt = (f"Here is a statement. Find me {numSources} resources defending this statement: {chosenStatement}")
    offenseSearchPrompt = (f"Here is a statement. Find me {numSources} resources countering this statement: {chosenStatement}")
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    # Find and build the argument supporting the statement.
    argument_for = SearchAndArgue(client, chosenStatement, defenseSearchPrompt, numSources, True)
    # Find and build the argument countering the statement.
    argument_against = SearchAndArgue(client, chosenStatement, offenseSearchPrompt, numSources, False)

    return {
        "chosen_statement": chosenStatement,
        "argument_for": argument_for,
        "argument_against": argument_against,
    }


class ScrollableFrame(ttk.Frame):
    """A frame whose contents can be scrolled vertically in the main window."""

    def __init__(self, master):
        super().__init__(master)
        self.canvas = tk.Canvas(self, bg=THEME_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.content = ttk.Frame(self.canvas, padding=18)
        self.content_window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.content.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_content)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _update_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_content(self, event):
        self.canvas.itemconfigure(self.content_window, width=event.width)

    def _on_mousewheel(self, event):
        if getattr(event, "num", None) == 4:
            self.canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            self.canvas.yview_scroll(1, "units")
        elif event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class DiscourseDissector:
    def __init__(self, root):
        self.root = root
        root.title("Discourse Dissector")
        root.geometry("760x760")
        root.minsize(560, 520)
        apply_theme(root)

        self.result_queue = queue.Queue()
        self.model_var = tk.StringVar(value="llama3.2:3b")
        self.resources_var = tk.IntVar(value=3)

        self.scrollable = ScrollableFrame(root)
        self.scrollable.pack(fill="both", expand=True)
        self.content = self.scrollable.content

        self._build_gui()
        self.root.after(100, self._poll_result_queue)

    def _build_gui(self):
        header = ttk.Frame(self.content)
        header.pack(fill="x", pady=(0, 18))

        title = tk.Label(
            header,
            text="Discourse Dissector",
            font=("Helvetica", 18, "bold"),
            bg=THEME_BG,
            fg=THEME_FG,
        )
        title.pack(anchor="center")

        input_frame = ttk.LabelFrame(self.content, text="Input", padding=12)
        input_frame.pack(fill="x", pady=(0, 12))

        tk.Label(
            input_frame,
            text="Enter a link to an article:",
            bg=THEME_BG,
            fg=THEME_FG,
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        self.statement_entry = ttk.Entry(input_frame)
        self.statement_entry.pack(fill="x", ipady=5)

        controls = ttk.Frame(self.content)
        controls.pack(fill="x", pady=(0, 12))
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)

        model_frame = ttk.LabelFrame(controls, text="Model", padding=12)
        model_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.model_dropdown = ttk.Combobox(
            model_frame,
            textvariable=self.model_var,
            values=("llama3.2:3b", "qwen2.5:3b"),
            state="readonly",
        )
        self.model_dropdown.pack(fill="x")

        resources_frame = ttk.LabelFrame(controls, text="Resources requested", padding=12)
        resources_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.resources_value_label = tk.Label(
            resources_frame,
            textvariable=self.resources_var,
            bg=THEME_BG,
            fg=THEME_FG,
            font=("Segoe UI", 11, "bold"),
        )
        self.resources_value_label.pack(anchor="center")

        self.resources_slider = tk.Scale(
            resources_frame,
            from_=1,
            to=10,
            resolution=1,
            orient="horizontal",
            showvalue=False,
            variable=self.resources_var,
            bg=THEME_BG,
            fg=THEME_FG,
            highlightthickness=0,
            troughcolor=THEME_FIELD_BG,
            activebackground=THEME_ACCENT,
        )
        self.resources_slider.pack(fill="x")

        run_frame = ttk.Frame(self.content)
        run_frame.pack(fill="x", pady=(2, 12))

        self.run_button = ttk.Button(
            run_frame,
            text="Run Dissection",
            style="Accent.TButton",
            command=self.on_run,
        )
        self.run_button.pack(anchor="center", ipadx=24, ipady=5)

        self.progress = ttk.Progressbar(run_frame, mode="indeterminate", length=260)
        self.progress.pack(anchor="center", pady=(10, 4))
        self.progress.pack_forget()

        self.status_label = tk.Label(
            run_frame,
            text="Ready",
            bg=THEME_BG,
            fg=THEME_FG,
        )
        self.status_label.pack(anchor="center")

        results_frame = ttk.LabelFrame(self.content, text="Dissection results", padding=12)
        results_frame.pack(fill="both", expand=True, pady=(0, 12))

        self.results_text = tk.Text(
            results_frame,
            wrap="word",
            height=28,
            bg=THEME_FIELD_BG,
            fg=THEME_FG,
            relief="solid",
            borderwidth=1,
            padx=10,
            pady=10,
        )
        results_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        results_scrollbar.pack(side="right", fill="y")
        self.results_text.pack(side="left", fill="both", expand=True)

        self.results_text.tag_configure("heading", font=("Segoe UI", 10, "bold"), foreground=THEME_ACCENT)
        self.results_text.insert("end", "Your chosen statement and both sides of the argument will appear here.\n")
        self.results_text.configure(state="disabled")

    def _set_results(self, content):
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("end", content)
        self.results_text.configure(state="disabled")
        self.results_text.yview_moveto(0)

    def on_run(self):
        source = self.statement_entry.get().strip()
        if not source:
            self.status_label.configure(text="Enter an article URL first.")
            return

        try:
            source = validate_article_url(source)
        except ValueError as exc:
            self.status_label.configure(text=str(exc))
            return

        selected_model = self.model_var.get()
        num_sources = int(self.resources_var.get())

        self.run_button.configure(state="disabled")
        self.statement_entry.configure(state="disabled")
        self.model_dropdown.configure(state="disabled")
        self.resources_slider.configure(state="disabled")
        self.progress.pack(anchor="center", pady=(10, 4))
        self.progress.start(10)
        self.status_label.configure(text="Running extraction, searches, and arguments...")
        self._set_results("Working...\n")

        worker = threading.Thread(
            target=self._run_in_background,
            args=(source, selected_model, num_sources),
            daemon=True,
        )
        worker.start()

    def _run_in_background(self, source, selected_model, num_sources):
        try:
            result = run_analysis(source, selected_model, num_sources)
            self.result_queue.put(("success", result))
        except Exception as exc:
            self.result_queue.put(("error", f"{type(exc).__name__}: {exc}"))

    def _poll_result_queue(self):
        try:
            result_type, result = self.result_queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_result_queue)
            return

        self.progress.stop()
        self.progress.pack_forget()
        self.run_button.configure(state="normal")
        self.statement_entry.configure(state="normal")
        self.model_dropdown.configure(state="readonly")
        self.resources_slider.configure(state="normal")

        if result_type == "success":
            output = (
                "Chosen Statement:\n"
                f"{result['chosen_statement']}\n\n"
                "Arguments for STATEMENT:\n"
                f"{result['argument_for']}\n\n"
                "Arguments against STATEMENT:\n"
                f"{result['argument_against']}\n"
            )
            self._set_results(output)
            self.status_label.configure(text="Dissection complete.")
        else:
            self._set_results(f"The dissection could not be completed.\n\n{result}\n")
            self.status_label.configure(text="An error occurred. See the results area for details.")

        self.root.after(100, self._poll_result_queue)


if __name__ == '__main__':
    root = tk.Tk()
    app = DiscourseDissector(root)
    root.mainloop()
