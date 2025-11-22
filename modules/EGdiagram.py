# This class is used to draw the EG diagram (Egram) using Matplotlib.
import time, threading, queue
import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque

# --- Matplotlib imports ---
import matplotlib
matplotlib.use("TkAgg") # Ensure we use the Tkinter backend
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
# --------------------------

class EgramModel: # Model to hold EGdiagram data buffers
    def __init__(self, time_span_s=8.0, sample_rate=200, gain=1.0, hp_filter_ecg=False):
        self.time_span_s = time_span_s
        self.sample_rate = sample_rate
        self.history_factor = 8  
        maxlen = int(self.time_span_s * self.sample_rate * self.history_factor) + 1
        self.buffers = {
            "Atrial EGM": deque(maxlen=maxlen),
            "Ventricular EGM": deque(maxlen=maxlen),
            "Surface ECG": deque(maxlen=maxlen)
        }
        self.gain = gain
        self.hp_filter_ecg = hp_filter_ecg
        self.markers = []

    def append_batch(self, batch):
        for t, atrial, ventricular, ecg in batch:
            self.buffers["Atrial EGM"].append((t, atrial))
            self.buffers["Ventricular EGM"].append((t, ventricular))
            self.buffers["Surface ECG"].append((t, ecg))

class EgramController: # Controller
    def __init__(self, model, view, source, tk_root, refresh_ms=50):
        self.model, self.view, self.source = model, view, source
        self.tk_root, self.refresh_ms = tk_root, refresh_ms
        self.q = queue.Queue()
        self.running = False
        self.thread = None

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._producer, daemon=True)
        self.thread.start()
        self._draw_loop()

    def stop(self):
        self.running = False

    def _producer(self):
        for chunk in self.source.stream():
            if not self.running: break
            self.q.put(chunk)

    def _draw_loop(self):
        try:
            while not self.q.empty():
                self.model.append_batch(self.q.get_nowait())
            
            if self.running:
                self.view.render(self.model)
                self.tk_root.after(self.refresh_ms, self._draw_loop)
        except Exception:
            pass

# --- Modified EgramView with Dragging Support ---
class EgramView(tk.Frame): 
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self.show = {"Atrial EGM": True, "Ventricular EGM": True, "Surface ECG": True}
        self.colors = {"Atrial EGM": "red", "Ventricular EGM": "green", "Surface ECG": "blue"}
        self.zoom = 1.0 
        self.pan_offset_s = 0.0
        self._drag_x = None

        # 1. Setup Figure and Axes
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Amplitude (mV)")
        self.ax.grid(True, linestyle='--', alpha=0.6)

        # 2. Initialize Lines
        self.lines = {}
        for name in ["Atrial EGM", "Ventricular EGM", "Surface ECG"]:
            line, = self.ax.plot([], [], label=name, color=self.colors[name], linewidth=1)
            self.lines[name] = line
        
        self.ax.legend(loc='upper right', fontsize='small')

        # 3. Embed into Tkinter
        self.canvas_agg = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas_widget = self.canvas_agg.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        # 4. Bind Events
        self.canvas_widget.bind("<ButtonPress-1>", self._on_press)
        self.canvas_widget.bind("<B1-Motion>", self._on_drag)
        self.canvas_widget.bind("<ButtonRelease-1>", self._on_release)
        self.canvas_widget.bind("<Double-Button-1>", self._on_reset_pan)

    def _on_press(self, ev):
        self._drag_x = ev.x

    def _on_drag(self, ev):
        # Only drag if we have a reference to the last time span
        if self._drag_x is None or not hasattr(self, "_last_span"):
            return
        
        w = self.canvas_widget.winfo_width()
        dx_px = ev.x - self._drag_x
        self._drag_x = ev.x
        
        # Convert pixels to seconds
        # Dragging right (positive dx) -> See past -> Increase offset
        dx_s = dx_px * (self._last_span / max(w, 1))
        
        # Update pan offset
        self.pan_offset_s = max(0.0, self.pan_offset_s + dx_s)
        
        # Force redraw if we have data
        if hasattr(self, "_last_model"):
            self.render(self._last_model)

    def _on_release(self, ev):
        self._drag_x = None

    def _on_reset_pan(self, ev):
        self.pan_offset_s = 0.0
        # Force redraw
        if hasattr(self, "_last_model"):
            self.render(self._last_model)

    def set_zoom(self, factor: float):
        self.zoom = factor

    def render(self, model):
        self._last_model = model # Save reference for dragging
        self._last_span = model.time_span_s
        
        buf = model.buffers["Surface ECG"]
        if not buf:
            return

        t_end = buf[-1][0]
        # Limit pan so we don't go past history
        max_history = buf[-1][0] - buf[0][0]
        max_pan = max(0.0, max_history - model.time_span_s)
        self.pan_offset_s = min(self.pan_offset_s, max_pan)

        t1 = t_end - self.pan_offset_s
        t0 = t1 - model.time_span_s

        # Update Lines
        for name, line in self.lines.items():
            if not self.show[name]:
                line.set_data([], [])
                continue
            
            data = model.buffers[name]
            if not data:
                continue
                
            # Convert deque to lists for plotting
            xs = [p[0] for p in data]
            ys = [p[1] for p in data]
            
            line.set_data(xs, ys)

        # Update Limits
        self.ax.set_xlim(t0, t1)
        
        limit = (2.5 / model.gain) / self.zoom
        self.ax.set_ylim(-limit, limit)

        self.canvas_agg.draw_idle()

