import tkinter as tk
from tkinter import ttk, messagebox, font
import requests
import webbrowser
import threading
import json
import unicodedata
import re
import urllib.parse

API_BASE_URL = "https://api.jikan.moe/v4"
COLOR_BG = "#050505"
COLOR_FG = "#00D2FF"
COLOR_ACCENT = "#005577"
COLOR_HIGHLIGHT = "#00FFFF"
FONT_FAMILY = "Consolas"

class AnimeTermApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ANIME_NET_TERMINAL_V2.0")
        self.root.geometry("800x600")
        self.root.configure(bg=COLOR_BG)

        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure("Vertical.TScrollbar", background=COLOR_ACCENT, troughcolor=COLOR_BG, borderwidth=0, arrowcolor=COLOR_FG)

        self.font_header = (FONT_FAMILY, 20, "bold")
        self.font_normal = (FONT_FAMILY, 12)
        self.font_small = (FONT_FAMILY, 10)

        self._setup_ui()

    def _setup_ui(self):
        header_frame = tk.Frame(self.root, bg=COLOR_BG, pady=20)
        header_frame.pack(fill="x")

        lbl_title = tk.Label(header_frame, text=">>> SYSTEM.ACCESS: ANIME_DATABASE",
                             font=self.font_header, bg=COLOR_BG, fg=COLOR_FG)
        lbl_title.pack()

        search_frame = tk.Frame(self.root, bg=COLOR_BG, pady=10)
        search_frame.pack(fill="x", padx=50)

        tk.Label(search_frame, text="[QUERY] >", font=self.font_normal, bg=COLOR_BG, fg=COLOR_FG).pack(side="left")

        self.entry_search = tk.Entry(search_frame, font=self.font_normal, bg="#111", fg=COLOR_FG, insertbackground=COLOR_FG, bd=1, relief="solid")
        self.entry_search.pack(side="left", fill="x", expand=True, padx=10)
        self.entry_search.bind("<Return>", lambda e: self.search_anime())
        self.entry_search.focus()

        btn_search = tk.Button(search_frame, text="[EXECUTE]", font=self.font_normal,
                               bg=COLOR_BG, fg=COLOR_FG, activebackground=COLOR_ACCENT, activeforeground=COLOR_HIGHLIGHT,
                               bd=1, relief="solid", command=self.search_anime)
        btn_search.pack(side="right")

        self.status_var = tk.StringVar()
        self.status_var.set("WAITING FOR INPUT...")
        lbl_status = tk.Label(self.root, textvariable=self.status_var, font=self.font_small, bg=COLOR_BG, fg=COLOR_ACCENT, anchor="w")
        lbl_status.pack(side="bottom", fill="x", padx=10, pady=5)

        results_frame = tk.Frame(self.root, bg=COLOR_BG, bd=2, relief="flat")
        results_frame.pack(fill="both", expand=True, padx=50, pady=10)

        self.listbox = tk.Listbox(results_frame, font=self.font_normal, bg="#0a0a0a", fg=COLOR_FG,
                                  selectbackground=COLOR_ACCENT, selectforeground=COLOR_HIGHLIGHT,
                                  bd=0, highlightthickness=1, highlightbackground=COLOR_ACCENT)
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.bind("<Double-Button-1>", self.on_item_select)
        self.listbox.bind("<Return>", self.on_item_select)

        self.current_results = []

    def log(self, message):
        self.status_var.set(f">> {message}")
        self.root.update_idletasks()

    def search_anime(self):
        query = self.entry_search.get().strip()
        if not query:
            return

        self.log(f"INITIATING SEARCH: {query}...")
        self.listbox.delete(0, tk.END)
        self.current_results = []

        threading.Thread(target=self._search_thread, args=(query,), daemon=True).start()

    def _search_thread(self, query):
        try:
            response = requests.get(f"{API_BASE_URL}/anime", params={"q": query, "limit": 20})
            response.raise_for_status()
            data = response.json().get("data", [])
            self.current_results = data
            self.root.after(0, self._update_listbox, data)
        except Exception as e:
            self.root.after(0, lambda: self.log(f"ERROR: {str(e)}"))

    def _update_listbox(self, data):
        self.listbox.delete(0, tk.END)
        if not data:
            self.log("NO_DATA_FOUND.")
            return

        for anime in data:
            title = anime.get("title", "Unknown")
            year = anime.get("year") or "????"
            score = anime.get("score") or "N/A"
            type_ = anime.get("type") or "?"
            display_text = f"[{type_:^5}] {title} ({year}) - Score: {score}"
            self.listbox.insert(tk.END, display_text)

        self.log(f"DATA_RETRIEVED: {len(data)} ENTRIES.")

    def on_item_select(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
        index = selection[0]
        anime = self.current_results[index]
        self.open_detail_window(anime)

    def open_detail_window(self, anime):
        detail_win = tk.Toplevel(self.root)
        detail_win.title(f"DETAILS: {anime.get('title')}")
        detail_win.geometry("700x500")
        detail_win.configure(bg=COLOR_BG)

        main_frame = tk.Frame(detail_win, bg=COLOR_BG, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text=anime.get("title"), font=(FONT_FAMILY, 16, "bold"),
                 bg=COLOR_BG, fg=COLOR_HIGHLIGHT, wraplength=650, justify="left").pack(anchor="w")

        meta_text = f"Type: {anime.get('type')} | Ep: {anime.get('episodes') or '?'} | Status: {anime.get('status')}"
        tk.Label(main_frame, text=meta_text, font=self.font_small, bg=COLOR_BG, fg=COLOR_ACCENT).pack(anchor="w", pady=(0, 10))

        tk.Label(main_frame, text="[SYNOPSIS]", font=self.font_normal, bg=COLOR_BG, fg=COLOR_FG).pack(anchor="w")

        synopsis_frame = tk.Frame(main_frame, bg=COLOR_BG, bd=1, relief="solid", highlightbackground=COLOR_ACCENT, highlightthickness=1)
        synopsis_frame.pack(fill="both", expand=True, pady=5)

        txt_synopsis = tk.Text(synopsis_frame, font=self.font_small, bg="#0a0a0a", fg=COLOR_FG,
                               wrap="word", height=10, bd=0, padx=5, pady=5)
        txt_synopsis.pack(side="left", fill="both", expand=True)

        scroll_syn = ttk.Scrollbar(synopsis_frame, orient="vertical", command=txt_synopsis.yview)
        scroll_syn.pack(side="right", fill="y")
        txt_synopsis.configure(yscrollcommand=scroll_syn.set)

        synopsis = anime.get("synopsis") or "No Synopsis Available."
        txt_synopsis.insert("1.0", synopsis)
        txt_synopsis.config(state="disabled")

        control_frame = tk.LabelFrame(main_frame, text="[ OPERATIONS ]", font=self.font_normal,
                                      bg=COLOR_BG, fg=COLOR_FG, bd=1, relief="solid")
        control_frame.pack(fill="x", pady=10)

        btn_frame = tk.Frame(control_frame, bg=COLOR_BG, pady=10)
        btn_frame.pack(fill="x")

        def _make_slug(title):
            s = title.lower()
            s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
            s = re.sub(r'[^a-z0-9]+', '-', s)
            return s.strip('-')

        def open_free_stream():
            self.log(f"CONNECTING TO ANIMEAV1: {anime.get('title')}...")

            def launch():
                title = anime.get("title")
                slug = _make_slug(title)
                episode_url = f"https://animeav1.com/media/{slug}/1"
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

                try:
                    r = requests.head(episode_url, headers=headers, timeout=5)
                    if r.status_code == 200:
                        webbrowser.open(episode_url)
                        self.root.after(0, lambda: self.log(f"STREAM OPENED: {episode_url}"))
                        return
                except:
                    pass

                anime_url = f"https://animeav1.com/media/{slug}"
                try:
                    r = requests.head(anime_url, headers=headers, timeout=5)
                    if r.status_code == 200:
                        webbrowser.open(anime_url)
                        self.root.after(0, lambda: self.log(f"ANIME PAGE OPENED: {anime_url}"))
                        return
                except:
                    pass

                webbrowser.open("https://animeav1.com/catalogo")
                self.root.after(0, lambda: self.log("CATALOG OPENED. SEARCH MANUALLY."))

            threading.Thread(target=launch, daemon=True).start()

        def open_download_search():
            title = anime.get("title")
            encoded_title = urllib.parse.quote(title)
            url = f"https://www.shanaproject.com/search/?title={encoded_title}&subber="
            webbrowser.open(url)

        tk.Button(btn_frame, text="[ 📺 WATCH ANIME ]", font=self.font_normal, bg=COLOR_BG, fg="#00ff00",
                  bd=1, relief="solid", command=open_free_stream).pack(side="left", padx=10, expand=True, fill="x")

        tk.Button(btn_frame, text="[ ⬇️ DOWNLOAD ]", font=self.font_normal, bg=COLOR_BG, fg="#00ccff",
                  bd=1, relief="solid", command=open_download_search).pack(side="left", padx=10, expand=True, fill="x")

        legal_frame = tk.LabelFrame(main_frame, text="[ LEGAL STREAMS ]", font=self.font_normal,
                                    bg=COLOR_BG, fg=COLOR_FG, bd=1, relief="solid")
        legal_frame.pack(fill="x", pady=(5, 0))

        self.legal_inner = tk.Frame(legal_frame, bg=COLOR_BG, pady=5)
        self.legal_inner.pack(fill="x")

        lbl_loading = tk.Label(self.legal_inner, text=">> SCANNING LEGAL SOURCES...",
                               font=self.font_small, bg=COLOR_BG, fg=COLOR_ACCENT)
        lbl_loading.pack(pady=5)

        self._load_legal_streams_inline(anime.get("mal_id"), self.legal_inner, lbl_loading)

    def _load_legal_streams_inline(self, anime_id, container, loading_label):
        def task():
            try:
                response = requests.get(f"{API_BASE_URL}/anime/{anime_id}/streaming")
                response.raise_for_status()
                data = response.json().get("data", [])
                self.root.after(0, lambda: self._display_legal_streams(data, container, loading_label))
            except Exception as e:
                self.root.after(0, lambda: loading_label.config(text=">> ERROR LOADING LEGAL SOURCES", fg="red"))

        threading.Thread(target=task, daemon=True).start()

    def _display_legal_streams(self, streams, container, loading_label):
        loading_label.destroy()

        if not streams:
            tk.Label(container, text="NO LEGAL STREAMS AVAILABLE.", font=self.font_small,
                     bg=COLOR_BG, fg="#666666").pack(pady=5)
            return

        platform_colors = {
            "crunchyroll": "#F47521",
            "netflix": "#E50914",
            "funimation": "#5B0BB5",
            "amazon prime video": "#00A8E1",
            "hulu": "#1CE783",
            "disney+": "#113CCF",
            "hidive": "#00BAFF",
            "bilibili": "#00A1D6",
        }

        btn_row = tk.Frame(container, bg=COLOR_BG)
        btn_row.pack(fill="x", padx=10, pady=5)

        for stream in streams:
            name = stream.get("name", "Unknown")
            url = stream.get("url", "")
            color = platform_colors.get(name.lower(), COLOR_HIGHLIGHT)

            btn = tk.Button(btn_row, text=f"▶ {name}", font=self.font_small,
                            bg="#111", fg=color, activebackground=COLOR_ACCENT,
                            activeforeground="white", bd=1, relief="solid", cursor="hand2",
                            command=lambda u=url: webbrowser.open(u))
            btn.pack(side="left", padx=3, pady=2, expand=True, fill="x")


if __name__ == "__main__":
    root = tk.Tk()
    app = AnimeTermApp(root)
    root.mainloop()
