# Image Segmentation via Max-Flow Min-Cut



---

## Prerequisites

Before you begin, ensure you have the following installed on your system:
* **Python 3.10** or higher
* **pip** (Python package installer)

---

## Installation Steps
Follow these instructions to configure your environment and run the interactive image segmentation application on your local machine.

### 1. Download the Project Files
Clone this repository or download and extract the project files into a dedicated directory on your computer:

```bash
git clone https://github.com/KSteponavicus/Image-Segmentation-via-Min-Cut-Max-Flow
```

### 2. Verify Project Structure

Ensure that all required code modules are located in the same root folder:

```bash

├── main.py    
├── gui.py           
├── image_loader.py      
├── boykov_kolmogorov.py  
├── graphs.py             
└── requirements.txt      

```

### 3. Instalation Dependencies

```bash
pip install -r requirements.txt
```

### 4. Running the Application

```bash
python main.py
```

## Navigating the UI

### 1. Click Open Image in the interface to load your target file.

### 2. Draw the Foregroung and Background:

- Paint with green brushstrokes over the foreground object.

- Paint with red brushstrokes over the background regions.

### 3. Select your preferred algorithm (Edmonds-Karp or Boykov-Kolmogorov) from the dropdown menu.

### 4. Click Process to execute the segmentation process. The calculated mask will render on the right half of the UI.
