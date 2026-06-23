import os
import sys
import shutil
import threading
import subprocess
import queue
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Visual Design Color Tokens (Starminer Sci-Fi Aesthetic)
COLOR_BG = "#0f111a"          # Deep cosmic dark
COLOR_CARD = "#161925"        # Card background
COLOR_TEXT_PRIMARY = "#ffffff" # Primary text
COLOR_TEXT_MUTED = "#8a93b2"   # Muted gray text
COLOR_CYAN = "#00d2ff"         # Cyber cyan
COLOR_BLUE = "#1d4ed8"         # Electric blue
COLOR_GREEN = "#10b981"        # Success green
COLOR_RED = "#ef4444"          # Warning red
COLOR_TERMINAL_BG = "#06070a"  # Console black
COLOR_BORDER = "#252b3d"       # Outer borders

class StarminerModGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Starminer Music Replacer Mod Tool")
        self.root.geometry("800x700")
        self.root.configure(bg=COLOR_BG)
        
        # Paths
        self.tool_dir = os.path.dirname(os.path.abspath(__file__))
        self.input_audio_dir = os.path.join(self.tool_dir, "InputAudio")
        self.game_exe = os.path.abspath(os.path.join(self.tool_dir, "..", "game", "ILLSpace.exe"))
        
        os.makedirs(self.input_audio_dir, exist_ok=True)
        
        # Queue for thread-safe UI console logging
        self.log_queue = queue.Queue()
        
        # Audio tracks definitions
        self.tracks = {
            "MainMenu": "Main Menu Theme",
            "Adrift": "Exploration - Adrift",
            "Breathless": "Exploration - Breathless",
            "Dream_Chamber": "Exploration - Dream Chamber",
            "Dust": "Exploration - Dust"
        }
        
        # UI variables
        self.track_statuses = {} # stores status labels
        self.track_actions = {}  # stores action frame reference
        
        self.setup_styles()
        self.build_ui()
        self.refresh_all_statuses()
        
        # Start checking the queue for console logs
        self.root.after(100, self.process_log_queue)

    def setup_styles(self):
        # Configure scrollbar styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Vertical.TScrollbar", gripcount=0,
                        background=COLOR_CARD, darkcolor=COLOR_CARD, lightcolor=COLOR_CARD,
                        troughcolor=COLOR_BG, bordercolor=COLOR_BG)

    def build_ui(self):
        # Main Frame container
        main_container = tk.Frame(self.root, bg=COLOR_BG, padx=20, pady=20)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # --- HEADER SECTION ---
        header_frame = tk.Frame(main_container, bg=COLOR_BG)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(header_frame, text="🌌 STARMINER MUSIC REPLACER", 
                               font=("Segoe UI", 18, "bold"), fg=COLOR_CYAN, bg=COLOR_BG)
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(header_frame, text="Replace Starminer's background tracks and package them into an encrypted patch pak.", 
                                  font=("Segoe UI", 10), fg=COLOR_TEXT_MUTED, bg=COLOR_BG)
        subtitle_label.pack(anchor="w", pady=(2, 0))
        
        # --- TRACKS MANAGER SECTION ---
        tracks_frame = tk.LabelFrame(main_container, text=" AUDIO TRACKS MANAGER ", 
                                     font=("Segoe UI", 10, "bold"), fg=COLOR_CYAN, bg=COLOR_CARD, 
                                     bd=1, relief=tk.SOLID, highlightbackground=COLOR_BORDER)
        tracks_frame.config(padx=15, pady=15)
        tracks_frame.pack(fill=tk.X, pady=(0, 15))
        
        for key, name in self.tracks.items():
            row_frame = tk.Frame(tracks_frame, bg=COLOR_CARD, pady=6)
            row_frame.pack(fill=tk.X)
            
            # Track Name
            lbl_name = tk.Label(row_frame, text=f"{name}:", font=("Segoe UI", 10, "bold"), 
                                fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD, width=22, anchor="w")
            lbl_name.pack(side=tk.LEFT)
            
            # Status Indicator
            lbl_status = tk.Label(row_frame, text="Original Game Music", font=("Segoe UI", 10), 
                                  fg=COLOR_TEXT_MUTED, bg=COLOR_CARD, width=32, anchor="w")
            lbl_status.pack(side=tk.LEFT, padx=10)
            self.track_statuses[key] = lbl_status
            
            # Action buttons container
            actions_frame = tk.Frame(row_frame, bg=COLOR_CARD)
            actions_frame.pack(side=tk.RIGHT)
            self.track_actions[key] = actions_frame

        # --- ACTIONS SECTION ---
        actions_bar = tk.Frame(main_container, bg=COLOR_BG)
        actions_bar.pack(fill=tk.X, pady=(0, 15))
        
        self.btn_compile = tk.Button(actions_bar, text="🔨 COMPILE MUSIC MOD", font=("Segoe UI", 11, "bold"),
                                     bg=COLOR_BLUE, fg=COLOR_TEXT_PRIMARY, activebackground=COLOR_CYAN,
                                     activeforeground=COLOR_BG, relief=tk.FLAT, bd=0, padx=20, pady=10,
                                     command=self.start_compilation)
        self.btn_compile.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_launch = tk.Button(actions_bar, text="🚀 LAUNCH STARMINER", font=("Segoe UI", 11, "bold"),
                                    bg=COLOR_GREEN, fg=COLOR_TEXT_PRIMARY, activebackground=COLOR_CYAN,
                                    activeforeground=COLOR_BG, relief=tk.FLAT, bd=0, padx=20, pady=10,
                                    command=self.launch_game)
        self.btn_launch.pack(side=tk.LEFT)
        if not os.path.exists(self.game_exe):
            self.btn_launch.config(state=tk.DISABLED, bg="#202b30", fg=COLOR_TEXT_MUTED)
            
        # --- CONSOLE TERMINAL SECTION ---
        console_frame = tk.LabelFrame(main_container, text=" BUILD CONSOLE LOGS ", 
                                      font=("Segoe UI", 10, "bold"), fg=COLOR_CYAN, bg=COLOR_TERMINAL_BG, 
                                      bd=1, relief=tk.SOLID)
        console_frame.config(padx=10, pady=10)
        console_frame.pack(fill=tk.BOTH, expand=True)
        
        self.terminal = tk.Text(console_frame, bg=COLOR_TERMINAL_BG, fg="#00ff66", 
                                font=("Consolas", 10), insertbackground="white", 
                                relief=tk.FLAT, bd=0, wrap=tk.WORD)
        self.terminal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(console_frame, orient="vertical", command=self.terminal.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.terminal.configure(yscrollcommand=scrollbar.set)
        
        self.append_to_terminal("Terminal Ready. Select your music files above and click 'Compile Music Mod'.\n")

    # --- TRACK STATUS LOGIC ---
    def find_track_file(self, track_key):
        """Scans InputAudio directory for the given track base name."""
        supported_exts = [".wav", ".mp3", ".ogg"]
        for ext in supported_exts:
            filename = track_key + ext
            path = os.path.join(self.input_audio_dir, filename)
            if os.path.exists(path):
                return path, filename
        return None, None

    def refresh_track_row(self, track_key):
        """Refreshes status text, color, and action buttons for a single track row."""
        path, filename = self.find_track_file(track_key)
        status_label = self.track_statuses[track_key]
        actions_frame = self.track_actions[track_key]
        
        # Clear existing action buttons
        for widget in actions_frame.winfo_children():
            widget.destroy()
            
        if path:
            status_label.config(text=f"Loaded: {filename}", fg=COLOR_GREEN)
            
            # Remove button
            btn_remove = tk.Button(actions_frame, text="Clear", font=("Segoe UI", 9),
                                   bg=COLOR_RED, fg=COLOR_TEXT_PRIMARY, activebackground=COLOR_CYAN,
                                   relief=tk.FLAT, bd=0, padx=12, pady=3,
                                   command=lambda k=track_key: self.clear_track(k))
            btn_remove.pack(side=tk.RIGHT)
        else:
            status_label.config(text="Original Game Music", fg=COLOR_TEXT_MUTED)
            
            # Import button
            btn_import = tk.Button(actions_frame, text="Import...", font=("Segoe UI", 9),
                                   bg=COLOR_BLUE, fg=COLOR_TEXT_PRIMARY, activebackground=COLOR_CYAN,
                                   relief=tk.FLAT, bd=0, padx=12, pady=3,
                                   command=lambda k=track_key: self.import_track(k))
            btn_import.pack(side=tk.RIGHT)

    def refresh_all_statuses(self):
        for key in self.tracks:
            self.refresh_track_row(key)

    def import_track(self, track_key):
        file_path = filedialog.askopenfilename(
            title=f"Select audio for {self.tracks[track_key]}",
            filetypes=[("Audio Files", "*.wav *.mp3 *.ogg"), ("WAV Files", "*.wav"), ("MP3 Files", "*.mp3"), ("OGG Files", "*.ogg")]
        )
        if not file_path:
            return
            
        ext = os.path.splitext(file_path)[1].lower()
        dest_filename = track_key + ext
        dest_path = os.path.join(self.input_audio_dir, dest_filename)
        
        # Delete any conflicting files for this track first
        self.clear_track(track_key, silent=True)
        
        try:
            shutil.copy2(file_path, dest_path)
            self.append_to_terminal(f"Successfully imported {os.path.basename(file_path)} as {dest_filename}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import file: {e}")
            self.append_to_terminal(f"Error importing file: {e}\n")
            
        self.refresh_track_row(track_key)

    def clear_track(self, track_key, silent=False):
        path, filename = self.find_track_file(track_key)
        if path:
            try:
                os.remove(path)
                if not silent:
                    self.append_to_terminal(f"Removed custom track {filename}. Reverted to original.\n")
            except Exception as e:
                if not silent:
                    messagebox.showerror("Error", f"Failed to delete file: {e}")
                    
        self.refresh_track_row(track_key)

    # --- COMPILATION LOGIC (THREADED) ---
    def start_compilation(self):
        # Prevent starting multiple compilations
        self.btn_compile.config(state=tk.DISABLED, bg="#202b30", text="🔨 COMPILING...")
        self.terminal.delete(1.0, tk.END)
        self.append_to_terminal("=== Starting Mod Compilation ===\n")
        
        # Start build thread
        thread = threading.Thread(target=self.run_compilation_thread)
        thread.daemon = True
        thread.start()

    def run_compilation_thread(self):
        # We run run_mod.bat as a subprocess, reading output line by line
        bat_file = os.path.join(self.tool_dir, "run_mod.bat")
        
        # On Windows, we use CREATE_NO_WINDOW to avoid spawning a console window
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        try:
            # We run cmd.exe /c run_mod.bat. To prevent it waiting for pause, we can pass input or temporarily bypass.
            process = subprocess.Popen(
                ["cmd.exe", "/c", bat_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=self.tool_dir,
                startupinfo=startupinfo,
                bufsize=1
            )
            
            # Press enter for any pauses by feeding empty input
            if process.stdin:
                process.stdin.close()
                
            for line in process.stdout:
                self.log_queue.put(line)
                
            process.wait()
            
            if process.returncode == 0:
                self.log_queue.put("\n=== SUCCESS: Mod compiled successfully! ===\n")
            else:
                self.log_queue.put(f"\n=== FAILED: Mod compilation failed with exit code {process.returncode} ===\n")
                
        except Exception as e:
            self.log_queue.put(f"\nError running build script: {e}\n")
            
        # Re-enable build button in thread-safe way via queue
        self.log_queue.put("ENABLE_BUILD_BUTTON")

    def process_log_queue(self):
        """Processes logs queued by the compilation thread to write them to the UI."""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if msg == "ENABLE_BUILD_BUTTON":
                    self.btn_compile.config(state=tk.NORMAL, bg=COLOR_BLUE, text="🔨 COMPILE MUSIC MOD")
                else:
                    self.append_to_terminal(msg)
                self.log_queue.task_done()
        except queue.Empty:
            pass
            
        # Schedule next queue check
        self.root.after(100, self.process_log_queue)

    def append_to_terminal(self, text):
        self.terminal.insert(tk.END, text)
        self.terminal.see(tk.END)

    # --- LAUNCH GAME ---
    def launch_game(self):
        if os.path.exists(self.game_exe):
            try:
                # Launch game without blocking GUI
                subprocess.Popen([self.game_exe], cwd=os.path.dirname(self.game_exe))
                self.append_to_terminal("Launching Starminer (ILLSpace.exe)...\n")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch game: {e}")
        else:
            messagebox.showerror("Error", f"Game executable not found at {self.game_exe}")

if __name__ == "__main__":
    root = tk.Tk()
    app = StarminerModGUI(root)
    root.mainloop()
