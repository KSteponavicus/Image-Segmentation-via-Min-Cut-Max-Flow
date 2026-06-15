import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
 
from PIL import Image, ImageTk, ImageDraw
 
 
# Pillow compatibility for old and new versions
if hasattr(Image, "Resampling"):
    RESAMPLE_NEAREST = Image.Resampling.NEAREST
    RESAMPLE_DOWNSAMPLE = Image.Resampling.BOX
else:
    RESAMPLE_NEAREST = Image.NEAREST
    RESAMPLE_DOWNSAMPLE = Image.BOX
 
 
class ScrollableImagePane(tk.Frame):
    """
    A reusable scrollable image pane with:
    - canvas
    - horizontal scrollbar
    - vertical scrollbar
    - right-click drag panning
    """
 
    def __init__(self, parent, bg="gray"):
        super().__init__(parent)
 
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.h_scroll = tk.Scrollbar(
            self,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview
        )
        self.v_scroll = tk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )
 
        self.canvas.configure(
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set
        )
 
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")
 
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
 
        self.tk_image = None
        self.image_id = None
 
        # Right-click panning
        self.canvas.bind("<Button-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.pan)
 
    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)
 
    def pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
 
    def show_image(self, pil_image, preserve_view=True):
        """
        Display a PIL image in this pane.
        Keeps a Tk reference so the image does not disappear.
        """
        if preserve_view:
            old_x = self.canvas.xview()[0]
            old_y = self.canvas.yview()[0]
        else:
            old_x = 0
            old_y = 0
 
        self.tk_image = ImageTk.PhotoImage(pil_image)
 
        self.canvas.delete("all")
        self.image_id = self.canvas.create_image(
            0,
            0,
            anchor="nw",
            image=self.tk_image
        )
 
        w, h = pil_image.size
        self.canvas.configure(scrollregion=(0, 0, w, h))
 
        if preserve_view:
            self.canvas.xview_moveto(old_x)
            self.canvas.yview_moveto(old_y)
 
 
class PixelAnnotationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Segmentation")
 
        # ----------------------------
        # Image state
        # ----------------------------
        self.image = None
        self.image_width = 0
        self.image_height = 0
 
        self.overlay = None
        self.overlay_draw = None
        self.overlay_pixels = None
 
        self.result_image = None
        self.result_overlay = None
 
        # Exact annotation masks.
        # These are bytearrays of length width * height.
        self.red_mask = None
        self.green_mask = None
 
        # Owner mask:
        # 0 = no annotation
        # 1 = green owns this pixel
        # 2 = red owns this pixel
        self.owner_mask = None
 
        # Undo support.
        self.undo_stack = []
        self.current_stroke_changes = None
 
        # Drawing/tool state
        self.current_color = "green"
        self.current_tool = "green"    # "green", "red", or "eraser"
        self.brush_radius = 0
        self.last_x = None
        self.last_y = None
 
        # Fixed annotation appearance.
        # Strokes do not accumulate opacity/intensity when painted over.
        self.marker_intensity = 1
        self.marker_alpha = 160
 
        # ----------------------------
        # Algorithm selection
        # ----------------------------
        self.algorithm_options = [
            "Edmonds-Karp",
            "Push-Relabel",
            "Dinic",
            "Boykov-Kolmogorov"
        ]
        self.selected_algorithm = tk.StringVar(value="Edmonds-Karp")
 
        # ----------------------------
        # Zoom state
        # ----------------------------
        self.zoom_levels = [
            0.125,
            0.25,
            0.5,
            1,
            2,
            4,
            8,
            16,
            32,
            64
        ]
        self.zoom_index = self.zoom_levels.index(1)
 
        # Prevent creating dangerously huge display images.
        self.max_display_pixels = 80_000_000
 
        # ----------------------------
        # Performance state
        # ----------------------------
        self._left_update_job = None
        self._left_base_cache = None
        self._left_base_cache_zoom = None
 
        # ----------------------------
        # Status animation state
        # ----------------------------
        self._status_anim_job = None
        self._status_anim_dots = 0
        self._status_base = ""
 
        # Icons
        self.green_icon = self.make_marker_icon("green")
        self.red_icon = self.make_marker_icon("red")
        self.eraser_icon = self.make_eraser_icon()
        self.zoom_out_icon = self.make_zoom_icon("-")
        self.zoom_in_icon = self.make_zoom_icon("+")
 
        self.build_ui()
 
    # ============================================================
    # UI
    # ============================================================
    def build_ui(self):
        menubar = tk.Menu(self.root)
 
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Image", command=self.load_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
 
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)
 
        # ----------------------------
        # Main two-pane area
        # ----------------------------
        self.main = tk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL,
            sashwidth=6
        )
        self.main.pack(fill=tk.BOTH, expand=True)
 
        self.left_pane = ScrollableImagePane(self.main, bg="#555555")
        self.right_pane = ScrollableImagePane(self.main, bg="#eeeeee")
 
        self.main.add(self.left_pane, stretch="always")
        self.main.add(self.right_pane, stretch="always")
 
        # Drawing events on left canvas only
        left_canvas = self.left_pane.canvas
        left_canvas.bind("<Button-1>", self.start_draw)
        left_canvas.bind("<B1-Motion>", self.paint)
        left_canvas.bind("<ButtonRelease-1>", self.end_draw)
        left_canvas.bind("<Motion>", self.update_pixel_status)
        left_canvas.bind("<Leave>", self.clear_pixel_status)
 
        # Mouse wheel zoom
        left_canvas.bind("<MouseWheel>", self.on_mousewheel_zoom)
        self.right_pane.canvas.bind("<MouseWheel>", self.on_mousewheel_zoom)
 
        # Linux mouse wheel support
        left_canvas.bind("<Button-4>", lambda event: self.zoom_in())
        left_canvas.bind("<Button-5>", lambda event: self.zoom_out())
        self.right_pane.canvas.bind("<Button-4>", lambda event: self.zoom_in())
        self.right_pane.canvas.bind("<Button-5>", lambda event: self.zoom_out())
 
        # Undo last completed stroke
        self.root.bind_all("<Control-z>", self.undo_last_stroke)
        self.root.bind_all("<Control-Z>", self.undo_last_stroke)
 
        # ----------------------------
        # Bottom toolbar
        # ----------------------------
        toolbar = tk.Frame(self.root, padx=6, pady=6)
        toolbar.pack(fill=tk.X)
 
        self.green_btn = tk.Button(
            toolbar,
            image=self.green_icon,
            command=lambda: self.set_marker("green"),
            relief=tk.SUNKEN
        )
        self.green_btn.pack(side=tk.LEFT, padx=4)
 
        self.red_btn = tk.Button(
            toolbar,
            image=self.red_icon,
            command=lambda: self.set_marker("red"),
            relief=tk.RAISED
        )
        self.red_btn.pack(side=tk.LEFT, padx=4)
 
        self.eraser_btn = tk.Button(
            toolbar,
            image=self.eraser_icon,
            command=self.set_eraser,
            relief=tk.RAISED
        )
        self.eraser_btn.pack(side=tk.LEFT, padx=4)
 
        self.zoom_out_btn = tk.Button(
            toolbar,
            image=self.zoom_out_icon,
            command=self.zoom_out
        )
        self.zoom_out_btn.pack(side=tk.LEFT, padx=(20, 4))
 
        self.zoom_in_btn = tk.Button(
            toolbar,
            image=self.zoom_in_icon,
            command=self.zoom_in
        )
        self.zoom_in_btn.pack(side=tk.LEFT, padx=4)
 
        self.zoom_label = tk.Label(toolbar, text="Zoom: 100%", width=12)
        self.zoom_label.pack(side=tk.LEFT, padx=8)
 
        self.image_size_label = tk.Label(
            toolbar,
            text="Image: -",
            width=18,
            anchor="w"
        )
        self.image_size_label.pack(side=tk.LEFT, padx=(20, 4))
 
        self.pixel_label = tk.Label(
            toolbar,
            text="Pixel: -",
            width=18,
            anchor="w"
        )
        self.pixel_label.pack(side=tk.LEFT, padx=4)
 
        tk.Label(toolbar, text="Brush radius:").pack(
            side=tk.LEFT,
            padx=(20, 4)
        )
 
        self.brush_scale = tk.Scale(
            toolbar,
            from_=0,
            to=5,
            orient=tk.HORIZONTAL,
            command=self.set_brush_radius,
            length=120
        )
        self.brush_scale.set(self.brush_radius)
        self.brush_scale.pack(side=tk.LEFT)
 
        tk.Label(toolbar, text="Algorithm:").pack(
            side=tk.LEFT,
            padx=(20, 4)
        )
 
        self.algorithm_dropdown = ttk.Combobox(
            toolbar,
            textvariable=self.selected_algorithm,
            values=self.algorithm_options,
            state="readonly",
            width=18
        )
        self.algorithm_dropdown.pack(side=tk.LEFT, padx=4)
        self.algorithm_dropdown.set("Edmonds-Karp")
 
        self.process_btn = tk.Button(
            toolbar,
            text="Process",
            command=self.process_image
        )
        self.process_btn.pack(side=tk.LEFT, padx=(12, 4))
 
        self.status_label = tk.Label(toolbar, text="", width=28, anchor="w", fg="#555555")
        self.status_label.pack(side=tk.LEFT, padx=(8, 4))
 
    # ============================================================
    # Status animation
    # ============================================================
    def _start_status_animation(self, algorithm_name):
        """Begin the animated 'Calculating...' label."""
        self._status_base = f"Running {algorithm_name}"
        self._status_anim_dots = 0
        self._tick_status()
 
    def _tick_status(self):
        dots = "." * (self._status_anim_dots % 4)
        self.status_label.config(text=self._status_base + dots)
        self._status_anim_dots += 1
        self._status_anim_job = self.root.after(400, self._tick_status)
 
    def _stop_status_animation(self, final_text=""):
        if self._status_anim_job is not None:
            self.root.after_cancel(self._status_anim_job)
            self._status_anim_job = None
        self.status_label.config(text=final_text)
 
    # ============================================================
    # Icons
    # ============================================================
 
    def make_marker_icon(self, color):
        """
        Create a small marker-like colored icon as a Tk PhotoImage.
        No external files needed.
        """
        img = Image.new("RGBA", (36, 28), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
 
        if color == "green":
            fill = (0, 180, 0, 255)
            outline = (0, 90, 0, 255)
        else:
            fill = (220, 0, 0, 255)
            outline = (120, 0, 0, 255)
 
        d.rounded_rectangle(
            [5, 8, 26, 19],
            radius=4,
            fill=fill,
            outline=outline,
            width=2
        )
 
        d.polygon(
            [(26, 10), (34, 14), (26, 18)],
            fill=fill,
            outline=outline
        )
 
        d.line(
            [8, 10, 22, 10],
            fill=(255, 255, 255, 110),
            width=1
        )
 
        return ImageTk.PhotoImage(img)
 
    def make_eraser_icon(self):
        """
        Create a small eraser icon matching the marker button size.
        """
        img = Image.new("RGBA", (36, 28), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
 
        d.rounded_rectangle(
            [7, 8, 28, 20],
            radius=4,
            fill=(245, 190, 210, 255),
            outline=(130, 90, 105, 255),
            width=2
        )
 
        d.rectangle(
            [21, 9, 28, 19],
            fill=(245, 245, 245, 255),
            outline=(130, 130, 130, 255)
        )
 
        d.line(
            [10, 18, 20, 9],
            fill=(180, 120, 140, 255),
            width=2
        )
 
        return ImageTk.PhotoImage(img)
 
    def make_zoom_icon(self, symbol):
        """
        Create a zoom icon matching the marker button size.
        """
        img = Image.new("RGBA", (36, 28), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
 
        d.rounded_rectangle(
            [5, 5, 31, 23],
            radius=4,
            fill=(242, 242, 242, 255),
            outline=(110, 110, 110, 255),
            width=2
        )
 
        if symbol == "+":
            d.line([18, 10, 18, 18], fill=(30, 30, 30, 255), width=3)
            d.line([14, 14, 22, 14], fill=(30, 30, 30, 255), width=3)
        else:
            d.line([14, 14, 22, 14], fill=(30, 30, 30, 255), width=3)
 
        return ImageTk.PhotoImage(img)
 
    # ============================================================
    # Loading
    # ============================================================
    def load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff"),
                ("All files", "*.*")
            ]
        )
 
        if not path:
            return
 
        self.cancel_scheduled_left_view_update()
 
        self.image = Image.open(path).convert("RGBA")
        self.image_width, self.image_height = self.image.size
 
        w = self.image_width
        h = self.image_height
 
        self.image_size_label.config(text=f"Image: {w} x {h} px")
        self.pixel_label.config(text="Pixel: -")
 
        self.result_overlay = None
        self.overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.overlay_draw = ImageDraw.Draw(self.overlay)
        self.overlay_pixels = self.overlay.load()
 
        self.red_mask = bytearray(w * h)
        self.green_mask = bytearray(w * h)
        self.owner_mask = bytearray(w * h)
 
        self.undo_stack = []
        self.current_stroke_changes = None
 
        self.result_image = None
        self.zoom_index = self.zoom_levels.index(1)
 
        self.invalidate_view_caches()
        self.update_all_views(preserve_view=False)
 
    # ============================================================
    # Display helpers
    # ============================================================
    def invalidate_view_caches(self):
        self._left_base_cache = None
        self._left_base_cache_zoom = None
 
    def current_zoom(self):
        return self.zoom_levels[self.zoom_index]
 
    def format_zoom_label(self):
        zoom = self.current_zoom()
 
        if zoom < 1:
            return f"Zoom: {zoom * 100:g}%"
 
        return f"Zoom: {int(zoom * 100)}%"
 
    def safe_zoom_allowed(self, zoom):
        """
        Prevent creating absurdly huge display images.
        """
        if self.image is None:
            return False
 
        w, h = self.image.size
 
        display_w = max(1, int(round(w * zoom)))
        display_h = max(1, int(round(h * zoom)))
 
        return (display_w * display_h) <= self.max_display_pixels
 
    def display_size_for_image(self, pil_image):
        zoom = self.current_zoom()
        w, h = pil_image.size
 
        display_w = max(1, int(round(w * zoom)))
        display_h = max(1, int(round(h * zoom)))
 
        return display_w, display_h
 
    def zoomed_copy(self, pil_image, is_overlay=False):
        """
        Create display-only zoomed version.
        Original image data is never modified.
        """
        zoom = self.current_zoom()
        display_w, display_h = self.display_size_for_image(pil_image)
 
        if is_overlay:
            resample = RESAMPLE_NEAREST
        elif zoom >= 1:
            resample = RESAMPLE_NEAREST
        else:
            resample = RESAMPLE_DOWNSAMPLE
 
        return pil_image.resize(
            (display_w, display_h),
            resample
        )
 
    def get_zoomed_base_for_left(self):
        zoom = self.current_zoom()
 
        if (
            self._left_base_cache is None
            or self._left_base_cache_zoom != zoom
        ):
            self._left_base_cache = self.zoomed_copy(
                self.image,
                is_overlay=False
            )
            self._left_base_cache_zoom = zoom
 
        return self._left_base_cache
 
    def make_left_preview(self):
        base_zoomed = self.get_zoomed_base_for_left()
        overlay_zoomed = self.zoomed_copy(self.overlay, is_overlay=True)
 
        return Image.alpha_composite(
            base_zoomed.convert("RGBA"),
            overlay_zoomed.convert("RGBA")
        )
 
    def update_all_views(self, preserve_view=True):
        if self.image is None:
            return
 
        self.update_left_view(preserve_view=preserve_view)
        self.update_right_view(preserve_view=preserve_view)
        self.zoom_label.config(text=self.format_zoom_label())
 
    def update_left_view(self, preserve_view=True):
        if self.image is None:
            return
 
        preview = self.make_left_preview()
        self.left_pane.show_image(preview, preserve_view=preserve_view)
 
    def update_right_view(self, preserve_view=True):
        """
        Update the right/result pane.
 
        This version supports a custom overlay on top of the right-pane image.
 
        Expected optional attribute:
            self.result_overlay
 
        If self.result_overlay exists and is a PIL RGBA image with the same size
        as the result/base image, it will be alpha-composited on top for display.
 
        Important:
        - This does NOT modify self.result_image.
        - This does NOT modify self.overlay.
        - The overlay is display-only.
        """
 
        if self.image is None:
            return
 
        # ------------------------------------------------------------
        # 1. Choose the base image for the right pane
        # ------------------------------------------------------------
        if self.result_image is None:
            base = Image.new(
                "RGBA",
                (self.image_width, self.image_height),
                (245, 245, 245, 255)
            )
        else:
            base = self.result_image.convert("RGBA")
 
        # ------------------------------------------------------------
        # 2. Optionally apply a custom right-pane overlay
        # ------------------------------------------------------------
        result_overlay = getattr(self, "result_overlay", None)
 
        if result_overlay is not None:
            result_overlay = result_overlay.convert("RGBA")
 
            if result_overlay.size == base.size:
                base = Image.alpha_composite(base, result_overlay)
            else:
                print(
                    "Warning: result_overlay size does not match right-pane image size. "
                    "Displaying result without custom overlay."
                )
 
        # ------------------------------------------------------------
        # 3. Zoom and display
        # ------------------------------------------------------------
        preview_zoomed = self.zoomed_copy(base, is_overlay=False)
        self.right_pane.show_image(preview_zoomed, preserve_view=preserve_view)
 
    # ============================================================
    # Throttled left-pane redraw
    # ============================================================
    def schedule_left_view_update(self):
        if self._left_update_job is None:
            self._left_update_job = self.root.after(
                33,
                self.flush_left_view_update
            )
 
    def flush_left_view_update(self):
        self._left_update_job = None
        self.update_left_view(preserve_view=True)
 
    def cancel_scheduled_left_view_update(self):
        if self._left_update_job is not None:
            try:
                self.root.after_cancel(self._left_update_job)
            except tk.TclError:
                pass
 
            self._left_update_job = None
 
    # ============================================================
    # Pixel status
    # ============================================================
    def update_pixel_status(self, event):
        if self.image is None:
            self.pixel_label.config(text="Pixel: -")
            return
 
        x, y = self.canvas_to_image_coords(event)
 
        if self.inside_image(x, y):
            self.pixel_label.config(text=f"Pixel: {x}, {y}")
        else:
            self.pixel_label.config(text="Pixel: -")
 
    def clear_pixel_status(self, event=None):
        self.pixel_label.config(text="Pixel: -")
 
    # ============================================================
    # Undo support
    # ============================================================
    def begin_stroke(self):
        self.current_stroke_changes = {}
 
    def record_pixel_before_change(self, x, y):
        if self.current_stroke_changes is None:
            return
 
        idx = self.mask_index(x, y)
 
        if idx in self.current_stroke_changes:
            return
 
        self.current_stroke_changes[idx] = (
            self.red_mask[idx],
            self.green_mask[idx],
            self.owner_mask[idx],
            self.overlay_pixels[x, y]
        )
 
    def commit_stroke(self):
        if self.current_stroke_changes:
            self.undo_stack.append(self.current_stroke_changes)
 
        self.current_stroke_changes = None
 
    def undo_last_stroke(self, event=None):
        if self.image is None:
            return
 
        if not self.undo_stack:
            return
 
        self.cancel_scheduled_left_view_update()
 
        stroke = self.undo_stack.pop()
        w = self.image_width
 
        for idx, previous_state in stroke.items():
            old_red, old_green, old_owner, old_overlay_pixel = previous_state
 
            self.red_mask[idx] = old_red
            self.green_mask[idx] = old_green
            self.owner_mask[idx] = old_owner
 
            x = idx % w
            y = idx // w
 
            self.overlay_pixels[x, y] = old_overlay_pixel
 
        self.update_left_view(preserve_view=True)
 
    # ============================================================
    # Drawing
    # ============================================================
    def canvas_to_image_coords(self, event):
        zoom = self.current_zoom()
 
        x_canvas = self.left_pane.canvas.canvasx(event.x)
        y_canvas = self.left_pane.canvas.canvasy(event.y)
 
        x = int(x_canvas / zoom)
        y = int(y_canvas / zoom)
 
        return x, y
 
    def start_draw(self, event):
        if self.image is None:
            return
 
        self.begin_stroke()
        self.update_pixel_status(event)
 
        x, y = self.canvas_to_image_coords(event)
 
        if not self.inside_image(x, y):
            self.last_x = None
            self.last_y = None
            return
 
        self.last_x = x
        self.last_y = y
 
        self.apply_brush_at(x, y)
        self.schedule_left_view_update()
 
    def paint(self, event):
        if self.image is None:
            return
 
        self.update_pixel_status(event)
 
        x, y = self.canvas_to_image_coords(event)
 
        if not self.inside_image(x, y):
            return
 
        if self.last_x is None or self.last_y is None:
            self.last_x = x
            self.last_y = y
 
        self.apply_line_to_masks(self.last_x, self.last_y, x, y)
 
        self.last_x = x
        self.last_y = y
 
        self.schedule_left_view_update()
 
    def end_draw(self, event):
        self.last_x = None
        self.last_y = None
 
        self.commit_stroke()
 
        self.cancel_scheduled_left_view_update()
        self.update_left_view(preserve_view=True)
 
    def inside_image(self, x, y):
        if self.image is None:
            return False
 
        return 0 <= x < self.image_width and 0 <= y < self.image_height
 
    def mask_index(self, x, y):
        return y * self.image_width + x
 
    def apply_line_to_masks(self, x0, y0, x1, y1):
        """
        Bresenham line rasterization.
        Prevents gaps when moving the mouse quickly.
        """
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
 
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
 
        err = dx - dy
 
        while True:
            self.apply_brush_at(x0, y0)
 
            if x0 == x1 and y0 == y1:
                break
 
            e2 = 2 * err
 
            if e2 > -dy:
                err -= dy
                x0 += sx
 
            if e2 < dx:
                err += dx
                y0 += sy
 
    def apply_brush_at(self, cx, cy):
        """
        Applies marker or eraser at an image-space pixel.
        Strokes do not accumulate opacity/intensity.
        """
        if self.image is None:
            return
 
        w = self.image_width
        h = self.image_height
        r = self.brush_radius
 
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if not (0 <= xx < w and 0 <= yy < h):
                    continue
 
                if r == 0:
                    inside = (xx == cx and yy == cy)
                else:
                    inside = ((xx - cx) ** 2 + (yy - cy) ** 2) <= r ** 2
 
                if not inside:
                    continue
 
                idx = self.mask_index(xx, yy)
 
                old_red = self.red_mask[idx]
                old_green = self.green_mask[idx]
                old_owner = self.owner_mask[idx]
 
                new_red = old_red
                new_green = old_green
                new_owner = old_owner
 
                if self.current_tool == "eraser":
                    new_red = 0
                    new_green = 0
                    new_owner = 0
 
                elif self.current_tool == "red":
                    new_red = self.marker_intensity
                    new_owner = 2
 
                elif self.current_tool == "green":
                    new_green = self.marker_intensity
                    new_owner = 1
 
                if (
                    new_red == old_red
                    and new_green == old_green
                    and new_owner == old_owner
                ):
                    continue
 
                self.record_pixel_before_change(xx, yy)
 
                self.red_mask[idx] = new_red
                self.green_mask[idx] = new_green
                self.owner_mask[idx] = new_owner
 
                self.update_overlay_pixel(xx, yy)
 
    def update_overlay_pixel(self, x, y):
        """
        Update exactly one overlay pixel from the mask data.
        Transparency is constant.
        """
        if self.overlay_pixels is None:
            return
 
        idx = self.mask_index(x, y)
        owner = self.owner_mask[idx]
 
        if owner == 2:
            self.overlay_pixels[x, y] = (255, 0, 0, self.marker_alpha)
        elif owner == 1:
            self.overlay_pixels[x, y] = (0, 255, 0, self.marker_alpha)
        else:
            self.overlay_pixels[x, y] = (0, 0, 0, 0)
 
    def redraw_annotation_overlay(self):
        """
        Full overlay rebuild from masks.
        Not used during normal drawing because it is expensive.
        """
        if self.image is None:
            return
 
        w = self.image_width
        h = self.image_height
 
        self.overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        px = self.overlay.load()
 
        for y in range(h):
            row_offset = y * w
 
            for x in range(w):
                idx = row_offset + x
                owner = self.owner_mask[idx]
 
                if owner == 2:
                    px[x, y] = (255, 0, 0, self.marker_alpha)
                elif owner == 1:
                    px[x, y] = (0, 255, 0, self.marker_alpha)
 
        self.overlay_draw = ImageDraw.Draw(self.overlay)
        self.overlay_pixels = self.overlay.load()
 
    # ============================================================
    # Marker / eraser / brush
    # ============================================================
    def set_marker(self, color):
        self.current_color = color
        self.current_tool = color
 
        if color == "green":
            self.green_btn.config(relief=tk.SUNKEN)
            self.red_btn.config(relief=tk.RAISED)
            self.eraser_btn.config(relief=tk.RAISED)
        else:
            self.green_btn.config(relief=tk.RAISED)
            self.red_btn.config(relief=tk.SUNKEN)
            self.eraser_btn.config(relief=tk.RAISED)
 
    def set_eraser(self):
        self.current_tool = "eraser"
 
        self.green_btn.config(relief=tk.RAISED)
        self.red_btn.config(relief=tk.RAISED)
        self.eraser_btn.config(relief=tk.SUNKEN)
 
    def set_brush_radius(self, value):
        self.brush_radius = int(value)
 
    # ============================================================
    # Zoom
    # ============================================================
    def on_mousewheel_zoom(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
 
    def zoom_in(self):
        if self.image is None:
            return
 
        if self.zoom_index >= len(self.zoom_levels) - 1:
            return
 
        candidate_zoom = self.zoom_levels[self.zoom_index + 1]
 
        if not self.safe_zoom_allowed(candidate_zoom):
            messagebox.showinfo(
                "Zoom limit",
                "This zoom level would create a very large preview image."
            )
            return
 
        self.cancel_scheduled_left_view_update()
 
        self.zoom_index += 1
        self.invalidate_view_caches()
        self.update_all_views(preserve_view=True)
 
    def zoom_out(self):
        if self.image is None:
            return
 
        if self.zoom_index <= 0:
            return
 
        candidate_zoom = self.zoom_levels[self.zoom_index - 1]
 
        if not self.safe_zoom_allowed(candidate_zoom):
            return
 
        self.cancel_scheduled_left_view_update()
 
        self.zoom_index -= 1
        self.invalidate_view_caches()
        self.update_all_views(preserve_view=True)
 
    # ============================================================
    # Processing
    # ============================================================
    def get_marked_pixels(self):
                green_pixels = []
                red_pixels = []
 
                for y in range(self.image_height):
                    row_offset = y * self.image_width
 
                    for x in range(self.image_width):
                        idx = row_offset + x
                        owner = self.owner_mask[idx]
 
                        if owner == 1:
                            green_pixels.append((x, y))
                        elif owner == 2:
                            red_pixels.append((x, y))
 
                return green_pixels, red_pixels
 
    def process_image(self):
        """
 
        The selected algorithm is currently read from the dropdown.
        The current demo behavior is:
        - Original image is copied.
        - Pixels owned by red become red.
        - Pixels owned by green become green.
        - Last drawn color dominates because processing uses owner_mask.
 
        """
        if self.image is None:
            return
 
        algorithm = self.selected_algorithm.get()
        print(f"Running algorithm: {algorithm}")
 
        # Clear previous result immediately so the right pane goes blank
        # while the algorithm runs, making it obvious something changed.
        self.result_overlay = None
        self.result_image = None
        self.update_right_view(preserve_view=True)
 
        # Disable button and start animated status label
        self.process_btn.config(state=tk.DISABLED)
        self._start_status_animation(algorithm)
 
        # Snapshot inputs before thread starts so drawing during processing
        # doesn't affect the current run.
        green_pixels, red_pixels = self.get_marked_pixels()
        if len(green_pixels) == 0 or len(red_pixels) == 0:
            messagebox.showwarning(
                "Missing strokes",
                "Before running the algorithm, be sure to mark at least one pixel as foreground and at least one pixel as background"
            )
            overlay = None
            _overlay = overlay
            _error = error
            _elapsed = elapsed
            self.root.after(0, lambda: self._finish_processing(
                image_snapshot, _overlay, algorithm, _error, _elapsed
            ))

        image_snapshot = self.image.copy()
 
        def run():
            overlay = None
            error = None
            elapsed = None
            try:
                from image_loader import image_to_graph
                graph_caps = image_to_graph(image_snapshot, green_pixels, red_pixels)
 
                overlay = Image.new(
                    "RGBA",
                    (self.image_width, self.image_height),
                    (0, 0, 0, 0)
                )
                px = overlay.load()
 
                t_start = time.perf_counter()
 
                if algorithm == "Edmonds-Karp":
                    from graphs import edmonds_karp, min_cut
 
                    mf, fl = edmonds_karp(graph_caps, 's', 't')
                    S, T, cut = min_cut(graph_caps, fl, 's')
 
                    print("S is now:", S)
 
                    for y in range(self.image_height):
                        for x in range(self.image_width):
                            if (x, y) in S:
                                px[x, y] = (0, 255, 0, 100)
                            if (x, y) in T:
                                px[x, y] = (255, 0, 0, 100)
 
                elif algorithm == "Boykov-Kolmogorov":
                    from boykov_kolmogorov import boykov_kolmogorov
 
                    mf, fl, S, T = boykov_kolmogorov(graph_caps, 's', 't')
 
                    print("S is now:", S)
 
                    for y in range(self.image_height):
                        for x in range(self.image_width):
                            if (x, y) in S:
                                px[x, y] = (0, 255, 0, 100)
                            elif (x, y) in T:
                                px[x, y] = (255, 0, 0, 100)
 
                else:
                    print("Unknown algorithm!")
                    overlay = None
 
                elapsed = time.perf_counter() - t_start
                print(f"--- [TIMER DEB_UG] {algorithm} took {elapsed:.4f} seconds ---")
 
            except Exception as e:
                error = e
                import traceback
                traceback.print_exc()
 
            finally:
                _overlay = overlay
                _error = error
                _elapsed = elapsed
                self.root.after(0, lambda: self._finish_processing(
                    image_snapshot, _overlay, algorithm, _error, _elapsed
                ))
 
        threading.Thread(target=run, daemon=True).start()
 
    def _finish_processing(self, image_snapshot, overlay, algorithm, error=None, elapsed=None):
        # Always re-enable the button regardless of success or failure
        self.process_btn.config(state=tk.NORMAL)
 
        if error is not None:
            self._stop_status_animation(final_text="Error — see console")
            return
 
        if elapsed is not None:
            final_text = f"{algorithm} done ({elapsed:.2f}s)"
        else:
            final_text = f"{algorithm} done"
 
        self._stop_status_animation(final_text=final_text)
 
        w = self.image_width
        h = self.image_height
 
        result = image_snapshot.copy()
        px = result.load()
 
        self.result_overlay = overlay
        self.result_image = result
        self.update_right_view(preserve_view=True)
 
 
def create_app_icon():
    """
    Create a nicer app icon directly in code using Pillow.
    No external image file required.
    """
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
 
    # App tile background
    d.rounded_rectangle(
        [6, 6, 58, 58],
        radius=12,
        fill=(245, 245, 245, 255),
        outline=(70, 70, 70, 255),
        width=3
    )
 
    # Tiny pixel grid
    grid_color = (210, 210, 210, 255)
    for x in range(16, 49, 8):
        d.line([x, 16, x, 48], fill=grid_color, width=1)
    for y in range(16, 49, 8):
        d.line([16, y, 48, y], fill=grid_color, width=1)
 
    # Green marker stroke
    d.line(
        [16, 42, 24, 34, 31, 38, 40, 24],
        fill=(0, 180, 0, 255),
        width=6
    )
 
    # Red marker stroke
    d.line(
        [18, 20, 28, 28, 38, 22, 48, 34],
        fill=(220, 0, 0, 255),
        width=6
    )
 
    # Small black outline pixels
    d.rectangle([15, 15, 49, 49], outline=(60, 60, 60, 255), width=2)
 
    return ImageTk.PhotoImage(img)
 
 
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x700")
 
    app = PixelAnnotationApp(root)
 
 
    root.app_icon = create_app_icon()
    root.iconphoto(True, root.app_icon)
 
 
    root.mainloop()