import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk, ImageOps
import os
import ttkbootstrap as ttkbs
from ttkbootstrap.constants import *
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

class ImageViewer(ttk.Frame):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title = title
        self.image = None
        self.photo = None
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        # Create UI
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        ttk.Label(self, text=self.title, font=('Helvetica', 10, 'bold')).pack(pady=(0, 5))
        
        # Canvas for image display
        self.canvas = tk.Canvas(self, bg='#2d2d2d', bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbars
        self.h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)
        
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse events for panning
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.pan)
        self.canvas.bind("<MouseWheel>", self.zoom_image)  # Windows/Mac
        self.canvas.bind("<Button-4>", self.zoom_image)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.zoom_image)    # Linux scroll down
    
    def set_image(self, cv_img):
        if cv_img is None:
            return
            
        self.image = cv_img
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.update_display()
    
    def update_display(self):
        if self.image is None:
            return
            
        # Convert OpenCV BGR to RGB
        img_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        
        # Apply zoom and pan
        h, w = img_rgb.shape[:2]
        new_h, new_w = int(h * self.zoom), int(w * self.zoom)
        
        # Resize image
        img_resized = cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Convert to PhotoImage
        img_pil = Image.fromarray(img_resized)
        self.photo = ImageTk.PhotoImage(image=img_pil)
        
        # Update canvas
        self.canvas.delete("all")
        self.canvas.create_image(
            self.pan_x, self.pan_y, 
            anchor=tk.NW, 
            image=self.photo
        )
        
        # Update scroll region
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
    
    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)
    
    def pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.pan_x = -self.canvas.canvasx(0)
        self.pan_y = -self.canvas.canvasy(0)
    
    def zoom_image(self, event):
        # Zoom in/out with mouse wheel
        if event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            self.zoom = max(0.1, self.zoom * 0.9)
        elif event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            self.zoom = min(3.0, self.zoom * 1.1)
        
        self.update_display()

