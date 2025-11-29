import numpy as np
from scipy.fftpack import dct, idct

# JPEG quantization table - this table is used to compress the image
Q = np.array([
    [16,11,10,16,24,40,51,61],
    [12,12,14,19,26,58,60,55],
    [14,13,16,24,40,57,69,56],
    [14,17,22,29,51,87,80,62],
    [18,22,37,56,68,109,103,77],
    [24,35,55,64,81,104,113,92],
    [49,64,78,87,103,121,120,101],
    [72,92,95,98,112,100,103,99]
], dtype=np.float32)


def dct2(block):
    # Apply DCT (Discrete Cosine Transform) to the block
    return dct(dct(block.T, norm="ortho").T, norm="ortho")

def idct2(block):
    # Apply inverse DCT to reconstruct the block
    return idct(idct(block.T, norm="ortho").T, norm="ortho")


# Zigzag pattern indices for 8x8 block
zigzag_order = None

def get_zigzag_order():
    # This function creates zigzag pattern for scanning 8x8 blocks
    global zigzag_order
    if zigzag_order is not None:
        return zigzag_order
    
    indices = []
    for sum_val in range(0, 15):  # sum goes from 0 to 14
        if sum_val % 2 == 0:
            # Move down-left
            x = min(sum_val, 7)
            y = sum_val - x
            while x >= 0 and y <= 7:
                indices.append((x, y))
                x -= 1
                y += 1
        else:
            # Move up-right
            y = min(sum_val, 7)
            x = sum_val - y
            while y >= 0 and x <= 7:
                indices.append((x, y))
                x += 1
                y -= 1
    
    zigzag_order = indices
    return zigzag_order


def convert_block_to_zigzag(block):
    # Convert 8x8 block to zigzag order list
    indices = get_zigzag_order()
    zigzag_list = []
    for (x, y) in indices:
        zigzag_list.append(int(block[x, y]))
    return zigzag_list


def convert_zigzag_to_block(zigzag_list):
    # Convert zigzag list back to 8x8 block
    indices = get_zigzag_order()
    block = np.zeros((8, 8), dtype=np.float32)
    for i, (x, y) in enumerate(indices):
        block[x, y] = zigzag_list[i]
    return block


def encode_block_with_rle(quantized_block):
    # Encode block using Run-Length Encoding (RLE)
    # This saves space by storing zeros more efficiently
    zigzag_values = convert_block_to_zigzag(quantized_block)
    zigzag_values = [int(v) for v in zigzag_values]
    
    # First value is DC coefficient (stores separately)
    dc_value = zigzag_values[0]
    
    # Rest are AC coefficients
    ac_values = zigzag_values[1:]
    
    # Encode AC coefficients with RLE
    encoded_ac = []
    zero_count = 0
    
    for value in ac_values:
        if value == 0:
            zero_count += 1
            # Limit zero run to 255
            if zero_count == 255:
                encoded_ac.append((255, 0))
                zero_count = 0
        else:
            encoded_ac.append((zero_count, int(value)))
            zero_count = 0
    
    # Return dictionary with DC and encoded AC values
    return {"dc": int(dc_value), "ac": encoded_ac}


def decode_block_from_rle(encoded_data):
    # Decode RLE encoded block back to 8x8 block
    dc_value = int(encoded_data["dc"])
    ac_pairs = encoded_data["ac"]
    
    # Create zigzag list with all 64 values
    zigzag_values = [0] * 64
    zigzag_values[0] = dc_value
    
    # Decode AC coefficients
    position = 1
    for (zeros, value) in ac_pairs:
        position += zeros  # Skip zeros
        if position >= 64:
            break
        zigzag_values[position] = int(value)
        position += 1
    
    # Convert zigzag back to 8x8 block
    block = convert_zigzag_to_block(zigzag_values)
    return block.astype(np.int16)


