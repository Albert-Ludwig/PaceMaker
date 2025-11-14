# This class is used to draw the EG diagram (Egram). 
# For D1, only data structure and windows are provided.

import time, threading, struct, tkinter as tk, queue
from tkinter import ttk, Canvas
from collections import deque
from tkinter import messagebox

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
        self.markers = []  # Reserved for future use (not displayed in D1)

    def append_batch(self, batch):  # batch: [(t, vAtrial, vVentricular, vECG), ...]
        for t, atrial, ventricular, ecg in batch:
            self.buffers["Atrial EGM"].append((t, atrial))
            self.buffers["Ventricular EGM"].append((t, ventricular))
            self.buffers["Surface ECG"].append((t, ecg))

class EgramController: # Controller to manage data streaming and drawing
    def __init__(self, model, view, source, tk_root, refresh_ms=25):
        self.model, self.view, self.source = model, view, source
        self.tk_root, self.refresh_ms = tk_root, refresh_ms
        self.q = queue.Queue()
        self.running = False
        self.thread = None

    def start(self): # Start data streaming and drawing
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._producer, daemon=True)
        self.thread.start()
        self._draw_loop()

    def stop(self): # Stop data streaming and drawing
        self.running = False

    def _producer(self): # Data producer thread
        for chunk in self.source.stream():  # Generator: yield [(t,atrial,ventricular,ecg), ...]
            if not self.running: break
            self.q.put(chunk)

    def _draw_loop(self): # Periodic drawing in main thread
        try:
            while not self.q.empty():
                self.model.append_batch(self.q.get_nowait())
            self.view.render(self.model)  # Draw in main thread
        finally:
            if self.running:
                self.tk_root.after(self.refresh_ms, self._draw_loop)

