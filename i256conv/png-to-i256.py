# Invoke like:
# $ python png-to-i256.py mypic.png output.256

from PIL import Image
import subprocess
from math import sqrt
import sys, tempfile

def lzsa_compress(buffer):
    f = tempfile.mktemp()
    o = tempfile.mktemp()
    
    try:
        with open(f, 'wb') as file:
            file.write(buffer)
        print(f"    wrote {len(buffer)} bytes to '{f}' successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
   
    try:    
      subprocess.run(['lzsa', '-c', '-f2', '-r', f, o])
    except Exception as e:
        print(f"An error occurred: {e}")

    try:
        with open(o, mode="rb") as f:
            data = f.read()
    except Exception as e:
        print(f"An error occurred: {e}")
    
    print(f"    read {len(data)} compress bytes")

    return data

def pal_to_clut(pal):
    clut = []
    for rgb in pal:
        if rgb[0] == -1:
             clut.append(0)
             clut.append(0)
             clut.append(0)
             clut.append(0)
        else:
            clut.append(rgb[2])
            clut.append(rgb[1])
            clut.append(rgb[0])
            clut.append(0xFF)
    return clut

def compress_chunks(chunks):
    compressed_chunks = []
    for chunk in chunks:
        # print(type(chunk))
        # print(len(chunk))
        b = bytearray(b''.join(chunk))  # fuck python
        comp = lzsa_compress(b)
        compressed_chunks.append(comp)
    return compressed_chunks     

# split list into chunk size lists.. why is this not a thing?
def data_to_chunks(data, chunk_size):
    return [data[i:i + chunk_size] for i in range(0,len(data), chunk_size)]
    

def distance3d(x1, y1, z1, x2, y2, z2):
	return sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)

def uniquepalette(image):
	hist = set()
	for j in range(image.size[1]):
		for i in range(image.size[0]):
			hist.add(image.getpixel((i,j)))
	return hist

def palette_gen(pal_set):
	new = set()
	# this does nothing but was thinking we could squash extra colors here if we wanted
	for rgb in pal_set:
		new.add(rgb)
    # for rgb in pal_set:
    # 	new.add(min(iigs_colors, key=lambda x: distance3d(x, rgb)))
	return new

### MAIN

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python png-to-i256.py mypic.png output.256")
    else:
        img = Image.open(sys.argv[1])
        rgb_img = img.convert("RGB")	# create the pixel map

        #todo: sorted probably isn't right for this tuple format
        orig_pal = sorted(uniquepalette(rgb_img))	# source palette from gif/png
        print(f'Colors in image = {len(orig_pal)}')
        new_pal = palette_gen(orig_pal)			    # our 4-bit colorspace versions
        image_pal = list(new_pal)					# as a list to index palette colors
        print(f'Colors in new pal = {len(new_pal)}')
        if len(new_pal) < 256:
            print('auto-moving palette out of color 0')
            image_pal.insert(0,(-1,-1,-1))
        pixel_bytes = []
        for j in range(rgb_img.size[1]):
            for i in range(rgb_img.size[0]):
                p1 = rgb_img.getpixel((i,j))
                nearest_idx1 = image_pal.index(min(image_pal, key=lambda x: distance3d(x[0], x[1], x[2], p1[0], p1[1], p1[2])))
                pixel_bytes.append(nearest_idx1.to_bytes(1))

        # print(pixel_bytes)
        print(f' len pixel bytes: {len(pixel_bytes)}')
        # print(new_pal)


        clut = pal_to_clut(image_pal)
        clut_lz = lzsa_compress(bytes(clut))
        clut_lz_len = len(clut_lz)

        pixel_chunks = data_to_chunks(pixel_bytes, 65536)
        # print(pixel_chunks)
        compressed_pixel_chunks = compress_chunks(pixel_chunks)



        i256data = bytearray()
        i256data.extend(bytes('I256', 'ascii'))
        i256data.extend(int(0).to_bytes(4))  # len bytes, will modify
        i256data.extend(int(0).to_bytes(2))  # v0.0
        i256data.extend(int(rgb_img.size[0]).to_bytes(2, 'little'))  # v0.0
        i256data.extend(int(rgb_img.size[1]).to_bytes(2, 'little'))  # v0.0
        i256data.extend(int(0).to_bytes(2, 'little'))  # 2 reserved bytes

        i256data.extend(bytes('CLUT', 'ascii'))
        i256data.extend(int(10+clut_lz_len).to_bytes(4, 'little')) # chunk len including 10 byte header
        i256data.extend(int(len(image_pal)|0x8000).to_bytes(2, 'little'))  # num colors + high bit meaning compressed
        print(f'numcolorszz 0x{int(len(image_pal)|0x8000):04x}')
        i256data.extend(clut_lz)

        i256data.extend(bytes('PIXL', 'ascii'))
        # get length of pixel data + space for blob size word + 10 byte header
        chunk_length = sum([len(x) for x in compressed_pixel_chunks]) + len(compressed_pixel_chunks)*2 + 10
        print(chunk_length)
        i256data.extend(int(chunk_length).to_bytes(4, 'little')) # {ChunkLength}
        i256data.extend(len(compressed_pixel_chunks).to_bytes(2, 'little')) # {NumBlobs}
        for c in compressed_pixel_chunks:
            print(f'LEN: {len(c)}')
            i256data.extend(len(c).to_bytes(2, 'little')) # blob length
            i256data.extend(c)

        filelen = len(i256data).to_bytes(4,'little')

        for z in range(4):
            i256data[4+z] = filelen[0+z]


        outname=sys.argv[2]
        with open(outname, 'wb') as file:
            file.write(i256data)              
