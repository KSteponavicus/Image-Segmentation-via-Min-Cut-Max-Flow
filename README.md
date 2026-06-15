# 🎨 Image Segmentation via Max-Flow Min-Cut

**An interactive GUI-based tool for precise image segmentation using advanced max-flow min-cut algorithms**

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

</div>

---

## 📋 Overview

This project implements an **interactive image segmentation system** using max-flow min-cut algorithms. It provides a user-friendly GUI where you can mark foreground and background regions, then applies sophisticated graph-cut algorithms to automatically segment the image based on color distribution and spatial coherence.

The application supports two state-of-the-art algorithms:
- **Edmonds-Karp** - Classic BFS-based maximum flow algorithm
- **Boykov-Kolmogorov** - Optimized binary minimum cut algorithm

---

## ✨ Key Features

- 🖌️ **Interactive Annotation** - Draw green strokes for foreground, red strokes for background
- 🔄 **Dual Algorithm Support** - Switch between Edmonds-Karp and Boykov-Kolmogorov algorithms
- 🔍 **Advanced Zoom & Pan** - Smooth zooming (0.125x to 64x) and right-click drag panning
- ↩️ **Undo Support** - Ctrl+Z to undo the last annotation stroke
- 🎨 **Real-Time Preview** - Instant segmentation results on the right panel
- 📊 **Split Pane Interface** - Side-by-side comparison of original and segmented images
- ⚙️ **Smart Probability Estimation** - Uses color histograms from annotations for intelligent segmentation
- 🎯 **Flexible Brush Control** - Adjustable brush size for precise or quick annotations

---

## 🔧 Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.10** or higher
- **pip** (Python package installer)

---

## 📦 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/KSteponavicus/Image-Segmentation-via-Min-Cut-Max-Flow
cd Image-Segmentation-via-Min-Cut-Max-Flow
```

### Step 2: Verify Project Structure

Ensure all required files are in the root directory:

```
├── main.py                      # GUI application entry point
├── boykov_kolmogorov.py         # Boykov-Kolmogorov algorithm
├── graphs.py                    # Edmonds-Karp and min-cut algorithms
├── image_loader.py              # Image processing & graph construction
├── constants.py                 # Configuration constants
├── test_graphs.py               # Unit tests
├── requirements.txt             # Python dependencies
├── test_images/                 # Sample test images
└── README.md                    # This file
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**
- `Pillow` - Image processing and manipulation

### Step 4: Run the Application

```bash
python main.py
```

The GUI window will open. You're ready to segment images!

---

## 🎮 How to Use

### Loading an Image

1. Click **File → Load Image** or use the "Load Image" button in the toolbar
2. Select an image from your computer (supports PNG, JPG, GIF, etc.)

### Annotating Foreground & Background

1. **Green Brush** - Click the green button in the toolbar to select it
   - Paint over objects you want to extract (foreground)
   
2. **Red Brush** - Click the red button to select it
   - Paint over background regions

3. **Eraser** - Click the eraser button to remove annotations

**Tips for Best Results:**
- Paint multiple strokes across different regions
- Include variety in color samples for better probability estimation
- You need at least a few pixels marked for each region

### Running Segmentation

1. Select your preferred algorithm from the dropdown menu:
   - **Edmonds-Karp** - Standard BFS-based flow algorithm, reliable
   - **Boykov-Kolmogorov** - Optimized for binary cuts, generally faster

2. Click the **Process** button to run segmentation

3. View the result in the right pane

### Navigation

- **Zoom In/Out** - Use mouse wheel or +/- buttons (range: 0.125x to 64x)
- **Pan** - Right-click and drag to move around large images
- **Undo** - Press **Ctrl+Z** to undo the last stroke

---

## 🧠 Algorithm Explanation

### Max-Flow Min-Cut Theorem

The core principle: Finding the maximum flow in a network equals finding the minimum cut.

### Graph Construction

For each image, a graph is constructed where:
- **Nodes** = Pixels + source (S) + sink (T)
- **Edges** = Connections between neighboring pixels + connections to S/T
- **Edge Weights**:
  - **Source edges**: Based on background probability (data cost)
  - **Sink edges**: Based on foreground probability (data cost)
  - **Between pixels**: Based on color similarity (smoothness cost)

### Energy Minimization

The algorithm finds the cut that minimizes:
```
E = Σ(data_cost) + λ·Σ(smoothness_cost)
```

Where:
- `data_cost` = -log(probability) based on color distribution of annotated regions
- `smoothness_cost` = Gaussian kernel based on color difference
- `λ = 100` = Balance parameter (adjustable in `image_loader.py`)

### Algorithms

**Edmonds-Karp Algorithm:**
- Uses BFS to find augmenting paths
- Time complexity: O(V·E²)
- Guaranteed to find maximum flow
- Good for general graphs

**Boykov-Kolmogorov Algorithm:**
- Uses bidirectional tree growth from source and sink
- More efficient for binary cuts
- Time complexity: ~O(V²·E) for most images
- Specifically optimized for computer vision problems

---

## 📁 Project Structure

### Core Modules

**`main.py`** - GUI Application
- `ScrollableImagePane` - Reusable scrollable canvas with zoom/pan
- `PixelAnnotationApp` - Main application controller
- Features: Drawing, zooming, undo, real-time preview

**`graphs.py`** - Flow Algorithms
- `edmonds_karp(graph, source, sink)` - Standard max-flow algorithm
- `min_cut(graph, flow, source)` - Computes minimum cut from flow
- Helper functions for residual graphs and path finding

**`boykov_kolmogorov.py`** - Optimized Binary Cut Algorithm
- Bidirectional tree search from source and sink
- Orphan node recovery for efficiency
- Optimized for binary segmentation problems

