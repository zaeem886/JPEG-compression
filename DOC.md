# Project Documentation (Beginner Friendly)

This app shows a simple JPEG-like compression pipeline and a Qt UI to load images, compress, decompress, and save/load a custom `.dat` file.

---

## jpeg_algo.py (Compression and Decompression)

### Quantization Table (Q)
- Q is an 8x8 matrix with larger numbers for high frequencies.
- We divide DCT coefficients by Q and round to integers to reduce precision (lossy).
- Larger values make more zeros (better compression, lower quality).

### DCT and IDCT
- dct2(block): applies DCT on rows and then columns (norm="ortho").
- idct2(block): inverse of DCT to reconstruct the spatial block.

Why DCT?
- It concentrates most image energy in low-frequency coefficients (top-left in the block).
- High-frequency coefficients often become small/zero after quantization.

### Zigzag Order
- ZIGZAG is a fixed list of (x, y) positions that reads coefficients from low to high frequency.
- block_to_zigzag(block): returns 64 values following ZIGZAG.
- zigzag_to_block(list): fills an 8x8 block using ZIGZAG positions.

### Run-Length Encoding (RLE)
- encode_block_with_rle(quantized_block):
  - First element is DC (stored directly).
  - Remaining 63 AC values: count zeros until a non-zero appears, store (zero_count, value).
  - If zero_count hits 255, flush as (255, 0) and continue.
- decode_block_from_rle(encoded):
  - Start with a 64-length list of zeros.
  - Place DC at index 0.
  - For each (zeros, value), move forward by `zeros`, write `value`, then move one step.

### Compression: jpeg_compress(img)
- Convert image to float32.
- For each channel (R, G, B):
  - Shift values by -128 (center around 0).
  - Process the image in 8x8 blocks:
    - If at the right/bottom edges, pad by repeating the last row/column so the block is 8x8.
    - Apply DCT (dct2).
    - Quantize: divide by Q and round to int16.
    - Encode with RLE (returns {"dc": int, "ac": [(zeros, val), ...]}).
  - Collect all blocks for the channel.
- Return (channels, original_shape).

Data structure returned:
- channels: List of 3 items (for R, G, B).
- Each channel: list of blocks, each block is {"dc": int, "ac": [(zeros, value), ...]}.
- original_shape: (height, width, 3).

### Decompression: jpeg_decompress(compressed_data)
- Unpack: channels, (h, w, c).
- For each channel:
  - Allocate an empty plane of shape (h, w).
  - Walk through the image in 8x8 steps:
    - Decode block from RLE to an 8x8 quantized block.
    - Dequantize: multiply by Q.
    - Apply IDCT and add +128 to shift back to 0–255 range.
    - Copy block into the plane (clip at edges for last partial block area).
- Combine channels into an image and clip to [0, 255], convert to uint8.

### Compression Stats: calculate_compression_stats(comp)
- Original size = h * w * c (bytes, 1 byte per pixel per channel).
- Compressed size estimate:
  - 2 bytes for DC in each block.
  - 3 bytes per AC pair (1 byte zeros + 2 bytes value).
  - +128 bytes for a small header.
- Ratio = original_size / compressed_size.

---

## window.py (Qt UI and File Operations)

### UI Setup and State
- MainWindow sets up buttons and labels via Ui_MainWindowUI.
- Tracks:
  - original_image (numpy array)
  - compressed_data (structure from jpeg_compress)
  - decompressed_image (numpy array)
  - image_path (path of the current image or .dat)

### Helpers
- show_array(arr): displays a numpy RGB array in lbl_result.
- pick_open(title, filter): opens a file dialog for choosing a file.
- pick_save(title, default, filter): save file dialog with a default filename.

### Load Image
- pick image file (jpg/png/jpeg/bmp).
- convert to RGB using PIL and keep as numpy array.
- show it on lbl_original.
- enable Compress.

### Compress Image
- Call jpeg_compress(original_image).
- Immediately call jpeg_decompress to show the reconstructed image.
- Show compression stats (original vs. estimated compressed).
- Enable “Download Compressed” and “Download Decompressed”.

### Save Compressed (.dat)
- Serialize compressed_data:
  - Write magic: "JQZ1".
  - Write image shape as little-endian `<III` (height, width, channels).
  - For each channel:
    - Write block count `<I`.
    - For each block:
      - Write DC `<h`.
      - Write number of AC pairs `<H`.
      - For each AC pair: zeros `<B`, value `<h`.
- Compress the whole byte buffer with zlib (deflate, level 9).
- Write to a .dat file.
- Show file sizes and ratio.

Why little-endian `<`?
- Ensures a consistent cross-platform binary format (no padding/alignment surprises).

### Load Compressed (.dat)
- Read file, zlib-decompress.
- Validate magic "JQZ1".
- Parse shape `<III`, channels and blocks exactly as written in Save.
- Reconstruct compressed_data and call jpeg_decompress to get the image.
- Display the image and enable “Download Decompressed”.
- Set image_path to the .dat so default filenames work.

### Save Decompressed (PNG)
- Use PIL to save the decompressed image as a PNG.
- Default filename is based on image_path (image or .dat) with “_decompressed”.

---

## End-to-End Flow
1. Load an image (or load a .dat).
2. Compress (DCT → Quantize → Zigzag → RLE).
3. Decompress (RLE → Zigzag → Dequantize → IDCT).
4. Save compressed as `.dat` (custom format + zlib).
5. Load `.dat` back into the app and decompress.
6. Save decompressed image as `.png`.

---

## Tips
- This is a lossy method; small details can be lost.
- RLE benefits from many zeros created by quantization.
- zlib gives additional compression on the serialized data.
- Code uses simple loops and numpy/PIL/Qt to stay beginner-friendly.
