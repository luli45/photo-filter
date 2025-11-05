import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk, ImageOps
import os
import logging
from datetime import datetime
from typing import Union, Tuple, Optional

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
        
        # Canvas for image display with custom style
        style = ttk.Style()
        style.configure('Custom.TFrame', background='#2d2d2d')
        
        self.canvas_frame = ttk.Frame(self, style='Custom.TFrame')
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(
            self.canvas_frame, 
            bg='#2d2d2d', 
            bd=0, 
            highlightthickness=0,
            relief='ridge'
        )
        
        # Add scrollbars
        self.h_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.v_scroll.grid(row=0, column=1, sticky='ns')
        self.h_scroll.grid(row=1, column=0, sticky='ew')
        
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Bind mouse events
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
            
        try:
            # Convert OpenCV BGR to RGB
            if len(self.image.shape) == 2:  # Grayscale
                img_rgb = cv2.cvtColor(self.image, cv2.COLOR_GRAY2RGB)
            else:  # BGR
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
                self.pan_x, 
                self.pan_y, 
                anchor=tk.NW, 
                image=self.photo
            )
            
            # Update scroll region
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
            
        except Exception as e:
            logging.error(f"Error updating display: {str(e)}")
    
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

class PhotoFilterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Modern Photo Filter App")
        self.geometry("1400x900")
        self.minsize(1000, 700)
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
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
        self.after(100, self.toggle_webcam)
    
    def configure_styles(self):
        # Modern color palette
        self.bg_color = '#1a1a2e'  # Dark blue-gray
        self.secondary_bg = '#16213e'  # Slightly lighter blue-gray
        self.accent_color = '#0f3460'  # Deep blue
        self.highlight_color = '#00b4d8'  # Bright cyan
        self.text_color = '#e8f1f5'  # Off-white
        self.button_bg = '#2a9d8f'  # Teal
        self.button_hover = '#21867a'  # Darker teal
        self.button_active = '#1a6b5e'  # Even darker teal
        
        # Configure base styles
        self.style.configure('.', 
                           background=self.bg_color,
                           foreground=self.text_color,
                           font=('Segoe UI', 10))
        
        # Configure main window
        self.configure(bg=self.bg_color)
        
        # Configure frames
        self.style.configure('TFrame', 
                           background=self.bg_color,
                           relief='flat')
        
        # Configure labels
        self.style.configure('TLabel', 
                           background=self.bg_color,
                           foreground=self.text_color,
                           font=('Segoe UI', 9))
        
        # Configure buttons with modern flat design
        self.style.configure('TButton',
                           background=self.button_bg,
                           foreground='white',
                           borderwidth=0,
                           focuscolor='none',
                           font=('Segoe UI', 9, 'bold'),
                           padding=8,
                           relief='flat',
                           borderradius=4)
        
        # Button states
        self.style.map('TButton',
                      background=[('active', self.button_hover),
                                ('pressed', self.button_active)],
                      foreground=[('active', 'white'),
                                ('pressed', 'white')],
                      relief=[('pressed', 'sunken'),
                            ('!pressed', 'flat')])
        
        # Configure labelframe with modern styling
        self.style.configure('TLabelframe',
                           background=self.secondary_bg,
                           foreground=self.highlight_color,
                           bordercolor=self.accent_color,
                           relief='flat',
                           padding=(10, 5, 10, 10),
                           borderwidth=1)
                           
        self.style.configure('TLabelframe.Label',
                           background=self.secondary_bg,
                           foreground=self.highlight_color,
                           font=('Segoe UI', 10, 'bold'),
                           padding=(0, 0, 5, 5))
        
        # Modern scrollbars
        self.style.configure('TScrollbar',
                           background=self.accent_color,
                           troughcolor=self.secondary_bg,
                           arrowcolor=self.text_color,
                           bordercolor=self.bg_color,
                           gripcount=0,
                           arrowsize=12,
                           width=12)
                           
        self.style.map('TScrollbar',
                     background=[('active', self.highlight_color)])
        
        # Modern combobox
        self.style.map('TCombobox',
                      fieldbackground=[('readonly', self.secondary_bg)],
                      selectbackground=[('readonly', self.accent_color)],
                      selectforeground=[('readonly', self.text_color)],
                      background=[('readonly', self.secondary_bg)],
                      foreground=[('readonly', self.text_color)],
                      arrowcolor=[('', self.text_color)])
        
        # Modern scale/slider
        self.style.configure('Horizontal.TScale',
                           background=self.secondary_bg,
                           troughcolor=self.accent_color,
                           bordercolor=self.highlight_color,
                           lightcolor=self.highlight_color,
                           darkcolor=self.highlight_color,
                           sliderthickness=12)
        
        # Custom style for active filter button
        self.style.configure('Active.TButton',
                           background=self.highlight_color,
                           foreground='white',
                           font=('Segoe UI', 9, 'bold'))
        
        # Configure separator
        self.style.configure('TSeparator',
                           background=self.accent_color)
    
    def setup_ui(self):
        # Main container with gradient background
        self.main_frame = ttk.Frame(self, style='TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Left panel - Controls with card-like appearance
        self.control_frame = ttk.LabelFrame(
            self.main_frame, 
            text="  CONTROLS  ",  # Extra spaces for padding
            padding=(15, 10, 15, 15),
            style='TLabelframe'
        )
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        
        # Right panel - Image views with card-like appearance
        self.view_frame = ttk.Frame(
            self.main_frame,
            style='Card.TFrame'  # Will be configured in configure_styles
        )
        self.view_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create a container for the image viewers
        self.viewer_container = ttk.Frame(self.view_frame, style='TFrame')
        self.viewer_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Create image viewers with modern styling
        self.original_view = ImageViewer(self.viewer_container, "ORIGINAL")
        self.original_view.pack(
            side=tk.LEFT, 
            fill=tk.BOTH, 
            expand=True, 
            padx=(0, 1), 
            pady=1
        )
        
        # Add modern vertical separator
        separator = ttk.Separator(
            self.viewer_container, 
            orient=tk.VERTICAL,
            style='TSeparator'
        )
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=3)
        
        self.filtered_view = ImageViewer(self.viewer_container, "FILTERED")
        self.filtered_view.pack(
            side=tk.LEFT, 
            fill=tk.BOTH, 
            expand=True, 
            padx=(1, 0), 
            pady=1
        )
        
        # Add controls with modern styling
        self.setup_controls()
        
        # Add a subtle drop shadow effect to the control panel
        self.style.configure('Card.TFrame',
                           background=self.secondary_bg,
                           relief='sunken',
                           borderwidth=1)
    
    def setup_controls(self):
        # Source controls section
        source_frame = ttk.LabelFrame(
            self.control_frame,
            text="  SOURCE  ",
            padding=10,
            style='TLabelframe'
        )
        source_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Modern button frame with consistent spacing
        btn_frame = ttk.Frame(source_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Modern icon buttons with hover effects
        self.load_btn = ttk.Button(
            btn_frame, 
            text="📂  Open Image",
            command=self.load_image,
            style='TButton'
        )
        self.load_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.webcam_btn = ttk.Button(
            btn_frame, 
            text="🎥  Webcam Off",
            command=self.toggle_webcam,
            style='TButton'
        )
        self.webcam_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Filters section with modern card style
        filter_frame = ttk.LabelFrame(
            self.control_frame,
            text="  FILTERS  ",
            padding=10,
            style='TLabelframe'
        )
        filter_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Filter buttons with icons and keyboard shortcuts
        filters = [
            ("🖼️  Original (1)", "original"),
            ("🔲  Box Blur (2)", "box_blur"),
            ("🌫️  Gaussian Blur (3)", "gaussian_blur"),
            ("✨  Sharpen (4)", "sharpen"),
            ("🔳  Sobel Edge (5)", "sobel"),
            ("🔍  Canny Edge (6)", "canny")
        ]
        
        for i, (text, filter_name) in enumerate(filters):
            btn = ttk.Button(
                filter_frame, 
                text=text,
                command=lambda f=filter_name: self.set_filter(f),
                style='TButton'
            )
            btn.pack(fill=tk.X, pady=3)
            
            # Store reference to style the active filter
            if filter_name == 'original':
                self.active_filter_btn = btn
        
        # Filter parameters
        self.setup_filter_params()
        
        # Status bar with modern styling
        status_frame = ttk.Frame(self.control_frame, style='Status.TFrame')
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(15, 0))
        
        # Add a subtle top border
        ttk.Separator(
            status_frame, 
            orient=tk.HORIZONTAL,
            style='TSeparator'
        ).pack(fill=tk.X, pady=(0, 5))
        
        self.status_var = tk.StringVar()
        self.status_var.set("🟢 Ready")
        
        ttk.Label(
            status_frame, 
            textvariable=self.status_var,
            style='Status.TLabel'
        ).pack(side=tk.LEFT, fill=tk.X, pady=2)
        
        # Configure status bar style
        self.style.configure('Status.TFrame',
                           background=self.secondary_bg)
                           
        self.style.configure('Status.TLabel',
                           background=self.secondary_bg,
                           foreground=self.highlight_color,
                           font=('Segoe UI', 8),
                           padding=(5, 2))
        
        # Bind keyboard shortcuts
        self.bind('<Key>', self.handle_keypress)
    
    def setup_filter_params(self):
        # Parameters frame
        self.param_frame = ttk.LabelFrame(self.control_frame, text="Parameters", padding=10)
        self.param_frame.pack(fill=tk.X, pady=10)
        
        # Box Blur
        ttk.Label(self.param_frame, text="Box Kernel Size:").grid(row=0, column=0, sticky='w', pady=2)
        self.box_kernel_var = tk.StringVar(value="5x5")
        ttk.Combobox(
            self.param_frame, 
            textvariable=self.box_kernel_var,
            values=["3x3", "5x5", "7x7", "9x9", "11x11"],
            state='readonly',
            width=8
        ).grid(row=0, column=1, sticky='e', pady=2)
        
        # Gaussian Blur
        ttk.Label(self.param_frame, text="Gaussian Kernel:").grid(row=1, column=0, sticky='w', pady=2)
        self.gaussian_kernel_var = tk.StringVar(value="5x5")
        ttk.Combobox(
            self.param_frame, 
            textvariable=self.gaussian_kernel_var,
            values=["3x3", "5x5", "7x7", "9x9"],
            state='readonly',
            width=8
        ).grid(row=1, column=1, sticky='e', pady=2)
        
        ttk.Label(self.param_frame, text="Sigma:").grid(row=2, column=0, sticky='w', pady=2)
        self.sigma_scale = ttk.Scale(
            self.param_frame, 
            from_=0.1, 
            to=5.0, 
            value=1.0,
            command=lambda v: self.update_param("gaussian_blur", "sigma", float(v))
        )
        self.sigma_scale.grid(row=2, column=1, sticky='ew', pady=2)
        
        # Canny
        ttk.Label(self.param_frame, text="Canny Threshold 1:").grid(row=3, column=0, sticky='w', pady=2)
        self.canny1_scale = ttk.Scale(
            self.param_frame, 
            from_=0, 
            to=255, 
            value=80,
            command=lambda v: self.update_param("canny", "threshold1", int(float(v)))
        )
        self.canny1_scale.grid(row=3, column=1, sticky='ew', pady=2)
        
        ttk.Label(self.param_frame, text="Canny Threshold 2:").grid(row=4, column=0, sticky='w', pady=2)
        self.canny2_scale = ttk.Scale(
            self.param_frame, 
            from_=0, 
            to=255, 
            value=150,
            command=lambda v: self.update_param("canny", "threshold2", int(float(v)))
        )
        self.canny2_scale.grid(row=4, column=1, sticky='ew', pady=2)
        
        # Configure grid weights
        self.param_frame.columnconfigure(1, weight=1)
    
    def handle_keypress(self, event):
        # Map number keys to filters
        key_mapping = {
            '1': 'original',
            '2': 'box_blur',
            '3': 'gaussian_blur',
            '4': 'sharpen',
            '5': 'sobel',
            '6': 'canny'
        }
        
        if event.char in key_mapping:
            self.set_filter(key_mapping[event.char])
    
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
                    self.apply_filter()
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
                self.apply_filter()
            self.after(10, self.update_webcam)
    
    def set_filter(self, filter_name):
        # Reset previous active button style
        if hasattr(self, 'active_filter_btn'):
            self.active_filter_btn.configure(style='TButton')
        
        # Update current filter and UI
        self.current_filter = filter_name
        self.status_var.set(f"🔄 Applying {filter_name.replace('_', ' ').title()} filter...")
        self.update_idletasks()
        
        # Apply the filter
        self.apply_filter()
        
        # Update active button style
        for child in self.control_frame.winfo_children():
            if isinstance(child, ttk.Button) and filter_name in child.cget('text').lower():
                child.configure(style='Active.TButton')
                self.active_filter_btn = child
                break
                
        self.status_var.set(f"✅ {filter_name.replace('_', ' ').title()} filter applied")
    
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