class EgramView(tk.Canvas): # Canvas to render EGdiagram
    def __init__(self, parent, **kw):
        super().__init__(parent, bg="white", **kw)
        self.show = {"Atrial EGM": True, "Ventricular EGM": True, "Surface ECG": True}
        self.colors = {"Atrial EGM":"red", "Ventricular EGM":"green", "Surface ECG":"blue"}
        self.zoom = 1.0 # Zoom factor 
        # Pan state (in seconds)
        self.pan_offset_s = 0.0
        self._drag_x = None
        # Mouse bindings for panning
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Double-Button-1>", self._on_reset_pan)

    # --- Mouse handlers for panning ---
    def _on_press(self, ev): # Start panning
        self._drag_x = ev.x

    def _on_drag(self, ev): # Update panning
        if self._drag_x is None or not hasattr(self, "_last_model"):
            return
        w = self.winfo_width()
        span = self._last_model.time_span_s
        # pixels -> seconds
        dx_px = ev.x - self._drag_x
        self._drag_x = ev.x
        dx_s = -dx_px * (span / max(w, 1))  # drag left -> look earlier
        # update and clamp pan offset
        self.pan_offset_s = max(0.0, min(self._max_pan(self._last_model), self.pan_offset_s + dx_s))
        self.render(self._last_model)

    def _on_release(self, ev): # End panning
        self._drag_x = None

    def _on_reset_pan(self, ev): # Double-click to reset pan
        self.pan_offset_s = 0.0
        if hasattr(self, "_last_model"):
            self.render(self._last_model)

    def _max_pan(self, model): # Maximum pan (in seconds) available based on buffered history.
        """Maximum pan (in seconds) available based on buffered history."""
        buf = model.buffers["Surface ECG"]
        if len(buf) < 2:
            return 0.0
        t_min = buf[0][0]
        t_max = buf[-1][0]
        history = max(0.0, (t_max - t_min) - model.time_span_s)
        return history

    def render(self, model):
        # keep a handle so drag events can re-render
        self._last_model = model

        w, h = self.winfo_width(), self.winfo_height()
        self.delete("all")
        
        # Draw axes with labels
        self._draw_axes_and_labels(w, h)
        
        # Draw grid (1s major grid, 0.2s minor grid)
        self._draw_grid(w, h, model.time_span_s)
        
        # Get X/Y scaling with margins for axes
        margin_left = 60  # Space for Y axis label
        margin_bottom = 30  # Space for X axis label
        plot_w = w - margin_left
        plot_h = h - margin_bottom
        
        sx = plot_w / model.time_span_s
        # Y axis, use fixed amplitude window (e.g. ±2.5 mV), then multiply by gain
        y_range_mv = 2.5 / model.gain
        sy = plot_h / (2*y_range_mv)  # Map ±y_range to canvas
        y_mid = plot_h/2

        # Determine time window [t0, t1]
        any_buf = model.buffers["Surface ECG"]
        if not any_buf:
            return
        t_end = any_buf[-1][0]  # latest timestamp we have
        max_pan = self._max_pan(model)
        self.pan_offset_s = max(0.0, min(max_pan, self.pan_offset_s))
        t0 = max(any_buf[0][0], t_end - model.time_span_s - self.pan_offset_s)
        t1 = t0 + model.time_span_s

        def to_xy(buf):
            if not buf: return []
            pts=[]
            # Only draw points within [t0, t1]
            for t,v in buf:
                if t < t0:
                    continue
                if t > t1:
                    break
                x = margin_left + (t - t0)*sx
                y = y_mid - (v * self.zoom) * sy
                pts += [x,y]
            return pts

        for ch in ("Atrial EGM","Ventricular EGM","Surface ECG"):
            if not self.show[ch]: continue
            pts = to_xy(model.buffers[ch])
            if len(pts)>=4:
                self.create_line(*pts, fill=self.colors[ch], width=2, smooth=False)
    
        label = f"X{self.zoom:g}"
        self.create_text(
            self.winfo_width() - 8, 12,
            text=label,
            anchor="ne",
            fill="blue",
            font=("TkDefaultFont", 12, "bold")
        )

    def _draw_grid(self, w, h, span_s):
        # Grid with margins
        margin_left = 60
        margin_bottom = 30
        plot_w = w - margin_left
        plot_h = h - margin_bottom
        
        # Vertical lines
        major=1.0; minor=0.2
        x_per_s = plot_w/span_s
        for i in range(int(span_s/minor)+1):
            x = margin_left + i*minor*x_per_s
            self.create_line(x, 0, x, plot_h, fill="#eee" if i%5 else "#ccc")
        # Horizontal lines
        for i in range(10):
            y = i*plot_h/10
            self.create_line(margin_left, y, w, y, fill="#eee" if i%5 else "#ccc")

    def _draw_axes_and_labels(self, w, h):
        """Draw X/Y axes with simple labels."""
        margin_left = 60
        margin_bottom = 30
        plot_w = w - margin_left
        plot_h = h - margin_bottom
        
        # Draw axes
        # Y axis (left side)
        self.create_line(margin_left, 0, margin_left, plot_h, fill="#000", width=2)
        # X axis (bottom)
        self.create_line(margin_left, plot_h, w, plot_h, fill="#000", width=2)
        
        # Y axis label (rotated "Amplitude")
        self.create_text(20, plot_h/2, text="Amplitude", angle=90, anchor="center", 
                        fill="#000", font=("TkDefaultFont", 12))
        
        # X axis label
        self.create_text(margin_left + plot_w/2, h - 10, text="Time", anchor="center",
                        fill="#000", font=("TkDefaultFont", 12))
    
    def set_zoom(self, factor: float):
        """Set the zoom factor"""
        self.zoom = factor
        if hasattr(self, "_last_model"):
            self.render(self._last_model)