def jpeg_compress(img):
    # Main compression function
    # Input: RGB image (height x width x 3)
    # Output: compressed data
    
    img = img.astype(np.float32)
    height, width, channels = img.shape
    
    # Store compressed data for each color channel
    all_compressed_channels = []
    
    # Process Red, Green, and Blue channels separately
    for channel_num in range(3):
        # Get one color channel
        channel_data = img[:, :, channel_num] - 128  # Shift values to -128 to 127
        compressed_blocks = []
        
        # Process image in 8x8 blocks
        for row in range(0, height, 8):
            for col in range(0, width, 8):
                # Extract 8x8 block
                block = channel_data[row:row+8, col:col+8]
                block_height, block_width = block.shape
                
                # Pad incomplete blocks (at edges)
                if (block_height, block_width) != (8, 8):
                    padded_block = np.zeros((8, 8), dtype=np.float32)
                    padded_block[:block_height, :block_width] = block
                    
                    # Fill padded area with edge values
                    if block_height < 8:
                        padded_block[block_height:8, :block_width] = padded_block[block_height-1:block_height, :block_width]
                    if block_width < 8:
                        padded_block[:block_height, block_width:8] = padded_block[:block_height, block_width-1:block_width]
                    if block_height < 8 and block_width < 8:
                        padded_block[block_height:8, block_width:8] = padded_block[block_height-1, block_width-1]
                    
                    block = padded_block
                
                # Apply DCT transform
                dct_block = dct2(block)
                
                # Quantize (divide by Q table and round)
                quantized_block = np.round(dct_block / Q).astype(np.int16)
                
                # Encode with RLE
                encoded_block = encode_block_with_rle(quantized_block)
                compressed_blocks.append(encoded_block)
        
        all_compressed_channels.append(compressed_blocks)
    
    # Return compressed data and original shape
    return (all_compressed_channels, img.shape)


def jpeg_decompress(compressed_data):
    # Main decompression function
    # Input: compressed data
    # Output: reconstructed RGB image
    
    all_compressed_channels, original_shape = compressed_data
    height, width, channels = original_shape
    
    # Create empty image to store result
    result_image = np.zeros((height, width, 3), dtype=np.float32)
    
    # Process each color channel
    for channel_num in range(3):
        compressed_blocks = all_compressed_channels[channel_num]
        channel_data = np.zeros((height, width), dtype=np.float32)
        
        block_index = 0
        
        # Reconstruct image from 8x8 blocks
        for row in range(0, height, 8):
            for col in range(0, width, 8):
                if block_index >= len(compressed_blocks):
                    break
                
                # Decode RLE to get quantized block
                encoded_block = compressed_blocks[block_index]
                quantized_block = decode_block_from_rle(encoded_block).astype(np.float32)
                
                # Dequantize (multiply by Q table)
                dct_block = quantized_block * Q
                
                # Apply inverse DCT
                reconstructed_block = idct2(dct_block) + 128  # Shift back to 0-255
                
                # Copy block to output (handle edges)
                block_height = min(8, height - row)
                block_width = min(8, width - col)
                channel_data[row:row+block_height, col:col+block_width] = reconstructed_block[:block_height, :block_width]
                
                block_index += 1
        
        # Store channel in result image
        result_image[:, :, channel_num] = channel_data
    
    # Clip values to 0-255 and convert to uint8
    result_image = np.clip(result_image, 0, 255).astype(np.uint8)
    return result_image


def calculate_compression_stats(compressed_data):
    # Calculate compression statistics
    # Returns: original size, compressed size, compression ratio
    
    all_compressed_channels, original_shape = compressed_data
    height, width, channels = original_shape
    
    # Original size (1 byte per pixel per channel)
    original_size = int(height) * int(width) * int(channels)
    
    # Estimate compressed size
    compressed_size = 0
    
    for channel_blocks in all_compressed_channels:
        for encoded_block in channel_blocks:
            # 2 bytes for DC value
            compressed_size += 2
            
            # For each AC pair: 1 byte for zero count + 2 bytes for value
            for zeros, value in encoded_block["ac"]:
                compressed_size += 1  # zero count
                compressed_size += 2  # value
    
    # Add small header overhead
    compressed_size += 128
    
    # Calculate compression ratio
    if compressed_size > 0:
        ratio = original_size / compressed_size
    else:
        ratio = float('inf')
    
    return original_size, compressed_size, ratio
