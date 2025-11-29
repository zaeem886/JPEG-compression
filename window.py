from PySide6.QtWidgets import QWidget, QFileDialog, QMessageBox
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from window_ui import Ui_MainWindowUI
from jpeg_algo import jpeg_compress, jpeg_decompress, calculate_compression_stats
import numpy as np
from PIL import Image
import os

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Setup the user interface
        self.ui = Ui_MainWindowUI()
        self.ui.setupUi(self)

        # Variables to store our images
        self.original_image = None  # Original loaded image
        self.compressed_data = None  # Compressed image data
        self.decompressed_image = None  # Decompressed result
        self.image_path = None  # Path to loaded image file

        # Connect buttons to their functions
        self.ui.btn_load.clicked.connect(self.load_image)
        self.ui.btn_compress.clicked.connect(self.compress_image)
        self.ui.btn_download_compressed.clicked.connect(self.save_compressed)
        self.ui.btn_download_decompressed.clicked.connect(self.save_decompressed)

        # Disable buttons at startup
        self.ui.btn_compress.setEnabled(False)
        self.ui.btn_download_compressed.setEnabled(False)
        self.ui.btn_download_decompressed.setEnabled(False)

    def load_image(self):
        # Open file dialog to let user select an image
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Image", 
            "", 
            "Images (*.jpg *.png *.jpeg *.bmp)"
        )
        
        if file_path:
            # Store the file path
            self.image_path = file_path
            
            # Load the image using PIL and convert to RGB
            img = Image.open(file_path).convert("RGB")
            self.original_image = np.array(img)
            
            # Display the image in the UI
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio)
            self.ui.lbl_original.setPixmap(scaled_pixmap)
            
            # Enable compress button
            self.ui.btn_compress.setEnabled(True)
            
            # Reset the output display
            self.ui.lbl_result.setText("Decompressed Image")
            self.ui.btn_download_compressed.setEnabled(False)
            self.ui.btn_download_decompressed.setEnabled(False)

    def compress_image(self):
        # Step 1: Compress the image using JPEG algorithm
        self.compressed_data = jpeg_compress(self.original_image)
        
        # Step 2: Decompress to show the result
        self.decompressed_image = jpeg_decompress(self.compressed_data)
        
        # Step 3: Display the decompressed image
        height, width, channels = self.decompressed_image.shape
        
        # Convert numpy array to QImage for display
        q_image = QImage(
            self.decompressed_image.data, 
            width, 
            height, 
            3 * width, 
            QImage.Format_RGB888
        )
        
        # Convert QImage to pixmap and scale it
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio)
        self.ui.lbl_result.setPixmap(scaled_pixmap)
        
        # Step 4: Calculate and show compression statistics
        original_bytes, compressed_bytes, compression_ratio = calculate_compression_stats(self.compressed_data)
        
        # Show statistics to user
        stats_message = f"Compression Complete!\n\n"
        stats_message += f"Original Size: {original_bytes/1024:.1f} KB\n"
        stats_message += f"Compressed Size: ~{compressed_bytes/1024:.1f} KB\n"
        stats_message += f"Compression Ratio: {compression_ratio:.2f}:1"
        
        QMessageBox.information(self, "Success", stats_message)
        
        # Enable download buttons
        self.ui.btn_download_compressed.setEnabled(True)
        self.ui.btn_download_decompressed.setEnabled(True)

    def save_compressed(self):
        # Check if we have compressed image
        if self.decompressed_image is None:
            QMessageBox.warning(self, "Error", "No compressed image to save!")
            return
        
        # Get the original filename without extension
        original_filename = os.path.basename(self.image_path)
        name_without_ext = original_filename.split('.')[0]
        default_filename = name_without_ext + "_compressed.jpg"
        
        # Show save file dialog
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Compressed Image", 
            default_filename, 
            "JPEG (*.jpg)"
        )
        
        if save_path:
            # Save the image as JPEG with quality 50 (more compression)
            pil_image = Image.fromarray(self.decompressed_image)
            pil_image.save(save_path, "JPEG", quality=50, optimize=True)
            
            # Calculate actual file sizes
            original_file_size = os.path.getsize(self.image_path)
            compressed_file_size = os.path.getsize(save_path)
            actual_ratio = original_file_size / compressed_file_size if compressed_file_size > 0 else 0
            
            # Show success message with file sizes
            success_message = f"Image saved successfully!\n\n"
            success_message += f"Original File: {original_file_size/1024:.1f} KB\n"
            success_message += f"Compressed File: {compressed_file_size/1024:.1f} KB\n"
            success_message += f"Actual Ratio: {actual_ratio:.2f}:1"
            
            QMessageBox.information(self, "Saved", success_message)

    def save_decompressed(self):
        # Check if we have decompressed image
        if self.decompressed_image is None:
            QMessageBox.warning(self, "Error", "No decompressed image to save!")
            return
        
        # Get the original filename without extension
        original_filename = os.path.basename(self.image_path)
        name_without_ext = original_filename.split('.')[0]
        default_filename = name_without_ext + "_decompressed.png"
        
        # Show save file dialog
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Decompressed Image", 
            default_filename, 
            "PNG (*.png)"
        )
        
        if save_path:
            # Save the decompressed image
            pil_image = Image.fromarray(self.decompressed_image)
            pil_image.save(save_path)
            
            QMessageBox.information(self, "Saved", "Decompressed image saved successfully!")
