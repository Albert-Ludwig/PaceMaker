# This file implements the EG diagram drawing logic using Matplotlib.
import time, threading, queue, struct
import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque

# --- Matplotlib imports ---
import matplotlib
matplotlib.use("TkAgg") 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class EgramModel:
    """Stores data buffers for Atrial and Ventricular signals."""
    def __init__(self, time_span_s=10.0, sample_rate=200):
        self.time_span_s = time_span_s
        self.sample_rate = sample_rate
        self.gain =1.0
        # Buffer holds enough data for smooth scrolling (approx 8x window width)
        maxlen = int(self.time_span_s * self.sample_rate * 8) + 1
        
        # Only Atrial and Ventricular buffers needed now
        self.buffers = {
            "Atrial": deque(maxlen=maxlen),
            "Ventricular": deque(maxlen=maxlen)
        }

    def append_batch(self, batch):
        """Append a batch of (time, atrial_val, vent_val) tuples."""
        for t, atrial, ventricular in batch:
            self.buffers["Atrial"].append((t, atrial))
            self.buffers["Ventricular"].append((t, ventricular))

class EgramController:
    """Manages the data stream thread and UI refresh loop."""
    def __init__(self, model, view, source, tk_root, refresh_ms=50):
        self.model = model
        self.view = view
        self.source = source
        self.tk_root = tk_root
        self.refresh_ms = refresh_ms
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
        # Fetch data from source and put into thread-safe queue
        for chunk in self.source.stream():
            if not self.running: break
            self.q.put(chunk)

    def _draw_loop(self):
        # Process queue and update view
        try:
            while not self.q.empty():
                self.model.append_batch(self.q.get_nowait())
            
            if self.running:
                self.view.render(self.model)
                self.tk_root.after(self.refresh_ms, self._draw_loop)
        except Exception:
            pass

class EgramView(tk.Frame):
    """Matplotlib-based view for plotting signals."""
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self.show = {"Atrial": True, "Ventricular": True}
        self.colors = {"Atrial": "red", "Ventricular": "green"}
        self.zoom = 1.0 
        self.pan_offset_s = 0.0
        self._drag_x = None
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Amplitude (mV)")
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.lines = {}
        for name, color in self.colors.items():
            line, = self.ax.plot([], [], color=color, label=name)
            self.lines[name] = line
        self.ax.legend(loc='upper right')
        self.canvas_agg = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas_widget = self.canvas_agg.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)
        self.canvas_widget.bind("<ButtonPress-1>", self._on_press)
        self.canvas_widget.bind("<B1-Motion>", self._on_drag)
        self.canvas_widget.bind("<ButtonRelease-1>", self._on_release)
        self.canvas_widget.bind("<Double-Button-1>", self._on_reset_pan)

    def _on_press(self, ev): self._drag_x = ev.x
    def _on_release(self, ev): self._drag_x = None
    
    def _on_drag(self, ev):
        if self._drag_x is None or not hasattr(self, "_last_span"): return
        w = self.canvas_widget.winfo_width()
        dx = ev.x - self._drag_x
        self._drag_x = ev.x
        # Pan logic: dragging right looks into the past
        dx_s = dx * (self._last_span / max(w, 1))
        self.pan_offset_s = max(0.0, self.pan_offset_s + dx_s)
        if hasattr(self, "_last_model"): self.render(self._last_model)

    def _on_reset_pan(self, ev):
        self.pan_offset_s = 0.0
        if hasattr(self, "_last_model"): self.render(self._last_model)

    def set_zoom(self, factor: float):
        self.zoom = factor

    def render(self, model):
        self._last_model = model
        self._last_span = model.time_span_s
        buf = model.buffers.get("Ventricular")
        if len(buf) == 0:
            buf = model.buffers.get("Atrial")
        if len(buf) == 0:
            return
        t_end = buf[-1][0]
        max_history = buf[-1][0] - buf[0][0]
        max_pan = max(0.0, max_history - model.time_span_s)
        self.pan_offset_s = min(self.pan_offset_s, max_pan)
        t1 = t_end - self.pan_offset_s
        t0 = t1 - model.time_span_s
        for name, line in self.lines.items():
            if not self.show.get(name, True):
                line.set_data([], [])
                continue
            data = model.buffers.get(name, [])
            if not data:
                line.set_data([], [])
                continue
            xs = [p[0] for p in data]
            ys = [p[1] for p in data]
            line.set_data(xs, ys)
        self.ax.set_xlim(t0, t1)
        limit = (2.5 / model.gain) / self.zoom
        self.ax.set_ylim(-limit, limit)
        self.canvas_agg.draw_idle()

