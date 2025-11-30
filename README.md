# JPEG-like Compression and App Flow (Beginner Friendly)

This app loads an image, compresses it using a simple JPEG-like approach (DCT + quantization + RLE), shows the decompressed result, and can save/load a custom `.dat` file.

## App Flow (window.py)
- Load Image: pick an image with a file dialog, convert to RGB using PIL, show it.
- Compress:
  - Calls `jpeg_compress(image)` to produce compressed data.
  - Immediately calls `jpeg_decompress(compressed_data)` to show how the result looks.
  - Shows basic compression stats (original vs. compressed size).
- Save Compressed:
  - Serializes the compressed data into a binary stream.
  - Packs a small header and all block data, then compresses with zlib.
  - Writes to a `.dat` file.
- Load Compressed:
  - Reads the `.dat`, zlib-decompresses it.
  - Parses the header and block data back into the same structure used by `jpeg_decompress`.
  - Displays the reconstructed image.
- Save Decompressed:
  - Saves the decompressed numpy array as a PNG.

### Serialization format (.dat)
- Magic/version: `JQZ1` (4 bytes)
- Image shape: little-endian `<III` for height, width, channels (12 bytes)
- For each channel:
  - Block count: `<I`
  - For each block:
    - DC coefficient: `<h` (int16)
    - Number of AC pairs: `<H` (uint16)
    - Each AC pair: zeros `<B` (uint8), value `<h` (int16)
- Entire buffer is compressed with zlib (deflate).

## Compression (jpeg_algo.py)
This imitates the main steps of JPEG, simplified:

1. Convert to float32 and work per color channel (R, G, B). Shift values by `-128` to center around zero.
2. Split the image into 8x8 blocks. If a block touches the right/bottom edge, pad by repeating edge pixels so the block becomes 8x8.
3. DCT (Discrete Cosine Transform):
   - Apply 2D DCT: `dct2(block)` which runs DCT on rows and columns with `norm="ortho"`.
   - DCT moves energy to low-frequency coefficients (top-left).
4. Quantization:
   - Divide by a fixed 8x8 quantization table `Q` and round to integers.
   - This reduces precision (lossy), making many coefficients become zero.
5. Zigzag + RLE:
   - Read the 8x8 coefficients in zigzag order (low to high frequency).
   - DC (first value) is stored directly.
   - AC (rest) are stored using Run-Length Encoding (count zeros, then store the next non-zero).
6. Return:
   - A list of blocks per channel where each block is `{ "dc": int, "ac": [(zeros, value), ...] }`.
   - Also return the original image shape.

## Decompression (jpeg_algo.py)
1. For each channel, iterate blocks in the same 8x8 layout.
2. Rebuild the zigzag list:
   - Set DC to the first value.
   - Fill AC by skipping zeros and placing the next non-zero, following the stored pairs.
3. Convert zigzag list back to 8x8 block.
4. Dequantize:
   - Multiply by the quantization table `Q`.
5. Inverse DCT:
   - Apply `idct2`, then add `+128` to shift values back to 0–255 range.
6. Copy the 8x8 block to the output image (trim edges for last partial blocks).
7. After all channels are done, clip values to `[0, 255]` and convert to `uint8`.

## Compression stats
- Original size: `height * width * channels` bytes (assuming 1 byte per pixel per channel).
- Estimated compressed size:
  - 2 bytes per block for DC.
  - 3 bytes per AC pair (1 for zeros, 2 for value).
  - +128 bytes overhead for the header.
- Ratio: `original_size / compressed_size`.

## Why the result looks acceptable
- DCT and quantization remove high-frequency detail (mostly invisible).
- RLE on zigzag order compresses runs of zeros efficiently.
- The approach is lossy but aims to keep important low-frequency details.

## Notes
- We use little-endian struct packing (`<`) to avoid platform differences.
- zlib makes the `.dat` smaller beyond our RLE.
- The code is written with simple loops to be beginner-friendly.
