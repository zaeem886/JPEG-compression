from PySide6.QtWidgets import QWidget, QFileDialog, QMessageBox
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from window_ui import Ui_MainWindowUI
from jpeg_algo import jpeg_compress, jpeg_decompress, calculate_compression_stats
import numpy as np
from PIL import Image
import os, struct, zlib

class MainWindow(QWidget):
    #this sets up the window, ui, initial state and button connections
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindowUI(); self.ui.setupUi(self)
        self.original_image = None
        self.compressed_data = None
        self.decompressed_image = None
        self.image_path = None
        self.ui.btn_load.clicked.connect(self.load_image)
        self.ui.btn_load_compressed.clicked.connect(self.load_compressed_file)
        self.ui.btn_compress.clicked.connect(self.compress_image)
        self.ui.btn_download_compressed.clicked.connect(self.save_compressed)
        self.ui.btn_download_decompressed.clicked.connect(self.save_decompressed)
        self.ui.btn_compress.setEnabled(False)
        self.ui.btn_download_compressed.setEnabled(False)
        self.ui.btn_download_decompressed.setEnabled(False)

    #this shows a numpy rgb image in the result label
    def show_array(self, arr):
        h, w, _ = arr.shape
        qimg = QImage(arr.data, w, h, 3 * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.ui.lbl_result.setPixmap(pix)

    #this opens a file dialog for selecting a file to open
    def pick_open(self, title, filter):
        fp, _ = QFileDialog.getOpenFileName(self, title, "", filter)
        return fp

    #this opens a file dialog for saving a file with a default name
    def pick_save(self, title, default, filter):
        fp, _ = QFileDialog.getSaveFileName(self, title, default, filter)
        return fp

    #this loads an image, converts it to rgb and prepares ui for compression
    def load_image(self):
        fp = self.pick_open("Select Image", "Images (*.jpg *.png *.jpeg *.bmp)")
        if not fp: return
        self.image_path = fp
        img = Image.open(fp).convert("RGB")
        self.original_image = np.array(img)
        pixmap = QPixmap(fp).scaled(300, 300, Qt.KeepAspectRatio)
        self.ui.lbl_original.setPixmap(pixmap)
        self.ui.lbl_result.setText("Decompressed Image")
        self.ui.btn_compress.setEnabled(True)
        self.ui.btn_download_compressed.setEnabled(False)
        self.ui.btn_download_decompressed.setEnabled(False)

    #this compresses the loaded image and shows the decompressed preview and stats
    def compress_image(self):
        if self.original_image is None: return
        self.compressed_data = jpeg_compress(self.original_image)
        self.decompressed_image = jpeg_decompress(self.compressed_data)
        self.show_array(self.decompressed_image)
        orig, comp, ratio = calculate_compression_stats(self.compressed_data)
        
        self.ui.btn_download_compressed.setEnabled(True)
        self.ui.btn_download_decompressed.setEnabled(True)

    #this saves the compressed data to a .dat file using a small custom binary format + zlib
    def save_compressed(self):
        if self.compressed_data is None:
            QMessageBox.warning(self, "Error", "No compressed data to save!")
            return
        base = os.path.splitext(os.path.basename(self.image_path or "image"))[0]
        save_path = self.pick_save("Save Compressed Data", base + "_compressed.dat", "Compressed Data (*.dat)")
        if not save_path: return
        all_channels, (h, w, c) = self.compressed_data
        try:
            buf = bytearray()
            buf += b"JQZ1"
            buf += struct.pack("<III", int(h), int(w), int(c))
            for ch in all_channels:
                buf += struct.pack("<I", len(ch))
                for enc in ch:
                    buf += struct.pack("<h", int(enc["dc"]))
                    ac = enc["ac"]
                    buf += struct.pack("<H", len(ac))
                    for zeros, val in ac:
                        buf += struct.pack("<Bh", int(zeros) & 0xFF, int(val))
            data = zlib.compress(bytes(buf), level=9)
            with open(save_path, "wb") as f: f.write(data)
            orig_size = os.path.getsize(self.image_path) if self.image_path else h * w * c
            comp_size = os.path.getsize(save_path)
            ratio = (orig_size / comp_size) if comp_size else 0.0
            msg = (f"Compressed data saved.\n\nOriginal: {orig_size/1024:.1f} KB\n"
                   f"Compressed (.dat): {comp_size/1024:.1f} KB\nRatio: {ratio:.2f}:1\n\n"
                   "Format: zlib(deflate) of [JQZ1][h,w,c][per-channel blocks].")
            if ratio < 1.0: msg += "\nNote: small/already compressed images may not compress well."
            QMessageBox.information(self, "Saved", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    #this saves the decompressed image as a png so we can download the result easily
    def save_decompressed(self):
        if self.decompressed_image is None:
            QMessageBox.warning(self, "Error", "No decompressed image to save!")
            return
        base = os.path.splitext(os.path.basename(self.image_path or "image"))[0]
        save_path = self.pick_save("Save Decompressed Image", f"{base}_decompressed.png", "PNG (*.png)")
        if not save_path: return
        try:
            Image.fromarray(self.decompressed_image).save(save_path)
            QMessageBox.information(self, "Saved", "Decompressed image saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    #this loads a .dat file, parses it, decompresses back to an image and shows it
    def load_compressed_file(self):
        fp = self.pick_open("Select Compressed File", "Compressed Data (*.dat)")
        if not fp: return
        try:
            with open(fp, "rb") as f: raw = f.read()
            decompressed = zlib.decompress(raw)
            off = 0
            def read(n):
                nonlocal off
                if off + n > len(decompressed): raise ValueError("Corrupted compressed file (EOF).")
                chunk = decompressed[off:off+n]; off += n; return chunk
            if read(4) != b"JQZ1": raise ValueError("Invalid compressed file magic/version.")
            h, w, c = struct.unpack("<III", read(12))
            all_channels = []
            for _ in range(c):
                num_blocks = struct.unpack("<I", read(4))[0]
                ch = []
                for _ in range(num_blocks):
                    dc = struct.unpack("<h", read(2))[0]
                    num_ac = struct.unpack("<H", read(2))[0]
                    ac = []
                    for _ in range(num_ac):
                        zeros = struct.unpack("<B", read(1))[0]
                        val = struct.unpack("<h", read(2))[0]
                        ac.append((zeros, val))
                    ch.append({"dc": dc, "ac": ac})
                all_channels.append(ch)
            self.compressed_data = (all_channels, (h, w, c))
            self.decompressed_image = jpeg_decompress(self.compressed_data)
            self.image_path = fp
            self.show_array(self.decompressed_image)
            self.ui.lbl_original.setPixmap(self.ui.lbl_result.pixmap())
            self.ui.btn_download_decompressed.setEnabled(True)
            QMessageBox.information(self, "Loaded", "Compressed .dat file loaded and decompressed.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load: {e}")

    #this accepts the close event and lets the app exit cleanly
    def closeEvent(self, event):
        event.accept()
