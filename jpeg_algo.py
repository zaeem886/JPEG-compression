import numpy as np
from scipy.fftpack import dct, idct

Q = (np.array([
    [16,11,10,16,24,40,51,61],
    [12,12,14,19,26,58,60,55],
    [14,13,16,24,40,57,69,56],
    [14,17,22,29,51,87,80,62],
    [18,22,37,56,68,109,103,77],
    [24,35,55,64,81,104,113,92],
    [49,64,78,87,103,121,120,101],
    [72,92,95,98,112,100,103,99]
], dtype=np.float32) * 2)

#this applies 2d dct to a block so we can separate low and high frequencies
def dct2(b): return dct(dct(b.T, norm="ortho").T, norm="ortho")

#this applies inverse dct to bring the block back to normal image values
def idct2(b): return idct(idct(b.T, norm="ortho").T, norm="ortho")

#this list defines the zigzag order for reading 8x8 coefficients from low to high frequency
ZIGZAG = [
    (0,0),(0,1),(1,0),(2,0),(1,1),(0,2),(0,3),(1,2),
    (2,1),(3,0),(4,0),(3,1),(2,2),(1,3),(0,4),(0,5),
    (1,4),(2,3),(3,2),(4,1),(5,0),(6,0),(5,1),(4,2),
    (3,3),(2,4),(1,5),(0,6),(0,7),(1,6),(2,5),(3,4),
    (4,3),(5,2),(6,1),(7,0),(7,1),(6,2),(5,3),(4,4),
    (3,5),(2,6),(1,7),(2,7),(3,6),(4,5),(5,4),(6,3),
    (7,2),(7,3),(6,4),(5,5),(4,6),(3,7),(4,7),(5,6),
    (6,5),(7,4),(7,5),(6,6),(5,7),(6,7),(7,6),(7,7)
]

#this converts an 8x8 block into a 64-length list using zigzag order
def block_to_zigzag(block):
    out = []
    for x, y in ZIGZAG:
        out.append(int(block[x, y]))
    return out

#this takes a 64-length zigzag list and places values back into an 8x8 block
def zigzag_to_block(lst):
    b = np.zeros((8, 8), dtype=np.float32)
    for i, (x, y) in enumerate(ZIGZAG):
        b[x, y] = lst[i]
    return b

#this encodes the quantized block using simple rle to store runs of zeros efficiently
def encode_block_with_rle(qb):
    zz = [int(v) for v in block_to_zigzag(qb)]
    dc = zz[0]; ac_vals = zz[1:]
    ac = []; zeros = 0
    for v in ac_vals:
        if v == 0:
            zeros += 1
            if zeros == 255:
                ac.append((255, 0)); zeros = 0
        else:
            ac.append((zeros, int(v))); zeros = 0
    return {"dc": int(dc), "ac": ac}

#this decodes rle back into a quantized 8x8 block using the zigzag positions
def decode_block_from_rle(enc):
    dc = int(enc["dc"]); ac_pairs = enc["ac"]
    zz = [0] * 64; zz[0] = dc
    pos = 1
    for z, v in ac_pairs:
        pos += z
        if pos >= 64: break
        zz[pos] = int(v)
        pos += 1
    return zigzag_to_block(zz).astype(np.int16)

#this compresses the image with dct, quantization, zigzag and rle for each 8x8 block
def jpeg_compress(img):
    img = img.astype(np.float32)
    h, w, _ = img.shape
    channels = []
    for ch in range(3):
        plane = img[:, :, ch] - 128
        blocks = []
        for r in range(0, h, 8):
            for c in range(0, w, 8):
                blk = plane[r:r+8, c:c+8]
                bh, bw = blk.shape
                if (bh, bw) != (8, 8):
                    pad = np.zeros((8, 8), dtype=np.float32)
                    pad[:bh, :bw] = blk
                    if bh < 8: pad[bh:8, :bw] = pad[bh-1:bh, :bw]
                    if bw < 8: pad[:bh, bw:8] = pad[:bh, bw-1:bw]
                    if bh < 8 and bw < 8: pad[bh:8, bw:8] = pad[bh-1, bw-1]
                    blk = pad
                dctb = dct2(blk)
                q = np.round(dctb / Q).astype(np.int16)
                blocks.append(encode_block_with_rle(q))
        channels.append(blocks)
    return (channels, img.shape)

#this rebuilds the image from compressed blocks using inverse steps and returns an rgb array
def jpeg_decompress(comp):
    channels, (h, w, c) = comp
    out = np.zeros((h, w, 3), dtype=np.float32)
    for ch in range(3):
        blocks = channels[ch]
        plane = np.zeros((h, w), dtype=np.float32)
        i = 0
        for r in range(0, h, 8):
            for c0 in range(0, w, 8):
                if i >= len(blocks): break
                q = decode_block_from_rle(blocks[i]).astype(np.float32)
                dctb = q * Q
                rec = idct2(dctb) + 128
                bh = min(8, h - r); bw = min(8, w - c0)
                plane[r:r+bh, c0:c0+bw] = rec[:bh, :bw]
                i += 1
        out[:, :, ch] = plane
    return np.clip(out, 0, 255).astype(np.uint8)

#this estimates compressed size and shows a simple compression ratio for the image
def calculate_compression_stats(comp):
    channels, (h, w, c) = comp
    original_size = int(h) * int(w) * int(c)
    compressed_size = 0
    for ch in channels:
        for blk in ch:
            compressed_size += 2  # DC
            for z, v in blk["ac"]:
                compressed_size += 1 + 2
    compressed_size += 128
    ratio = original_size / compressed_size if compressed_size > 0 else float('inf')
    return original_size, compressed_size, ratio
