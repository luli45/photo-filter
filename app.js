document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const heroUploadBtn = document.getElementById('hero-upload-btn');
    const heroWebcamBtn = document.getElementById('hero-webcam-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const webcamBtn = document.getElementById('webcam-btn');
    const backToHeroBtn = document.getElementById('back-to-hero');
    const imageUpload = document.getElementById('image-upload');
    const originalCanvas = document.getElementById('original-canvas');
    const filteredCanvas = document.getElementById('filtered-canvas');
    const filterButtons = document.querySelectorAll('.filter-btn');
    const intensitySlider = document.getElementById('intensity');
    const intensityValue = document.getElementById('intensity-value');
    const downloadBtn = document.getElementById('download-btn');
    const statusElement = document.getElementById('status');
    const webcamModal = document.getElementById('webcam-modal');
    const closeModal = document.querySelector('.close');
    const captureBtn = document.getElementById('capture-btn');
    const cancelWebcam = document.getElementById('cancel-webcam');
    const webcamVideo = document.getElementById('webcam');
    
    const heroSection = document.getElementById('hero');
    const editorSection = document.getElementById('editor');

    // Canvas contexts
    const originalCtx = originalCanvas.getContext('2d', { willReadFrequently: true });
    const filteredCtx = filteredCanvas.getContext('2d', { willReadFrequently: true });

    // App state
    let currentFilter = 'none';
    let originalImage = null;
    let webcamStream = null;

    // Initialize the app
    function init() {
        setupEventListeners();
        updateStatus('Ready to upload an image');
    }

    // Set up event listeners
    function setupEventListeners() {
        // Button clicks
        heroUploadBtn.addEventListener('click', () => imageUpload.click());
        heroWebcamBtn.addEventListener('click', openWebcamModal);
        uploadBtn.addEventListener('click', () => imageUpload.click());
        webcamBtn.addEventListener('click', openWebcamModal);
        backToHeroBtn.addEventListener('click', showHeroSection);
        closeModal.addEventListener('click', closeWebcamModal);
        captureBtn.addEventListener('click', captureFromWebcam);
        cancelWebcam.addEventListener('click', closeWebcamModal);
        downloadBtn.addEventListener('click', downloadImage);

        // File upload
        imageUpload.addEventListener('change', handleImageUpload);

        // Filter buttons
        filterButtons.forEach(btn => {
            btn.addEventListener('click', () => setActiveFilter(btn.dataset.filter));
        });

        // Intensity slider
        intensitySlider.addEventListener('input', () => {
            intensityValue.textContent = intensitySlider.value;
            applyCurrentFilter();
        });
    }
    
    // Show hero section
    function showHeroSection() {
        heroSection.style.display = 'flex';
        editorSection.style.display = 'none';
    }
    
    // Show editor section
    function showEditorSection() {
        heroSection.style.display = 'none';
        editorSection.style.display = 'flex';
    }

    // Handle image upload
    function handleImageUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const img = new Image();
            img.onload = () => {
                originalImage = img;
                displayImage(img);
                showEditorSection();
                updateStatus('Image loaded successfully');
                downloadBtn.disabled = false;
            };
            img.src = event.target.result;
        };
        reader.readAsDataURL(file);
    }

    // Display image on canvas
    function displayImage(img) {
        // Set canvas dimensions to match image, but limit to a reasonable size
        const maxWidth = 800;
        const maxHeight = 600;
        let width = img.width;
        let height = img.height;

        if (width > maxWidth) {
            height = (maxWidth / width) * height;
            width = maxWidth;
        }
        if (height > maxHeight) {
            width = (maxHeight / img.height) * width;
            height = maxHeight;
        }

        // Set canvas dimensions
        originalCanvas.width = width;
        originalCanvas.height = height;
        filteredCanvas.width = width;
        filteredCanvas.height = height;

        // Draw original image on both canvases
        originalCtx.drawImage(img, 0, 0, width, height);
        filteredCtx.drawImage(img, 0, 0, width, height);

        // Apply the current filter
        applyCurrentFilter();
    }

    // Set active filter
    function setActiveFilter(filter) {
        currentFilter = filter;
        filterButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
        applyCurrentFilter();
    }

    // Apply the current filter to the image
    function applyCurrentFilter() {
        if (!originalImage) return;

        // Copy original image to filtered canvas
        filteredCtx.drawImage(originalImage, 0, 0, filteredCanvas.width, filteredCanvas.height);

        // Get image data
        const imageData = filteredCtx.getImageData(0, 0, filteredCanvas.width, filteredCanvas.height);
        const data = imageData.data;
        const intensity = parseInt(intensitySlider.value);

        // Apply selected filter
        switch (currentFilter) {
            case 'blur':
                applyBlur(data, intensity);
                break;
            case 'sharpen':
                applySharpen(data, intensity);
                break;
            case 'grayscale':
                applyGrayscale(data);
                break;
            case 'invert':
                applyInvert(data);
                break;
            case 'sepia':
                applySepia(data);
                break;
            case 'edge':
                applyEdgeDetection(data, intensity);
                break;
            // 'none' filter does nothing
        }

        // Put the modified data back to the canvas
        filteredCtx.putImageData(imageData, 0, 0);
    }

    // Filter functions
    function applyBlur(data, radius) {
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        tempCanvas.width = filteredCanvas.width;
        tempCanvas.height = filteredCanvas.height;
        
        // Apply multiple box blurs to approximate Gaussian blur
        const blurRadius = Math.min(radius, 20);
        for (let i = 0; i < 3; i++) {
            tempCtx.putImageData(new ImageData(data, filteredCanvas.width), 0, 0);
            filteredCtx.filter = `blur(${blurRadius}px)`;
            filteredCtx.drawImage(tempCanvas, 0, 0);
        }
    }

    function applySharpen(data, intensity) {
        const width = filteredCanvas.width;
        const height = filteredCanvas.height;
        const tempData = new Uint8ClampedArray(data);
        
        // Simple sharpen kernel
        const kernel = [
            0, -1, 0,
            -1, 5, -1,
            0, -1, 0
        ];
        
        // Apply convolution
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                for (let c = 0; c < 3; c++) {
                    let sum = 0;
                    for (let ky = -1; ky <= 1; ky++) {
                        for (let kx = -1; kx <= 1; kx++) {
                            const idx = ((y + ky) * width + (x + kx)) * 4 + c;
                            const kidx = (ky + 1) * 3 + (kx + 1);
                            sum += tempData[idx] * kernel[kidx];
                        }
                    }
                    const outIdx = (y * width + x) * 4 + c;
                    data[outIdx] = Math.max(0, Math.min(255, sum));
                }
            }
        }
    }

    function applyGrayscale(data) {
        for (let i = 0; i < data.length; i += 4) {
            const avg = (data[i] * 0.3 + data[i + 1] * 0.59 + data[i + 2] * 0.11);
            data[i] = data[i + 1] = data[i + 2] = avg;
        }
    }

    function applyInvert(data) {
        for (let i = 0; i < data.length; i += 4) {
            data[i] = 255 - data[i];         // R
            data[i + 1] = 255 - data[i + 1]; // G
            data[i + 2] = 255 - data[i + 2]; // B
        }
    }

    function applySepia(data) {
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            
            data[i] = Math.min(255, (r * 0.393) + (g * 0.769) + (b * 0.189));     // R
            data[i + 1] = Math.min(255, (r * 0.349) + (g * 0.686) + (b * 0.168)); // G
            data[i + 2] = Math.min(255, (r * 0.272) + (g * 0.534) + (b * 0.131)); // B
        }
    }

    function applyEdgeDetection(data, threshold) {
        // First convert to grayscale
        const width = filteredCanvas.width;
        const height = filteredCanvas.height;
        const grayData = new Uint8ClampedArray(width * height);
        
        // Convert to grayscale
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const idx = (y * width + x) * 4;
                grayData[y * width + x] = (
                    data[idx] * 0.3 +
                    data[idx + 1] * 0.59 +
                    data[idx + 2] * 0.11
                );
            }
        }
        
        // Apply Sobel operator
        const sobelX = [
            -1, 0, 1,
            -2, 0, 2,
            -1, 0, 1
        ];
        
        const sobelY = [
            -1, -2, -1,
             0,  0,  0,
             1,  2,  1
        ];
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                let gx = 0, gy = 0;
                
                // Convolution with Sobel kernels
                for (let ky = -1; ky <= 1; ky++) {
                    for (let kx = -1; kx <= 1; kx++) {
                        const idx = (y + ky) * width + (x + kx);
                        const kidx = (ky + 1) * 3 + (kx + 1);
                        gx += grayData[idx] * sobelX[kidx];
                        gy += grayData[idx] * sobelY[kidx];
                    }
                }
                
                // Calculate gradient magnitude
                const magnitude = Math.sqrt(gx * gx + gy * gy) * (threshold / 5);
                const outIdx = (y * width + x) * 4;
                const edgeValue = magnitude > threshold ? 255 : 0;
                
                // Set RGB to edge value, keep alpha
                data[outIdx] = edgeValue;     // R
                data[outIdx + 1] = edgeValue; // G
                data[outIdx + 2] = edgeValue; // B
            }
        }
    }

    // Webcam functions
    async function openWebcamModal() {
        try {
            webcamStream = await navigator.mediaDevices.getUserMedia({ video: true });
            webcamVideo.srcObject = webcamStream;
            webcamModal.style.display = 'flex';
            updateStatus('Webcam activated');
        } catch (err) {
            console.error('Error accessing webcam:', err);
            updateStatus('Could not access webcam: ' + err.message);
        }
    }

    function closeWebcamModal() {
        if (webcamStream) {
            webcamStream.getTracks().forEach(track => track.stop());
            webcamStream = null;
        }
        webcamModal.style.display = 'none';
    }

    function captureFromWebcam() {
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = webcamVideo.videoWidth;
        tempCanvas.height = webcamVideo.videoHeight;
        const tempCtx = tempCanvas.getContext('2d');
        
        // Draw video frame to canvas
        tempCtx.drawImage(webcamVideo, 0, 0, tempCanvas.width, tempCanvas.height);
        
        // Create image from canvas
        const img = new Image();
        img.onload = () => {
            originalImage = img;
            displayImage(img);
            showEditorSection();
            updateStatus('Image captured from webcam');
            downloadBtn.disabled = false;
        };
        img.src = tempCanvas.toDataURL('image/png');
        
        // Close the modal
        closeWebcamModal();
    }

    // Download the filtered image
    function downloadImage() {
        const link = document.createElement('a');
        link.download = `filtered-${new Date().getTime()}.png`;
        link.href = filteredCanvas.toDataURL('image/png');
        link.click();
        updateStatus('Image downloaded');
    }

    // Update status message
    function updateStatus(message) {
        statusElement.textContent = message;
        console.log(message);
    }

    // Initialize the app
    init();
});