class EgramWindow:
    """Main window container for the Egram graph and controls."""
    def __init__(self, parent, comm_manager=None):
        self.comm_manager = comm_manager
        self.window = tk.Toplevel(parent)
        self.window.title("EG Diagram (Real-time)")
        self.window.geometry("1100x700")
        
        # Controls Frame
        ctrl_frame = ttk.Frame(self.window)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_btn = ttk.Button(ctrl_frame, text="Start", command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(ctrl_frame, text="Stop", command=self.stop)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(ctrl_frame, text="Clear", command=self.clear)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        ttk.Label(ctrl_frame, text="Zoom:").pack(side=tk.LEFT, padx=(15, 5))
        for z in (0.5, 1, 2, 4):
            ttk.Button(ctrl_frame, text=f"x{z}", width=4,
                       command=lambda f=z: self.canvas.set_zoom(f)).pack(side=tk.LEFT)

        # Toggle Channels (Surface ECG removed)
        self.ch_vars = {
            "Atrial": tk.BooleanVar(value=True),
            "Ventricular": tk.BooleanVar(value=True)
        }
        ttk.Label(ctrl_frame, text="| Show:").pack(side=tk.LEFT, padx=(15, 5))
        for name, var in self.ch_vars.items():
            ttk.Checkbutton(ctrl_frame, text=name, variable=var, 
                           command=self.update_display).pack(side=tk.LEFT, padx=5)

        # Graph Area
        self.canvas = EgramView(self.window)
        self.canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.model = EgramModel()
        self.controller = None
        self._is_running = False
        self._update_ui_state()
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def _update_ui_state(self):
        state = "disabled" if self._is_running else "normal"
        inv_state = "normal" if self._is_running else "disabled"
        self.start_btn.config(state=state)
        self.stop_btn.config(state=inv_state)
        self.clear_btn.config(state=state)

    def start(self):
        if self._is_running: return
        if not self.comm_manager or not self.comm_manager.get_connection_status():
            messagebox.showerror("Error", "Pacemaker not connected.")
            return

        source = PacemakerEgramSource(self.comm_manager)
        self.controller = EgramController(self.model, self.canvas, source, self.window)
        self.controller.start()
        self._is_running = True
        self._update_ui_state()
        self._check_conn_loop()

    def _check_conn_loop(self):
        # Stop automatically if connection drops
        if not self._is_running: return
        if not self.comm_manager or not self.comm_manager.get_connection_status():
            self.stop()
            return
        self.window.after(500, self._check_conn_loop)

    def stop(self):
        if self.controller: self.controller.stop()
        self._is_running = False
        self._update_ui_state()

    def clear(self):
        for b in self.model.buffers.values(): b.clear()
        self.canvas.render(self.model)

    def update_display(self):
        for name, var in self.ch_vars.items():
            self.canvas.show[name] = var.get()
        self.canvas.render(self.model)

    def on_close(self):
        self.stop()
        self.window.destroy()

class PacemakerEgramSource:
    def __init__(self, comm_manager, sample_rate=200):
        self.comm_manager = comm_manager
        self.sample_rate = sample_rate
        self.time = 0.0

    def stream(self):
        if self.comm_manager is None:
            return
        try:
            if not self.comm_manager.get_connection_status():
                return
        except Exception:
            return
        serial_mgr = getattr(self.comm_manager, "serial_mgr", None)
        if not serial_mgr or not serial_mgr.is_connected():
            return
        try:
            if not serial_mgr.start_egram():
                return
        except Exception:
            return
        try:
            while True:
                try:
                    if not self.comm_manager.get_connection_status():
                        break
                except Exception:
                    break
                batch = []
                for _ in range(10):
                    pkt = serial_mgr.read_packet(timeout=0.1)
                    if not pkt:
                        continue
                    try:
                        parsed = serial_mgr.parse_packet(pkt)
                    except Exception:
                        parsed = None
                    if not parsed:
                        continue
                    data = parsed.get("data", b"")
                    if not data:
                        continue
                    try:
                        decoded = serial_mgr.decode_egram(data)
                        a_amp = float(decoded.get("m_araw", 0.0))
                        v_amp = float(decoded.get("m_vraw", 0.0))
                    except Exception:
                        a_amp, v_amp = 0.0, 0.0
                    t = self.time
                    batch.append((t, a_amp, v_amp))
                    self.time += 1.0 / self.sample_rate
                if batch:
                    yield batch
                else:
                    time.sleep(0.01)
        finally:
            try:
                serial_mgr.stop_egram()
            except Exception:
                pass