class PhotoFilterApp(ttkbs.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Advanced Photo Filter App")
        
        # Configure window
        self.geometry("1400x900")
        self.minsize(1000, 700)
        self.center_window()
        
        # Initialize variables
        self.original_image = None
        self.filtered_image = None
        self.cap = None
        self.is_webcam_active = False
        self.current_filter = "original"
        self.filter_params = {
            "box_blur": {"kernel_size": 5},
            "gaussian_blur": {"kernel_size": 5, "sigma": 1.0},
            "sharpen": {"amount": 1.0},
            "sobel": {"kernel_size": 3},
            "canny": {"threshold1": 80, "threshold2": 150}
        }
        
        # Create UI
        self.setup_ui()
        
        # Start with webcam if available
        self.toggle_webcam()
    
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        # Main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Controls
        self.control_frame = ttk.LabelFrame(self.main_frame, text="Controls", padding=10)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Right panel - Image views
        self.view_frame = ttk.Frame(self.main_frame)
        self.view_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create image viewers
        self.original_view = ImageViewer(self.view_frame, "Original")
        self.original_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.filtered_view = ImageViewer(self.view_frame, "Filtered")
        self.filtered_view.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Add divider
        self.divider = ttk.Separator(self.view_frame, orient=tk.VERTICAL)
        self.divider.pack(fill=tk.Y, padx=5)
        
        # Add controls
        self.setup_controls()
    
    def setup_controls(self):
        # Source controls
        ttk.Label(self.control_frame, text="Source:", font=('Helvetica', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        btn_frame = ttk.Frame(self.control_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="📁 Open Image", 
                  command=self.load_image, 
                  style='primary.TButton').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.webcam_btn = ttk.Button(btn_frame, text="🎥 Webcam Off", 
                                    command=self.toggle_webcam,
                                    style='secondary.TButton')
        self.webcam_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Filters
        ttk.Separator(self.control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(self.control_frame, text="Filters:", font=('Helvetica', 10, 'bold')).pack(anchor='w')
        
        # Filter buttons
        filters = [
            ("Original (1)", "original"),
            ("Box Blur (2)", "box_blur"),
            ("Gaussian Blur (3)", "gaussian_blur"),
            ("Sharpen (4)", "sharpen"),
            ("Sobel Edge (5)", "sobel"),
            ("Canny Edge (6)", "canny")
        ]
        
        for text, filter_name in filters:
            btn = ttk.Button(
                self.control_frame, 
                text=text,
                command=lambda f=filter_name: self.set_filter(f),
                style='outline.TButton'
            )
            btn.pack(fill=tk.X, pady=2)
        
        # Filter parameters
        self.setup_filter_params()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(
            self.control_frame, 
            textvariable=self.status_var,
            style='secondary.TLabel'
        ).pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
    
    def setup_filter_params(self):
        # Parameters frame
        self.param_frame = ttk.LabelFrame(self.control_frame, text="Parameters", padding=10)
        self.param_frame.pack(fill=tk.X, pady=10)
        
        # Box Blur
        ttk.Label(self.param_frame, text="Box Kernel Size:").grid(row=0, column=0, sticky='w')
        self.box_kernel_var = tk.StringVar(value="5x5")
        ttk.Combobox(
            self.param_frame, 
            textvariable=self.box_kernel_var,
            values=["3x3", "5x5", "7x7", "9x9", "11x11"],
            state='readonly',
            width=8
        ).grid(row=0, column=1, sticky='e', pady=2)
        
        # Gaussian Blur
        ttk.Label(self.param_frame, text="Gaussian Kernel:").grid(row=1, column=0, sticky='w')
        self.gaussian_kernel_var = tk.StringVar(value="5x5")
        ttk.Combobox(
            self.param_frame, 
            textvariable=self.gaussian_kernel_var,
            values=["3x3", "5x5", "7x7", "9x9"],
            state='readonly',
            width=8
        ).grid(row=1, column=1, sticky='e', pady=2)
        
        ttk.Label(self.param_frame, text="Sigma:").grid(row=2, column=0, sticky='w')
        self.sigma_scale = ttk.Scale(
            self.param_frame, 
            from_=0.1, 
            to=5.0, 
            value=1.0,
            command=lambda v: self.update_param("gaussian_blur", "sigma", float(v))
        )
        self.sigma_scale.grid(row=2, column=1, sticky='ew', pady=2)
        
        # Canny
        ttk.Label(self.param_frame, text="Canny Threshold 1:").grid(row=3, column=0, sticky='w')
        self.canny1_scale = ttk.Scale(
            self.param_frame, 
            from_=0, 
            to=255, 
            value=80,
            command=lambda v: self.update_param("canny", "threshold1", int(float(v)))
        )
        self.canny1_scale.grid(row=3, column=1, sticky='ew', pady=2)
        
        ttk.Label(self.param_frame, text="Canny Threshold 2:").grid(row=4, column=0, sticky='w')
        self.canny2_scale = ttk.Scale(
            self.param_frame, 
            from_=0, 
            to=255, 
            value=150,
            command=lambda v: self.update_param("canny", "threshold2", int(float(v)))
        )
        self.canny2_scale.grid(row=4, column=1, sticky='ew', pady=2)
    
    def update_param(self, filter_name, param, value):
        if filter_name in self.filter_params and param in self.filter_params[filter_name]:
            self.filter_params[filter_name][param] = value
            self.apply_filter()
    
    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tif"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.stop_webcam()
                self.original_image = cv2.imread(file_path)
                if self.original_image is not None:
                    self.is_webcam_active = False
                    self.webcam_btn.config(text="🎥 Webcam Off")
                    self.status_var.set(f"Loaded: {os.path.basename(file_path)}")
                    self.update_views()
                else:
                    raise Exception("Failed to load image")
            except Exception as e:
                self.status_var.set(f"Error: {str(e)}")
                logging.error(f"Error loading image: {str(e)}")
    
    def toggle_webcam(self):
        if self.is_webcam_active:
            self.stop_webcam()
            self.webcam_btn.config(text="🎥 Webcam Off")
        else:
            self.start_webcam()
            self.webcam_btn.config(text="🎥 Webcam On")
    
    def start_webcam(self):
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Could not open webcam")
                
            self.is_webcam_active = True
            self.status_var.set("Webcam activated")
            self.update_webcam()
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            logging.error(f"Webcam error: {str(e)}")
            self.is_webcam_active = False
    
    def stop_webcam(self):
        self.is_webcam_active = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.original_image = None
    
    def update_webcam(self):
        if self.is_webcam_active and self.cap is not None:
            ret, frame = self.cap.read()
            if ret:
                self.original_image = frame
                self.update_views()
            self.after(10, self.update_webcam)
    
    def set_filter(self, filter_name):
        self.current_filter = filter_name
        self.status_var.set(f"Filter: {filter_name.replace('_', ' ').title()}")
        self.apply_filter()
    
    def apply_filter(self):
        if self.original_image is None:
            return
            
        try:
            if self.current_filter == "original":
                self.filtered_image = self.original_image.copy()
            
            elif self.current_filter == "box_blur":
                ksize = int(self.box_kernel_var.get().split('x')[0])
                self.filtered_image = cv2.blur(self.original_image, (ksize, ksize))
            
            elif self.current_filter == "gaussian_blur":
                ksize = int(self.gaussian_kernel_var.get().split('x')[0])
                ksize = ksize if ksize % 2 != 0 else ksize + 1
                sigma = self.filter_params["gaussian_blur"]["sigma"]
                self.filtered_image = cv2.GaussianBlur(
                    self.original_image, 
                    (ksize, ksize), 
                    sigmaX=sigma
                )
            
            elif self.current_filter == "sharpen":
                kernel = np.array([
                    [-1, -1, -1],
                    [-1,  9, -1],
                    [-1, -1, -1]
                ])
                self.filtered_image = cv2.filter2D(self.original_image, -1, kernel)
            
            elif self.current_filter == "sobel":
                gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
                sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
                sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
                sobel = cv2.magnitude(sobelx, sobely)
                self.filtered_image = cv2.normalize(sobel, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
                self.filtered_image = cv2.cvtColor(self.filtered_image, cv2.COLOR_GRAY2BGR)
            
            elif self.current_filter == "canny":
                gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
                t1 = self.filter_params["canny"]["threshold1"]
                t2 = self.filter_params["canny"]["threshold2"]
                edges = cv2.Canny(gray, t1, t2)
                self.filtered_image = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            
            self.update_views()
            
        except Exception as e:
            self.status_var.set(f"Filter error: {str(e)}")
            logging.error(f"Filter error: {str(e)}")
    
    def update_views(self):
        if self.original_image is not None:
            self.original_view.set_image(self.original_image)
            
            if self.filtered_image is not None:
                self.filtered_view.set_image(self.filtered_image)
            else:
                self.filtered_view.set_image(self.original_image)
    
    def on_closing(self):
        self.stop_webcam()
        self.destroy()

if __name__ == "__main__":
    try:
        app = PhotoFilterApp()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
    except Exception as e:
        logging.error(f"Application error: {str(e)}", exc_info=True)
