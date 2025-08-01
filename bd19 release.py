import sys
import os
import zipfile
import cv2
import numpy as np
import pygame
from PyQt6.QtGui import (QGuiApplication, QAction)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow,QFileDialog,QLabel,QHBoxLayout,QVBoxLayout,    QWidget, QPushButton )
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
import shutil

class ComicViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Comic Viewer")
        pygame.init()

        self.scroll_position = 0
        self.version= "v 0.19"
        self.filename = ""
        self.page_number = 0
        self.panel_number = ""
        self.panel_surfaces = []
        self.panel_info = []
        self.setStyleSheet("background-color: black;")
        self.screen_width = 800
        self.screen_height = 600
        self.menu_height = 50
        self.zoom_factor = 1.0
        self.label = QLabel("No file opened.")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_files = []
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        # Make buttons visible in grey with white text
        self.prev_button.setStyleSheet("background-color: grey; color: white;")
        self.next_button.setStyleSheet("background-color: grey; color: white;")
        self.prev_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.next_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.prev_button.clicked.connect(self.show_previous_panel)
        self.next_button.clicked.connect(self.show_next_panel)

        image_layout = QVBoxLayout()
        image_layout.addWidget(self.label)

        nav_layout = QHBoxLayout()
        ## hiding the navigation buttons
        #nav_layout.addWidget(self.prev_button)
        #nav_layout.addWidget(self.next_button)
        # Optional: ensure buttons are visible
        #self.prev_button.setMinimumHeight(0)
        #self.next_button.setMinimumHeight(0)


        main_layout = QVBoxLayout()
        main_layout.addLayout(image_layout)
        main_layout.addLayout(nav_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        self.menuBar().setStyleSheet("background-color: gray;")
        self.create_menus()
        self.update_title()

    def create_menus(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        open_action = QAction("Open File", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        display_menu = menubar.addMenu("Display")

        self.display_filename_action = QAction("Display Filename", self, checkable=True, checked=True)
        self.display_page_action = QAction("Display Page Number", self, checkable=True, checked=True)
        self.display_panel_action = QAction("Display Panel Number", self, checkable=True, checked=True)

        self.display_filename_action.triggered.connect(self.update_title)
        self.display_page_action.triggered.connect(self.update_title)
        self.display_panel_action.triggered.connect(self.update_title)

        display_menu.addAction(self.display_filename_action)
        display_menu.addAction(self.display_page_action)
        display_menu.addAction(self.display_panel_action)
        
        reading_menu = menubar.addMenu("Reading Mode")

        # Existing actions
        self.reading_menu_panel_action = QAction("Panel View", self, checkable=True)
        self.reading_menu_page_action = QAction("Full Page View", self, checkable=True)
        self.reading_menu_fit_width_action = QAction("Fit Width", self, checkable=True)

        # Set default state
        #self.reading_menu_panel_action.setChecked(True)
        self.reading_menu_page_action.setChecked(True)

        # Define toggle behavior
        def toggle_to_panel():
            self.reading_menu_panel_action.setChecked(True)
            self.reading_menu_page_action.setChecked(False)
            self.reading_menu_fit_width_action.setChecked(False)
            self.update_title()

        def toggle_to_page():
            self.reading_menu_panel_action.setChecked(False)
            self.reading_menu_page_action.setChecked(True)
            self.reading_menu_fit_width_action.setChecked(False)
            self.update_title()

        def toggle_to_fit_width():
            self.reading_menu_panel_action.setChecked(False)
            self.reading_menu_page_action.setChecked(False)
            self.reading_menu_fit_width_action.setChecked(True)
            self.update_title()

        # Connect actions
        self.reading_menu_panel_action.triggered.connect(toggle_to_panel)
        self.reading_menu_page_action.triggered.connect(toggle_to_page)
        self.reading_menu_fit_width_action.triggered.connect(toggle_to_fit_width)

        # Add to menu
        reading_menu.addAction(self.reading_menu_panel_action)
        reading_menu.addAction(self.reading_menu_page_action)
        reading_menu.addAction(self.reading_menu_fit_width_action)

        
        # Add version label to the right side of the menu bar
        version_label = QLabel(self.version)
        version_label.setStyleSheet("color: white; margin-left: auto; padding: 5px;")
        menubar.setCornerWidget(version_label, Qt.Corner.TopRightCorner)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Comic Book", filter="CBZ files (*.cbz);;ZIP files (*.zip)")
        if file_path:
            self.filename = os.path.basename(file_path)

            self.page_number = 1
            self.panel_number = 1

            # Show loading message
            self.label.setText("Loading comic book...")
            self.label.setStyleSheet("color: grey; background-color: black;")
            self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            QApplication.processEvents()  # Force UI to update immediately


            self.panel_surfaces, self.panel_info = self.extract_and_process_panels(file_path)
            self.display_panel()


            self.update_title()

    def extract_and_process_panels(self, zip_path):
        extract_dir = 'extracted_images'

        # Clear the extraction directory if it exists
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)

        # Extract all contents of the ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Recursively collect image files from all subdirectories
        self.image_files = []
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    self.image_files.append(os.path.join(root, file))


        panel_surfaces = []
        panel_info = []
        for page_index, image_path in enumerate(sorted(self.image_files)):
            image = cv2.imread(image_path)
            if image is None:
                continue
            image_resized, panel_boxes_sorted = self.detect_panels(image)
            for panel_index, (x, y, w, h) in enumerate(panel_boxes_sorted):
                panel = image_resized[y:y+h, x:x+w]
                scale_factor = min(self.screen_width / w, (self.screen_height - self.menu_height) / h, 1.0)
                panel_resized = cv2.resize(panel, (int(w * scale_factor), int(h * scale_factor)))
                panel_rgb = cv2.cvtColor(panel_resized, cv2.COLOR_BGR2RGB)
                panel_surface = pygame.surfarray.make_surface(np.transpose(panel_rgb, (1, 0, 2)))
                panel_surfaces.append(panel_surface)
                panel_info.append((os.path.basename(zip_path), page_index + 1, panel_index + 1))
        return panel_surfaces, panel_info

    def detect_panels(self, image):
        height, width = image.shape[:2]
        max_dim = 4000
        scale = max_dim / max(height, width)
        image_resized = cv2.resize(image, (int(width * scale), int(height * scale)))

        gray = cv2.cvtColor(image_resized, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        inverted = cv2.bitwise_not(morphed)
        contours, _ = cv2.findContours(inverted, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        panel_boxes = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w * h > 10000:
                panel_boxes.append((x, y, w, h))

        def sort_panels(boxes, row_tolerance=30):
            boxes = sorted(boxes, key=lambda b: b[1])
            rows, current_row = [], []
            for box in boxes:
                if not current_row or abs(box[1] - current_row[0][1]) < row_tolerance:
                    current_row.append(box)
                else:
                    rows.append(sorted(current_row, key=lambda b: b[0]))
                    current_row = [box]
            if current_row:
                rows.append(sorted(current_row, key=lambda b: b[0]))
            return [box for row in rows for box in row]

        return image_resized, sort_panels(panel_boxes)

    def display_panel(self):
        if (self.reading_menu_page_action.isChecked() or self.reading_menu_fit_width_action.isChecked()):
            # Full Page View
            extract_dir = 'extracted_images'
        # Recursively collect image files from all subdirectories
            #image_files = []
            #for root, dirs, files in os.walk(extract_dir):
            #    for file in files:
            #        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            #            self.image_files.append(os.path.join(root, file))

            if not self.image_files:
                self.label.setText("No JPG images found.")
                return

            #first_image_path = sorted(self.image_files)[0]
            
            # Use current page number instead of always showing the first image
            current_index = max(0, self.page_number - 1)
            first_image_path = sorted(self.image_files)[current_index]

            print(first_image_path)
            image = cv2.imread(first_image_path)
            if image is None:
                self.label.setText("Failed to load image.")
                return

            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            height, width, channel = image_rgb.shape
            bytes_per_line = 3 * width
            q_image = QImage(image_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB32)
            pixmap = QPixmap.fromImage(q_image)


            # Conditionally scale to fit screen width
            if self.reading_menu_fit_width_action.isChecked():
                screen_width = self.size().width()  # or use self.size().width() for full window
                pixmap = pixmap.scaledToWidth(screen_width, Qt.TransformationMode.SmoothTransformation)
                #pixmap = pixmap.scaledToHeight(self.size().height() - self.menu_height, Qt.TransformationMode.SmoothTransformation)
                print('Scaling to fit width:', screen_width)


            label_size = self.label.size()
            scaled_pixmap = pixmap.scaled(label_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.label.setPixmap(scaled_pixmap)
        else:
            # Panel View
            if not self.panel_surfaces:
                self.label.setText("No panels to display.")
                return

            index = 0
            for i, info in enumerate(self.panel_info):
                if info[1] == self.page_number and info[2] == self.panel_number:
                    index = i
                    break

            surface = self.panel_surfaces[index]
            width, height = surface.get_size()
            image = QImage(surface.get_buffer(), width, height, QImage.Format.Format_RGB32)
            pixmap = QPixmap.fromImage(image)

            if hasattr(self, 'zoom_factor') and self.zoom_factor != 1.0:
                new_width = int(width * self.zoom_factor)
                new_height = int(height * self.zoom_factor)
                pixmap = pixmap.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

            self.label.setPixmap(pixmap)

        self.update_title()

    def show_next_panel(self):
        if self.reading_menu_page_action.isChecked():
            # Full page mode: no next page implemented
            return
        for i, info in enumerate(self.panel_info):
            if info[1] == self.page_number and info[2] == self.panel_number:
                if i + 1 < len(self.panel_info):
                    self.page_number, self.panel_number = self.panel_info[i + 1][1], self.panel_info[i + 1][2]
                    self.display_panel()
                break

    def show_previous_panel(self):
        if self.reading_menu_page_action.isChecked():
            # Full page mode: no previous page implemented
            return
        for i, info in enumerate(self.panel_info):
            if info[1] == self.page_number and info[2] == self.panel_number:
                if i - 1 >= 0:
                    self.page_number, self.panel_number = self.panel_info[i - 1][1], self.panel_info[i - 1][2]
                    self.display_panel()
                break

    def update_title(self):
        parts = []
        if self.display_filename_action.isChecked() and self.filename:
            parts.append(self.filename)
        if self.display_page_action.isChecked():
            parts.append(f"Page {self.page_number} / {len(self.image_files)}")
        if self.reading_menu_page_action.isChecked():
            parts.append(f"Full Page View")
        else:
            if self.display_panel_action.isChecked() and not self.reading_menu_fit_width_action.isChecked():
                parts.append(f"Panel {self.panel_number}")
                parts.append(f"Zoom {self.zoom_factor:.1f}")
        self.setWindowTitle(" - ".join(parts) if parts else "Comic Viewer")

    def keyPressEvent(self, event):
        try:
            key = event.key()
            text = event.text()
            if self.reading_menu_page_action.isChecked() or self.reading_menu_fit_width_action.isChecked():
                return  # Ignore key events in Full Page View
            if key == Qt.Key.Key_Right:
                self.show_next_panel()
            elif key == Qt.Key.Key_Left:
                self.show_previous_panel()
            elif (text == '+' or key == Qt.Key.Key_Plus) and not self.reading_menu_page_action.isChecked():
                self.zoom_factor = min(2.5, self.zoom_factor + 0.1)
                self.display_panel()
            elif (text == '-' or key == Qt.Key.Key_Minus) and not self.reading_menu_page_action.isChecked():
                self.zoom_factor = max(0.5, self.zoom_factor - 0.1)
                self.display_panel()
            else:
                super().keyPressEvent(event)
        except Exception as e:
            print(f"Error in keyPressEvent: {e}")

    def wheelEvent(self, event):
        if (self.reading_menu_page_action.isChecked() or self.reading_menu_fit_width_action.isChecked()):
            # Full Page View navigation
            #extract_dir = 'extracted_images'
            #self.image_files = sorted([f for f in os.listdir(extract_dir) if f.lower().endswith('.jpg')])
            

            extract_dir = 'extracted_images'
            self.image_files = sorted([
                os.path.join(root, file)
                for root, _, files in os.walk(extract_dir)
                for file in files
                if file.lower().endswith('.jpg')
            ])

            if not self.image_files or not self.image_files[self.page_number - 1]:
                return

            image_path = self.image_files[self.page_number - 1]
            image = cv2.imread(image_path)
            if image is None:
                return

            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            height, width, _ = image_rgb.shape
            bytes_per_line = 3 * width
            q_image = QImage(image_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)

            if self.reading_menu_fit_width_action.isChecked():
                label_width = self.label.width()
                scaled_pixmap = pixmap.scaledToWidth(label_width, Qt.TransformationMode.SmoothTransformation)
                scaled_height = scaled_pixmap.height()
                visible_height = self.label.height()
                scroll_step = 100
                max_scroll = max(0, scaled_height - visible_height)

                if event.angleDelta().y() > 0:
                    if self.scroll_position > 0:
                        self.scroll_position = max(0, self.scroll_position - scroll_step)
                    else:
                        # Only switch page if already at top
                        if self.page_number > 1:
                            self.page_number -= 1
                            # Load new image and scroll to bottom
                            image_path = self.image_files[self.page_number - 1]
                            image = cv2.imread(image_path)
                            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                            height, width, _ = image_rgb.shape
                            q_image = QImage(image_rgb.data, width, height, 3 * width, QImage.Format.Format_RGB888)
                            pixmap = QPixmap.fromImage(q_image)
                            scaled_pixmap = pixmap.scaledToWidth(self.label.width(), Qt.TransformationMode.SmoothTransformation)
                            self.scroll_position = max(0, scaled_pixmap.height() - self.label.height())

                else:
                    if self.scroll_position < max_scroll:
                        self.scroll_position = min(max_scroll, self.scroll_position + scroll_step)
                    elif self.scroll_position >= max_scroll and self.page_number < len(self.image_files):
                        self.page_number += 1
                        self.scroll_position = 0


                # Crop the image to simulate vertical scroll
                cropped_pixmap = scaled_pixmap.copy(0, self.scroll_position, scaled_pixmap.width(), visible_height)
                self.label.setPixmap(cropped_pixmap)

            else:
                self.scroll_position = 0
                if event.angleDelta().y() > 0 and self.page_number > 1:
                    self.page_number -= 1
                elif event.angleDelta().y() < 0 and self.page_number < len(self.image_files):
                    self.page_number += 1

                label_size = self.label.size()
                scaled_pixmap = pixmap.scaled(label_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.label.setPixmap(scaled_pixmap)

            self.update_title()

        else:
            # Panel View navigation
            if event.angleDelta().y() > 0:
                self.show_previous_panel()
            else:
                self.show_next_panel()

    def closeEvent(self, event):
        extract_dir = 'extracted_images'
        if os.path.exists(extract_dir):
            try:
                shutil.rmtree(extract_dir)
                print(f"Temporary directory '{extract_dir}' deleted.")
            except Exception as e:
                print(f"Error deleting temporary directory: {e}")
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ComicViewer()
    # Set the initial size of the viewer to 80% of the screen size
    screen = QGuiApplication.primaryScreen().availableGeometry()
    width = int(screen.width() * 0.8)
    height = int(screen.height() * 0.8)
    viewer = ComicViewer()
    viewer.resize(width, height)

    viewer.show()
    sys.exit(app.exec())