# -----------------------------------------------------------

class EgramWindow:
    def __init__(self, parent, comm_manager=None):
        self.comm_manager = comm_manager
        self.window = tk.Toplevel(parent)
        self.window.title("EG Diagram")
        self.window.geometry("1100x700")
        
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="Start", command=self.start_egram)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_egram)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(control_frame, text="Clear", command=self.clear_egram)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self._is_running = False
        self._update_buttons()

        ttk.Label(control_frame, text="Zoom:").pack(side=tk.LEFT, padx=(10, 2))
        for z in (0.5, 1, 2):
            ttk.Button(
                control_frame,
                text=f"X{z}",
                command=lambda f=z: self.canvas.set_zoom(f)
            ).pack(side=tk.LEFT, padx=2)
        
        self.channel_vars = {
            "Atrial EGM": tk.BooleanVar(value=True),
            "Ventricular EGM": tk.BooleanVar(value=True),
            "Surface ECG": tk.BooleanVar(value=True)
        }
        
        for channel, var in self.channel_vars.items():
            ttk.Checkbutton(control_frame, text=channel, variable=var, 
                           command=self.update_display).pack(side=tk.LEFT, padx=5)
        
        # Changed to use new EgramView (Frame + Matplotlib)
        self.canvas = EgramView(self.window)
        self.canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.model = EgramModel()
        self.controller = None
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _update_buttons(self):
        running = bool(getattr(self, "_is_running", False))
        try:
            self.start_btn.configure(state=("disabled" if running else "normal"))
            self.stop_btn.configure(state=("normal" if running else "disabled"))
            self.clear_btn.configure(state=("disabled" if running else "normal"))
        except Exception:
            pass

    def start_egram(self):
        if getattr(self, "_is_running", False):
            messagebox.showwarning("Warning", "Egram is already running.")
            return

        if self.comm_manager is None:
            messagebox.showerror("Error", "Pacemaker not available.")
            return
        try:
            is_connected = self.comm_manager.get_connection_status()
        except Exception:
            is_connected = False
        if not is_connected:
            messagebox.showerror("Error", "Pacemaker not connected.")
            return

        source = PacemakerEgramSource(self.comm_manager)
        self.controller = EgramController(self.model, self.canvas, source, self.window)
        self.controller.start()
        self._is_running = True
        self._update_buttons()
        self._poll_connection()

    def _poll_connection(self):
        if not getattr(self, "_is_running", False):
            return
        if self.comm_manager is None:
            self.stop_egram()
            return
        try:
            is_connected = self.comm_manager.get_connection_status()
        except Exception:
            is_connected = False
        if not is_connected:
            self.stop_egram()
            return
        try:
            self.window.after(200, self._poll_connection)
        except Exception:
            pass

    def stop_egram(self):
        try:
            if self.controller:
                self.controller.stop()
        except Exception:
            pass
        self._is_running = False
        self._update_buttons()
    
    def clear_egram(self):
        if self._is_running:
            messagebox.showwarning("Warning", "Stop the Egram before clearing.")
            return

        ok = messagebox.askyesno("Confirm", "Clear history signal?")
        if not ok:
            return

        for ch in self.model.buffers:
            self.model.buffers[ch].clear()

        self.canvas.render(self.model)
    
    def update_display(self):
        for channel, var in self.channel_vars.items():
            self.canvas.show[channel] = var.get()
        self.canvas.render(self.model)
    
    def on_close(self):
        if getattr(self, "_is_running", False):
            try:
                self.stop_egram()
            except Exception:
                pass
        self.window.destroy()

class PacemakerEgramSource:
    def __init__(self, comm_manager, sample_rate=200):
        self.comm_manager = comm_manager
        self.sample_rate = sample_rate
        self.time = 0.0

    def stream(self):
        if self.comm_manager is None: return
        try:
            if not self.comm_manager.get_connection_status(): return
        except: return

        serial_mgr = getattr(self.comm_manager, "serial_mgr", None)
        if not serial_mgr or not serial_mgr.is_connected(): return

        try:
            if not serial_mgr.start_egram(): return
        except: return

        try:
            while True:
                try:
                    if not self.comm_manager.get_connection_status(): break
                except: break

                batch = []
                for _ in range(10): 
                    pkt = serial_mgr.read_packet(timeout=0.1)
                    if not pkt: continue
                    
                    if hasattr(serial_mgr, "decode_egram"):
                        decoded = serial_mgr.decode_egram(pkt[4:17])
                        m_vraw = decoded.get("m_vraw", 2048)
                    else:
                        # Fallback logic if decode_egram is missing
                        try:
                            m_vraw = 2048 
                        except: m_vraw = 2048

                    v_signal = (m_vraw - 2048) / 2048.0
                    t = self.time
                    batch.append((t, 0.0, 0.0, v_signal))
                    self.time += 1.0 / self.sample_rate

                if batch:
                    yield batch
                else:
                    time.sleep(0.01)
        finally:
            try: serial_mgr.stop_egram()
            except: pass