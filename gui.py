import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QMessageBox, QGroupBox, QDoubleSpinBox, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

from step_processor import STEPProcessor

class STEPFaceColorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processor = STEPProcessor()
        self.current_file = None
        self.face_colors = {}
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('STEP File Face Coloring')
        self.setGeometry(100, 100, 500, 300)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # File selection
        file_group = QGroupBox("File Selection")
        file_layout = QVBoxLayout()
        
        self.file_label = QLabel("No file selected")
        file_layout.addWidget(self.file_label)
        
        file_btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load STEP File")
        self.load_btn.clicked.connect(self.load_file)
        file_btn_layout.addWidget(self.load_btn)
        
        self.process_btn = QPushButton("Process and Save")
        self.process_btn.clicked.connect(self.process_and_save)
        self.process_btn.setEnabled(False)
        file_btn_layout.addWidget(self.process_btn)
        
        file_layout.addLayout(file_btn_layout)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Orientation options
        orient_group = QGroupBox("Orientation Options")
        orient_layout = QVBoxLayout()
        
        orient_criteria_layout = QHBoxLayout()
        orient_criteria_layout.addWidget(QLabel("Orientation Criteria:"))
        self.orient_combo = QComboBox()
        self.orient_combo.addItems(["Largest Face Down", "Z-Axis Up"])
        orient_criteria_layout.addWidget(self.orient_combo)
        orient_layout.addLayout(orient_criteria_layout)
        
        orient_group.setLayout(orient_layout)
        layout.addWidget(orient_group)
        
        # Coloring options
        color_group = QGroupBox("Coloring Options")
        color_layout = QVBoxLayout()
        
        angle_layout = QHBoxLayout()
        angle_layout.addWidget(QLabel("Angle Tolerance (degrees):"))
        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(1, 45)
        self.angle_spin.setValue(15)
        self.angle_spin.setSingleStep(1)
        angle_layout.addWidget(self.angle_spin)
        color_layout.addLayout(angle_layout)
        
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)
        
        # Status bar
        self.statusBar().showMessage('Ready')
    
    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open STEP File", "", "STEP Files (*.stp *.step)")
        
        if file_path:
            self.current_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            
            success, message = self.processor.load_step_file(file_path)
            if success:
                self.statusBar().showMessage(f"Loaded: {os.path.basename(file_path)}")
                self.process_btn.setEnabled(True)
            else:
                QMessageBox.critical(self, "Error", message)
                self.statusBar().showMessage("Load failed")
    
    def process_and_save(self):
        if not self.current_file:
            return
            
        # Get orientation criteria
        criteria_index = self.orient_combo.currentIndex()
        criteria = "largest_face_down" if criteria_index == 0 else "z_axis_up"
        
        # Orient the shape
        self.processor.orient_shape(criteria)
        
        # Color faces
        angle_tolerance = self.angle_spin.value()
        self.face_colors = self.processor.color_faces_by_orientation(angle_tolerance)
        
        # Generate output path
        base, ext = os.path.splitext(self.current_file)
        output_path = f"{base}_colored{ext}"
        
        # Save the file
        success = self.processor.save_colored_step(self.current_file, output_path, self.face_colors)
        
        if success:
            QMessageBox.information(self, "Success", f"File saved as: {output_path}")
            self.statusBar().showMessage(f"Saved: {os.path.basename(output_path)}")
        else:
            QMessageBox.critical(self, "Error", "Failed to save file")
            self.statusBar().showMessage("Save failed")

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = STEPFaceColorGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
