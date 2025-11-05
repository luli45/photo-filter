# Research   
**Overview**  
You will create a **real-time photo filtering application** similar to Photoshop or Instagram filters using Windsurf or Cursor AI as your coding assistant. Your application should process webcam video or uploaded images and apply various computer vision filters we've studied.  
You will create a **real-time photo filtering application** similar to Photoshop or Instagram filters using Windsurf or Cursor AI as your coding assistant. Your application should process webcam video or uploaded images and apply various computer vision filters we've studied.  
**Tools**: Windsurf or Cursor IDE **Language**: Any (Python recommended, but JavaScript/TypeScript, Rust, C++, etc. are acceptable) **Time Estimate**: 2-3 hours  
**Tools**: Windsurf or Cursor IDE **Language**: Any (Python recommended, but JavaScript/TypeScript, Rust, C++, etc. are acceptable) **Time Estimate**: 2-3 hours  
  
**Learning Objectives**  
By completing this assignment, you will:  
* Apply convolution operations to real images  
* Implement multiple image filters (blur, sharpen, edge detection)  
* Build an interactive user interface  
* Work with real-time video processing  
* Practice using AI coding assistants effectively  
  
**Requirements**  
Your application must implement **ALL** of the following features:  
Your application must implement **ALL** of the following features:  
**Core Features (7 points)**  
## **1. Image/Video Input (1 point)**  
* Load images from file **OR** capture from webcam  
* Display the original input  
## **2. Box Blur Filter (1 point)**  
* Implement averaging/box blur with adjustable kernel size  
* Allow users to switch between 5×5 and 11×11 kernels (minimum)  
* Display the blurred result  
## **3. Gaussian Blur Filter (1 point)**  
* Implement Gaussian blur with adjustable parameters  
* Allow users to control kernel size and/or sigma value  
* Display the Gaussian blurred result  
## **4. Sharpening Filter (1 point)**  
* Implement image sharpening using a sharpening kernel  
* Apply to either original or blurred images  
* Display the sharpened result  
## **5. Edge Detection (2 points)**  
* Implement **Sobel edge detection** (horizontal and/or vertical)  
* Implement **Canny edge detection** with adjustable thresholds  
* Allow users to switch between edge detection methods  
* Display edge maps  
## **6. Interactive Controls (1 point)**  
* User can switch between different filters in real-time  
* **At minimum**: Keyboard controls (like 'P' for preview, 'C' for Canny, 'B' for blur, etc.)  
* **Better**: GUI controls (sliders, buttons, dropdown menus)  
  
**Advanced Features (2 points - Choose at least ONE)**  
## **Option A: Real-Time Webcam Processing**  
* Process live webcam feed at reasonable frame rate (15+ FPS)  
* Apply filters in real-time with minimal lag  
* Smooth switching between filters  
## **Option B: Side-by-Side Comparison**  
* Display multiple filtered versions simultaneously  
* Allow users to compare original, blurred, sharpened, and edge-detected versions  
* Clean layout with labels  
## **Option C: Custom/Creative Filter**  
* Implement an emboss filter  
* Create a "cartoon" effect (edge detection + color quantization)  
* Implement bilateral filtering (edge-preserving blur)  
* Any other creative filter combining techniques  
## **Option D: Parameter Tuning Interface**  
* Real-time sliders for kernel sizes  
* Real-time adjustment of Canny thresholds  
* Real-time sigma adjustment for Gaussian blur  
* Live preview of parameter changes  
## **Option E: Save/Export Functionality**  
* Save filtered images to disk  
* Allow users to name and organize saved images  
* Optional: batch processing of multiple images  
  
**Code Quality & Documentation (1 point)**  
* **Clean, readable code** with meaningful variable names  
* **Comments explaining** key sections (especially the math/filters)  
* **README file** with:  
    * How to run your application  
    * Which features you implemented  
    * Brief explanation of how you used Windsurf/Cursor  
    * Any challenges you faced and how you solved them  