class EgramWindow: # EGdiagram window
    def __init__(self, parent, comm_manager=None):
        self.comm_manager = comm_manager
        self.window = tk.Toplevel(parent)
        self.window.title("EG Diagram")
        self.window.geometry("1100x700")
        
        # Create control panel
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Add control buttons
        self.start_btn = ttk.Button(control_frame, text="Start", command=self.start_egram)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_egram)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(control_frame, text="Clear", command=self.clear_egram)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # state of the EGdiagram
        self._is_running = False
        self._update_buttons()

        # Zoom controls
        ttk.Label(control_frame, text="Zoom:").pack(side=tk.LEFT, padx=(10, 2))
        for z in (0.5, 1, 2):
            ttk.Button(
                control_frame,
                text=f"X{z}",
                command=lambda f=z: self.canvas.set_zoom(f)
            ).pack(side=tk.LEFT, padx=2)
        
        # Add channel selection
        self.channel_vars = {
            "Atrial EGM": tk.BooleanVar(value=True),
            "Ventricular EGM": tk.BooleanVar(value=True),
            "Surface ECG": tk.BooleanVar(value=True)
        }
        
        for channel, var in self.channel_vars.items():
            ttk.Checkbutton(control_frame, text=channel, variable=var, 
                           command=self.update_display).pack(side=tk.LEFT, padx=5)
        
        # Create EGdiagram canvas
        self.canvas = EgramView(self.window, width=780, height=500)
        self.canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Initialize EGdiagram model and controller
        self.model = EgramModel()
        self.controller = None
        
        # Set window close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _update_buttons(self):
        """Keep Start/Stop/Clear buttons consistent with current running state."""
        running = bool(getattr(self, "_is_running", False))
        try:
            self.start_btn.configure(state=("disabled" if running else "normal"))
            self.stop_btn.configure(state=("normal" if running else "disabled"))
            self.clear_btn.configure(state=("disabled" if running else "normal"))
        except Exception:
            pass

    def start_egram(self):
        """Start EGdiagram data stream"""
        if getattr(self, "_is_running", False):
            messagebox.showwarning("Warning", "Egram is already running. Please press Stop first.")
            return

        if self.comm_manager is None:
            messagebox.showerror("Error", "Pacemaker not available. Please connect first.")
            return
        try:
            is_connected = self.comm_manager.get_connection_status()
        except Exception:
            is_connected = False
        if not is_connected:
            messagebox.showerror("Error", "Pacemaker not connected. Please connect first.")
            return

        source = PacemakerEgramSource(self.comm_manager)
        self.controller = EgramController(self.model, self.canvas, source, self.window)
        self.controller.start()
        self._is_running = True
        self._update_buttons()
        self._poll_connection()

    def _poll_connection(self):
        """
        Periodically check if pacemaker is still connected.
        If disconnected while plotting, stop the egram immediately.
        """
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
        """Stop EGdiagram data stream"""
        try:
            if self.controller:
                self.controller.stop()
        except Exception:
            pass
        self._is_running = False
        self._update_buttons()
    
    def clear_egram(self):
        """Clear EGdiagram display"""
        if self._is_running:
            messagebox.showwarning("Warning", "Stop the Egram before clearing.")
            return

        ok = messagebox.askyesno(
            "Confirm",
            "This option will clear the history signal, still want to clear?"
        )
        if not ok:
            return

        for ch in self.model.buffers:
            self.model.buffers[ch].clear()

        self.canvas.render(self.model)
    
    def update_display(self):
        """Update channel display status"""
        for channel, var in self.channel_vars.items():
            self.canvas.show[channel] = var.get()
        self.canvas.render(self.model)
    
    def on_close(self):
        if getattr(self, "_is_running", False):
            ok = messagebox.askyesno(
                "Confirm Exit",
                "Egram is still running. Do you want to stop and close the window?"
            )
            if not ok:
                return
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
        if self.comm_manager is None:
            return
        try:
            is_connected = self.comm_manager.get_connection_status()
        except Exception:
            is_connected = False
        if not is_connected:
            return

        serial_mgr = getattr(self.comm_manager, "serial_mgr", None)
        if serial_mgr is None:
            return
        try:
            if not serial_mgr.is_connected():
                return
        except Exception:
            return

        try:
            ok = serial_mgr.start_egram()
        except Exception:
            return
        if not ok:
            return

        try:
            while True:
                try:
                    if not self.comm_manager.get_connection_status():
                        break
                    if not serial_mgr.is_connected():
                        break
                except Exception:
                    break

                batch = []
                for _ in range(20):
                    pkt = serial_mgr.read_packet(timeout=0.2)
                    if not pkt:
                        continue
                    data = pkt[4:17]
                    decoded = serial_mgr.decode_egram(data)
                    m_vraw = decoded.get("m_vraw", 0)

                    v_signal = (m_vraw - 2048) / 2048.0
                    t = self.time
                    batch.append((t, 0.0, v_signal, 0.0))
                    self.time += 1.0 / self.sample_rate

                if batch:
                    yield batch
                else:
                    time.sleep(0.05)
        finally:
            try:
                serial_mgr.stop_egram()
            except Exception:
                pass
