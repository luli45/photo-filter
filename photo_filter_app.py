import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import os

class PhotoFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Image Filter App")
        
        # Set window size and position
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 1200
        window_height = 800
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # Set window to be on top
        self.root.attributes('-topmost', 1)
        self.root.after(100, lambda: self.root.attributes('-topmost', 0))
        
        # Initialize video capture
        self.cap = None
        self.video_source = 0  # Default to webcam
        self.is_image = False
        self.original_image = None
        
        # Filter parameters
        self.current_filter = "original"
        self.box_kernel_size = 5
        self.gaussian_kernel_size = 5
        self.gaussian_sigma = 1.0
        self.canny_threshold1 = 80
        self.canny_threshold2 = 150
        self.sobel_kernel = 3
        
        # Create GUI
        self.setup_gui()
        
        # Start with webcam by default
        self.toggle_webcam()
        
    def setup_gui(self):
        # Create main frames
        self.control_frame = ttk.LabelFrame(self.root, text="Controls", padding="5")
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        self.preview_frame = ttk.LabelFrame(self.root, text="Preview", padding="5")
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input Source Controls
        ttk.Label(self.control_frame, text="Input Source:").grid(row=0, column=0, sticky='w')
        ttk.Button(self.control_frame, text="Load Image", command=self.load_image).grid(row=1, column=0, sticky='ew', pady=2)
        ttk.Button(self.control_frame, text="Toggle Webcam", command=self.toggle_webcam).grid(row=2, column=0, sticky='ew', pady=2)
        
        # Filter Selection
        ttk.Separator(self.control_frame, orient='horizontal').grid(row=3, column=0, sticky='ew', pady=10)
        ttk.Label(self.control_frame, text="Filters:").grid(row=4, column=0, sticky='w')
        
        filter_buttons = [
            ("Original (1)", "original"),
            ("Box Blur (B)", "box_blur"),
            ("Gaussian Blur (G)", "gaussian_blur"),
            ("Sharpen (S)", "sharpen"),
            ("Sobel Edge (O)", "sobel"),
            ("Canny Edge (C)", "canny")
        ]
        
        for i, (text, filter_name) in enumerate(filter_buttons, 5):
            ttk.Button(self.control_frame, text=text, 
                      command=lambda f=filter_name: self.set_filter(f)).grid(row=i, column=0, sticky='ew', pady=2)
        
        # Filter Parameters
        self.param_frame = ttk.LabelFrame(self.control_frame, text="Parameters")
        self.param_frame.grid(row=11, column=0, sticky='ew', pady=10)
        
        # Box Blur Parameters
        ttk.Label(self.param_frame, text="Box Kernel Size:").grid(row=0, column=0, sticky='w')
        self.box_kernel_var = tk.StringVar(value="5x5")
        ttk.Combobox(self.param_frame, textvariable=self.box_kernel_var, 
                    values=["3x3", "5x5", "7x7", "11x11"], state='readonly').grid(row=0, column=1)
        
        # Gaussian Blur Parameters
        ttk.Label(self.param_frame, text="Gaussian Kernel:").grid(row=1, column=0, sticky='w')
        self.gaussian_kernel_var = tk.StringVar(value="5x5")
        ttk.Combobox(self.param_frame, textvariable=self.gaussian_kernel_var, 
                    values=["3x3", "5x5", "7x7", "9x9"], state='readonly').grid(row=1, column=1)
        
        ttk.Label(self.param_frame, text="Sigma:").grid(row=2, column=0, sticky='w')
        self.sigma_scale = ttk.Scale(self.param_frame, from_=0.1, to=5.0, value=1.0, 
                                   command=lambda v: setattr(self, 'gaussian_sigma', float(v)))
        self.sigma_scale.grid(row=2, column=1, sticky='ew')
        
        # Canny Parameters
        ttk.Label(self.param_frame, text="Canny Thresh 1:").grid(row=3, column=0, sticky='w')
        self.canny1_scale = ttk.Scale(self.param_frame, from_=0, to=255, value=80,
                                    command=lambda v: setattr(self, 'canny_threshold1', int(float(v))))
        self.canny1_scale.grid(row=3, column=1, sticky='ew')
        
        ttk.Label(self.param_frame, text="Canny Thresh 2:").grid(row=4, column=0, sticky='w')
        self.canny2_scale = ttk.Scale(self.param_frame, from_=0, to=255, value=150,
                                    command=lambda v: setattr(self, 'canny_threshold2', int(float(v))))
        self.canny2_scale.grid(row=4, column=1, sticky='ew')
        
        # Preview Label
        self.preview_label = ttk.Label(self.preview_frame)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind keyboard shortcuts
        self.root.bind('1', lambda e: self.set_filter("original"))
        self.root.bind('b', lambda e: self.set_filter("box_blur"))
        self.root.bind('g', lambda e: self.set_filter("gaussian_blur"))
        self.root.bind('s', lambda e: self.set_filter("sharpen"))
        self.root.bind('o', lambda e: self.set_filter("sobel"))
        self.root.bind('c', lambda e: self.set_filter("canny"))
        self.root.bind('p', lambda e: self.set_filter("original"))
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    # Image processing methods
    def apply_box_blur(self, frame):
        """Apply box blur with adjustable kernel size"""
        ksize = int(self.box_kernel_var.get().split('x')[0])
        return cv2.blur(frame, (ksize, ksize))
    
    def apply_gaussian_blur(self, frame):
        """Apply Gaussian blur with adjustable kernel size and sigma"""
        ksize = int(self.gaussian_kernel_var.get().split('x')[0])
        ksize = ksize if ksize % 2 != 0 else ksize + 1  # Ensure odd kernel size
        return cv2.GaussianBlur(frame, (ksize, ksize), self.gaussian_sigma)
    
    def apply_sharpen(self, frame):
        """Apply sharpening filter"""
        kernel = np.array([[-1,-1,-1], 
                          [-1, 9,-1],
                          [-1,-1,-1]])
        return cv2.filter2D(frame, -1, kernel)
    
    def apply_sobel(self, frame):
        """Apply Sobel edge detection"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=self.sobel_kernel)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=self.sobel_kernel)
        sobel = cv2.magnitude(sobelx, sobely)
        return cv2.normalize(sobel, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    
    def apply_canny(self, frame):
        """Apply Canny edge detection with adjustable thresholds"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.Canny(gray, self.canny_threshold1, self.canny_threshold2)
    
    def apply_filter(self, frame):
        """Apply the current filter to the frame"""
        if self.current_filter == "box_blur":
            return self.apply_box_blur(frame)
        elif self.current_filter == "gaussian_blur":
            return self.apply_gaussian_blur(frame)
        elif self.current_filter == "sharpen":
            return self.apply_sharpen(frame)
        elif self.current_filter == "sobel":
            return self.apply_sobel(frame)
        elif self.current_filter == "canny":
            return self.apply_canny(frame)
        return frame
    
    # GUI and control methods
    def load_image(self):
        """Load an image from file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tif")]
        )
        if file_path:
            self.is_image = True
            if self.cap is not None:
                self.cap.release()
            self.original_image = cv2.imread(file_path)
            if self.original_image is not None:
                self.status_var.set(f"Loaded: {os.path.basename(file_path)}")
                self.update_preview()
    
    def toggle_webcam(self):
        """Toggle between webcam and no video source"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.is_image = False
            self.original_image = None
            self.status_var.set("Webcam deactivated")
            self.update_preview()
            return
        
        try:
            # Try different backends for macOS compatibility
            for backend in [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY]:
                self.cap = cv2.VideoCapture(0, backend)
                if self.cap.isOpened():
                    # Test if we can actually read a frame
                    ret, frame = self.cap.read()
                    if ret:
                        self.is_image = False
                        self.status_var.set("Webcam activated")
                        self.update_preview()
                        return
                    else:
                        self.cap.release()
                        self.cap = None
            
            # If we get here, no backend worked
            raise Exception("Could not access webcam")
            
        except Exception as e:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            self.status_var.set(f"Error: {str(e)}")
            self.root.bell()  # Make a sound to alert the user
    
    def set_filter(self, filter_name):
        """Set the current filter"""
        self.current_filter = filter_name
        self.status_var.set(f"Filter: {filter_name.replace('_', ' ').title()}")
    
    def update_preview(self):
        """Update the preview with the current frame and filter"""
        if self.is_image and self.original_image is not None:
            frame = self.original_image.copy()
        elif self.cap is not None:
            ret, frame = self.cap.read()
            if not ret:
                return
        else:
            return
        
        # Apply current filter
        filtered_frame = self.apply_filter(frame)
        
        # Convert to RGB for display
        if len(filtered_frame.shape) == 2:  # Grayscale
            filtered_frame = cv2.cvtColor(filtered_frame, cv2.COLOR_GRAY2RGB)
        else:  # BGR to RGB
            filtered_frame = cv2.cvtColor(filtered_frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PhotoImage
        img = Image.fromarray(filtered_frame)
        img.thumbnail((800, 600))  # Resize to fit window
        imgtk = ImageTk.PhotoImage(image=img)
        
        # Update the label
        self.preview_label.imgtk = imgtk
        self.preview_label.configure(image=imgtk)
        
        # Schedule next update
        if not self.is_image:
            self.root.after(10, self.update_preview)
    
    def on_close(self):
        """Handle window close event"""
        if self.cap is not None:
            self.cap.release()
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        self.update_preview()
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x800")  # Set initial window size
    app = PhotoFilterApp(root)
    try:
        app.run()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if hasattr(app, 'cap') and app.cap is not None and app.cap.isOpened():
            app.cap.release()
        cv2.destroyAllWindows()
