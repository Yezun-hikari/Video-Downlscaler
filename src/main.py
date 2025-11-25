import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QPushButton, QFileDialog, QLineEdit, QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import compressor

class WorkerThread(QThread):
    progress = Signal(int, str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, input_path, output_path, target_size):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.target_size = target_size

    def run(self):
        try:
            compressor.compress_video(
                self.input_path,
                self.output_path,
                self.target_size,
                lambda p, s: self.progress.emit(p, s)
            )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class DragDropWidget(QLabel):
    fileDropped = Signal(str)

    def __init__(self):
        super().__init__()
        self.setText("Drag & Drop Video Here\nor Click to Select")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                font-size: 16px;
                color: #555;
            }
            QLabel:hover {
                border-color: #555;
                background-color: #f0f0f0;
            }
        """)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.fileDropped.emit(files[0])

    def mousePressEvent(self, event):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.mov *.avi *.mkv)")
        if file_path:
            self.fileDropped.emit(file_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Compressor Tool")
        self.setMinimumSize(400, 350)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)

        # Drag & Drop Area
        self.drop_area = DragDropWidget()
        self.drop_area.fileDropped.connect(self.on_file_selected)
        layout.addWidget(self.drop_area)

        # File Info Label
        self.file_label = QLabel("No file selected")
        layout.addWidget(self.file_label)

        # Target Size Input
        size_layout = QVBoxLayout()
        size_label = QLabel("Target Size (MB):")
        self.size_input = QLineEdit()
        self.size_input.setPlaceholderText("e.g. 50")
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_input)
        layout.addLayout(size_layout)

        # Output Filename Input
        name_layout = QVBoxLayout()
        name_label = QLabel("Output Filename:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter output filename (optional)")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Start Button
        self.start_btn = QPushButton("Start Compression")
        self.start_btn.clicked.connect(self.start_compression)
        self.start_btn.setEnabled(False)
        layout.addWidget(self.start_btn)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.selected_file = None

    def on_file_selected(self, file_path):
        self.selected_file = file_path
        self.file_label.setText(f"Selected: {os.path.basename(file_path)}")
        self.start_btn.setEnabled(True)

        # Suggest a filename
        base_name = os.path.basename(file_path)
        name, ext = os.path.splitext(base_name)
        self.name_input.setText(f"{name}_compressed{ext}")

        self.drop_area.setText("File Selected")
        self.drop_area.setStyleSheet("border: 2px solid #4CAF50; border-radius: 10px; padding: 20px; color: #4CAF50;")

    def start_compression(self):
        if not self.selected_file:
            return

        try:
            target_size = float(self.size_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for target size.")
            return

        # Determine output path (Exe directory)
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            application_path = os.path.dirname(sys.executable)
        else:
            # Running as script
            application_path = os.path.dirname(os.path.abspath(__file__))
            # Adjust if we are in src/
            # Actually for dev, usually we want it in the current working dir or script dir.
            # Let's stick to script dir for now or CWD.
            # But user said "path of the Exe".

        output_filename = self.name_input.text().strip()
        if not output_filename:
             base, ext = os.path.splitext(os.path.basename(self.selected_file))
             output_filename = f"{base}_compressed{ext}"

        output_path = os.path.join(application_path, output_filename)

        self.start_btn.setEnabled(False)
        self.drop_area.setEnabled(False)
        self.status_label.setText("Starting...")

        self.worker = WorkerThread(self.selected_file, output_path, target_size)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def update_progress(self, percent, message):
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)

    def on_finished(self):
        self.status_label.setText("Compression Complete!")
        self.progress_bar.setValue(100)
        self.start_btn.setEnabled(True)
        self.drop_area.setEnabled(True)
        QMessageBox.information(self, "Success", "Video compressed successfully!")

    def on_error(self, message):
        self.status_label.setText("Error occurred.")
        self.start_btn.setEnabled(True)
        self.drop_area.setEnabled(True)
        QMessageBox.critical(self, "Error", message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
