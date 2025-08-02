# Panel Viewer

Panel Viewer is a Python-based desktop application for viewing comic book archives (`.cbz` / `.zip`) with support for panel detection, full-page view, and fit-width scrolling. It uses **PyQt6** for the GUI and **OpenCV** for image processing.

---

## Features

- 📂 Open CBZ/ZIP comic book files
- 🧠 Automatic panel detection and navigation
- 🖼️ Full-page and fit-width viewing modes
- 🔍 Zoom in/out on panels
- 🖱️ Scroll through pages using mouse wheel
- 📝 Display filename, page number, panel number, and zoom level

---

## Installation

### Manual Setup
git clone https://github.com/blippu/panel_viewer.git
cd panel_viewer
pip install -r requirements.txt
python main.py

### With VSCode
1. Open the project folder in **Visual Studio Code**.
2. Press `Ctrl + Shift + P` to open the **Command Palette**.
3. Type and select `Python: Create Environment`.
4. Choose `Venv` as the environment type.
5. Select your Python interpreter (e.g., `python.exe`).
6. VSCode will automatically create a virtual environment and install dependencies from `requirements.txt` if available.

---