**`image_loader.py`** - Image Processing
- `get_distributions(image, pixels)` - Computes color histograms
- `image_to_graph(image, fg_pixels, bg_pixels)` - Constructs graph from image and annotations
- Handles probability estimation and edge weight calculation

**`constants.py`** - Configuration
- `DEBUG_MODE` - Enable/disable debug output

**`test_graphs.py`** - Unit Tests
- Tests for both algorithms
- Validates max-flow min-cut theorem
- Ensures correctness of implementations

### Test Images

The `test_images/` directory contains sample images:
- `dog.jpg` - Animal segmentation test
- `face.png` - Face extraction test
- `wine.jpg` - Object segmentation test
- `small_test.jpg` - Quick test image
- `test_image_smile.png` - Simple test image
- Various other formats for compatibility testing

---

## 🧪 Testing

Run the included unit tests to verify algorithm correctness:

```bash
python -m pytest test_graphs.py -v
```

Or run directly:

```bash
python test_graphs.py
```

**Test Coverage:**
- ✅ Edmonds-Karp max-flow correctness
- ✅ Boykov-Kolmogorov max-flow correctness
- ✅ Min-cut computation
- ✅ Max-flow min-cut theorem verification

---

## ⚙️ Configuration

### Adjustable Parameters

**`image_loader.py`:**
```python
LAMBDA = 100  # Weight of smoothness term vs data term
               # Higher = smoother segments, more sensitive to boundaries
               # Lower = follows annotations more closely
```

**`constants.py`:**
```python
DEBUG_MODE = False  # Set to True for detailed algorithm logging
```

**`main.py` - Zoom levels:**
```python
self.zoom_levels = [0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64]
```

---

## 🚀 Performance Tips

1. **For Large Images**: Use a smaller zoom level (e.g., 0.5x) when annotating
2. **For Complex Scenes**: Use Boykov-Kolmogorov for faster results
3. **For Accuracy**: Use Edmonds-Karp for more guaranteed optimality
4. **Memory**: The app limits display to 80 million pixels to prevent memory issues

---

## 📚 Technical Details

### Graph Construction Example

For a 2×2 pixel image with color values [100, 150, 120, 130]:

```
Pixel Layout:
(0,0)=100  (1,0)=150
(0,1)=120  (1,1)=130

Graph Structure:
    S (source)
    / | \ \
(0,0) (1,0) (0,1) (1,1)
    \ | / /
    T (sink)
    
Plus horizontal & vertical neighbor edges
```

### Color Probability Distribution

When you paint pixels:
1. Color histogram is built from annotated pixels
2. Smoothing: ε = 0.001 to avoid log(0)
3. Normalized to probability distribution
4. Used to compute -log(probability) as edge weights

---

## 🐛 Troubleshooting

**Issue: GUI doesn't open**
- Ensure Python 3.10+ is installed
- Check: `python --version`
- Reinstall Pillow: `pip install --upgrade Pillow`

**Issue: Image won't load**
- Verify the image path is correct
- Supported formats: PNG, JPG, GIF, BMP, etc.
- Try a different image format

**Issue: Segmentation looks wrong**
- Add more annotation strokes (both foreground and background)
- Ensure annotations cover color variety
- Try adjusting LAMBDA in `image_loader.py`
- Try the other algorithm for comparison

**Issue: Out of memory**
- Work with smaller images
- Reduce zoom level before annotating
- Close other applications

---

## 🔬 Algorithm Comparison

| Feature | Edmonds-Karp | Boykov-Kolmogorov |
|---------|--------------|-------------------|
| **Approach** | Global BFS | Local tree search |
| **Best For** | General graphs | Binary cuts |
| **Speed** | Moderate | Generally Faster |
| **Memory** | Moderate | Lower |
| **Complexity** | O(V·E²) | ~O(V²·E) |
| **Reliability** | Very High | Very High |

---

## 📖 References

- **Boykov & Kolmogorov (2004)** - "An Experimental Comparison of Min-Cut/Max-Flow Algorithms for Energy Minimization in Vision"
- **Edmonds & Karp (1972)** - "Theoretical Improvements in Algorithmic Efficiency for Network Flow Problems"
- **Max-Flow Min-Cut Theorem** - Fundamental result in network flow theory

---

## 📝 License

This project is provided as-is for educational and research purposes.

---

## 👨‍💻 Development

### Setting Up Development Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python test_graphs.py
```

### Code Structure Best Practices

- Each module has a single responsibility
- Algorithms in `graphs.py` and `boykov_kolmogorov.py` are algorithm-agnostic
- Graph representation: Dictionary of edge → capacity
- Flow representation: Dictionary of edge → flow

---

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:

- [ ] Multi-way cut support
- [ ] GPU acceleration
- [ ] Additional algorithms (push-relabel, etc.)
- [ ] Image format export options
- [ ] Batch processing mode
- [ ] Dark theme UI
- [ ] Performance optimizations

---

## ❓ FAQ

**Q: What image formats are supported?**  
A: All formats supported by Pillow: PNG, JPG, GIF, BMP, TIFF, etc.

**Q: Can I use this for video?**  
A: Currently no, but frames could be processed individually.

**Q: How accurate is the segmentation?**  
A: Accuracy depends on annotation quality and image complexity. Simple images with clear boundaries often achieve >95% accuracy.

**Q: Can I batch process images?**  
A: Not yet - consider creating a script that iterates through `image_loader.py` functions.

**Q: What's the maximum image size?**  
A: Theoretically unlimited, but display is limited to 80M pixels and memory to available RAM.

---

**Made with ❤️ for computer vision enthusiasts**
