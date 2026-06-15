# 🎨 Image Segmentation via Max-Flow Min-Cut

**An interactive GUI-based tool for precise image segmentation using max-flow min-cut algorithms**


---

## 📋 Overview

The project is an implementation of two Min-Cut / Max flow algorithms (Edmonds-Karp, Boykov-Kolmogorov), applied to a graph generated from an image in order to perform a binary segmentation between foreground and background pixels, allowing for subject separation. To test the algorithms, a graphical user interface was created, allowing for foreground and background user strokes that guide the procedure.



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

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**
- `Pillow` - Image processing and manipulation

### Step 3: Run the Application

```bash
python main.py
```

The GUI window will open. 

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

### Running Segmentation

1. Select your preferred algorithm from the dropdown menu:
   - **Edmonds-Karp** 
   - **Boykov-Kolmogorov** 

2. Click the **Process** button to run segmentation

3. View the result in the right pane

### Navigation

- **Zoom In/Out** - Use mouse wheel or +/- buttons (range: 0.125x to 64x)
- **Undo** - Press **Ctrl+Z** to undo the last stroke

---

## 🧠 Algorithm Explanation

### Max-Flow Min-Cut Theorem

Finding the maximum flow in a network equals finding the minimum cut.

### Graph Construction

The image is represented as a graph where foreground pixels are connected to the source and background pixels to the sink. User strokes are used as hard constraints, while unmarked pixels get weights based on intensity distributions learned from the strokes. Neighboring pixels are also connected so that similar pixels are encouraged to stay in the same segment.

### Algorithms

**Edmonds-Karp Algorithm:**
- Uses BFS to find augmenting paths

**Boykov-Kolmogorov Algorithm:**
- Uses bidirectional tree growth from source and sink
- More efficient for binary cuts

---

## 📁 Project Structure

### Core Modules

**`main.py`** - GUI Application
- `ScrollableImagePane` - Reusable scrollable canvas with zoom/pan
- `PixelAnnotationApp` - Main application controller
- Features: Drawing, zooming, undo

**`graphs.py`** - Edmonds-Karp and Min-Cut
- `edmonds_karp(graph, source, sink)` - Implementation of Edmonds-Karp
- `min_cut(graph, flow, source)` - Computes minimum cut from flow
- Helper functions for residual graphs and path finding

**`boykov_kolmogorov.py`**
- Bidirectional tree search from source and sink
- Optimized for binary segmentation problems

**`image_loader.py`** - Image Processing
- `get_distributions(image, pixels)` - Computes  histograms from user strokes
- `image_to_graph(image, fg_pixels, bg_pixels)` - Constructs graph from image and annotations
- Handles probability estimation and edge weight calculation

**`constants.py`** - Configuration
- `DEBUG_MODE` - Enable/disable debug output

**`test_graphs.py`** - Unit Tests
- Tests for both algorithms
- Validates max-flow min-cut theorem
- Ensures correctness of implementations

### Test Images

The `test_images` directory contains sample images.

---






## 🔬 Algorithm Comparison

| Feature | Edmonds-Karp | Boykov-Kolmogorov |
|---------|--------------|-------------------|
| **Approach** | Global BFS | Local tree search |
| **Best For** | General graphs | Image segmentation |
| **Speed** | Moderate | Faster than EK for image segmentation |
| **Complexity** | O(V·E²) | O(V²·E·|c|) |

Note: |c| represent the cost of the minimum cut.
