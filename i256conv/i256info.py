
import sys, tempfile
import subprocess
import pygame
from pygame.locals import *


def lzsa_expand(buffer):
    f = tempfile.mktemp()
    o = tempfile.mktemp()
    try:
        with open(f, 'wb') as file:
            file.write(buffer)
        print(f"    Bytes saved to '{f}' successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
   
    try:    
      subprocess.run(['lzsa', '-d', '-f2', '-r', f, o])
    except Exception as e:
        print(f"An error occurred: {e}")
    try:
        with open(o, mode="rb") as f:
            data = f.read()
    except Exception as e:
        print(f"An error occurred: {e}")
    print(f"    read {len(data)} decompressed bytes in {o}")

    return data

def render_defaults(img):
    SCREEN_X=img.width
    SCREEN_Y=img.height
    SCREEN_PIXELS = img.width * img.height

    surface = pygame.display.set_mode((SCREEN_X, SCREEN_Y))
    # pxarray = pygame.PixelArray(surface)
    # pxarray[0:SCREEN_PIXELS] = 0xff00ff
    # pxarray.close()
    # pygame.display.flip()

    clut = img.cluts[0]
    pixl = img.pixls[0].get_blobs()

    pxarray = pygame.PixelArray(surface)
    pxarray[0:SCREEN_PIXELS] = 0x110011
    for y in range(0,SCREEN_Y):
        for x in range(0, SCREEN_X):
            byteidx = (y*SCREEN_X)+x
            try:
                byte = pixl[byteidx]
            except:
                print(f' oops {byteidx}')
                continue
            pal = clut.clut_data

            # BGRA
            color_b = pal[(byte*4)]
            color_g = pal[(byte*4)+1]
            color_r = pal[(byte*4)+2]
            color_a = pal[(byte*4)+3]
            rrggbb = (color_r<<16) + (color_g<<8) + (color_b)
            # print(f' 0x{rrggbb:06x}', end='')
            pxarray[x][y] = rrggbb
           # print(x,y, hex(rrggbb))
    pxarray.close()
    pygame.display.flip()
    waitkey()

def waitkey():
    pygame.event.clear()
    while True:
        event = pygame.event.wait()
        if event.type == KEYDOWN:
            return
            if event.key == K_q:
                return

# class lzsa2:  
#     def __init__(self):
#         self.bytes_cursor = 0
#         self.bytes = b''
#         self.length = 0
#         self.decompressed = b''
#         self.decompressed_cursor = 0
    
#     def set_bytes(self, b):
#         self.bytes = b
#         self.length = len(b)

#     def get_bytes(self, count, endianness='little'):
#         v = int.from_bytes(self.bytes[self.bytes_cursor:self.bytes_cursor+count], endianness)
#         self.bytes_cursor += count
#         return(v)
    
#     def get_byte(self):
#         return(self.get_bytes(1))
    
#     def decompress(self):
#         self.bytes_cursor = 0
#         self.decompressed_cursor = 0
#         while self.bytes_cursor < self.length:
#             token = self.get_byte()
#             L = (token >> 3) | 0b00000011   # number of literals, 0 to 2... 3= extra literals nibbles/bytes to follow
#             M = token | 0b00000111          # encoded match length, 0 to 6... 7= extra match nibbles/bytes to follow
#             XYZ = (token >> 5) | 0b00000111 # how to decode match offset

class CLUT:
    def __init__(self):
        self.num_colors = 0
        self.clut_data = 0

    def __init__(self, num_colors, clut_data):
        self.num_colors = num_colors
        self.clut_data = clut_data



class PIXL:
    def __init__(self):
        self.pixl_data_blobs = []

    def add_blob(self, pixl_data):
        print(f'     add_blob() -adding blob of {len(pixl_data)}')
        self.pixl_data_blobs.append(pixl_data)

    def get_blobs(self):
        return [item for row in self.pixl_data_blobs for item in row]
    

class I256:

    ID_STR_CONST = b'I256'
    CHUNK_PIXL_STR_CONST = b'PIXL'
    CHUNK_CLUT_STR_CONST = b'CLUT'
    CHUNK_TMAP_STR_CONST = b'TMAP'


    def __init__(self):
        self.bytes_cursor = 0
        self.bytes = b''        # lol I don't know what you're supposed to do in python
        self.length = 0         # LONG
        self.versionstr = '0.0'
        self.vm = 0             # BYTE
        self.vl = 0             # BYTE
        self.width = 0          # WORD
        self.height = 0         # WORD

        self.reset_ptr = 0         # HACK - set to reset point... start of ANIM? 
        
        self.chunks = []
        self.fb_bytes = bytearray(0x8000)
        self.fb_bytes_cursor = 0
        self.debug = False
        self.cluts = []
        self.tmaps = []
        self.pixls = []

    def load(self, filename):
        with open(filename, mode="rb") as f:
            self.bytes = f.read()
    
    def debuglog(self, str):
        if self.debug:
            self.log(str)

    def log(self, str):
        print(f'>> {str}')

    def scanstr(self, match):
        # self.debuglog(f'scanstr(): {self.bytes[self.bytes_cursor:self.bytes_cursor+len(match)]} == {match} ?  = {self.bytes[self.bytes_cursor:self.bytes_cursor+len(match)] == match}')
        return self.bytes[self.bytes_cursor:self.bytes_cursor+len(match)] == match

    # cursor advance strlen
    def curadvstr(self, match):
        self.bytes_cursor += len(match)

    def data_remaining(self):
        return self.bytes_cursor < len(self.bytes)

    def get_bytes(self, count, endianness='little'):
        v = int.from_bytes(self.bytes[self.bytes_cursor:self.bytes_cursor+count], endianness)
        self.bytes_cursor += count
        return(v)
    
    def get_byte_stream(self, count):
        v = []
        for i in range(0, count):
            v.append(self.get_byte())
        return bytes(v)

    def get_byte(self):
        return(self.get_bytes(1))
    
    def get_word(self):
        return(self.get_bytes(2))

    def get_long(self):
        return(self.get_bytes(4))

    def get_header(self):
        self.debuglog("----- I256 HEADER -----")
        self.get_idstr()
        self.get_len()
        self.get_version()
        self.get_size()
        self.get_byte() # reserved 1
        self.get_byte() # reserved 2
        # print(f'v{self.versionstr}')
        # print(f'x:{self.width} y:{self.height}')
        self.debuglog("----- END HEADER -----")
        

    def get_idstr(self):
        if self.scanstr(self.ID_STR_CONST):
            self.curadvstr(self.ID_STR_CONST)
        else:
            raise Exception("No header")

        
    def get_len(self):
        self.length = self.get_long()
        self.debuglog(f'Length: {self.length:08x}  =  {self.length}')

    def get_version(self):
        self.vl = self.get_byte()
        self.vh = self.get_byte()
        self.versionstr = f'{self.vh}.{self.vl}'
        self.debuglog(f'Version: {self.versionstr} ')

    def get_size(self):
        self.width = self.get_word()
        self.height = self.get_word()
        self.debuglog(f'Size: {self.width:04x} x {self.height:04x}  =  {self.width} x {self.height}')

    def get_chunk(self):
        if self.scanstr(self.CHUNK_PIXL_STR_CONST):
            self.get_chunk_pixl()
        elif self.scanstr(self.CHUNK_CLUT_STR_CONST):
            self.get_chunk_clut()
        elif self.scanstr(self.CHUNK_TMAP_STR_CONST):
            self.get_chunk_tmap()
        else:
            raise Exception('YOU DONE CHUNKED UP NOW!!')
    

    def get_chunk_pixl(self):
        self.debuglog("----- PIXL -----")
        self.curadvstr(self.CHUNK_PIXL_STR_CONST)   # SKIP ID BYTES
        header_len = 0xA
        chunk_len = self.get_long()
        num_blobs = self.get_word()
        self.debuglog(f'chunk_len: {chunk_len}  num_blobs: {num_blobs}')
        pixl = PIXL()
        for i in range(num_blobs):  
            sizeinfo = self.get_word()
            if sizeinfo == 0:
                compressed = False
                blob_size =  65536  # this is what the doc sez... shrug
                print(f"{sizeinfo} ALERT!!!")
            else:
                compressed = True
                blob_size = sizeinfo
            data = self.get_byte_stream(blob_size)
            if compressed:
                data = lzsa_expand(data)
            
            pixl.add_blob(data)
        self.pixls.append(pixl)
        # a= self.get_byte_stream(chunk_len-header_len)
        self.debuglog('----- END PIXL ----')


    def get_chunk_clut(self):
        self.debuglog("----- CLUT -----")
        self.curadvstr(self.CHUNK_CLUT_STR_CONST)   # SKIP ID BYTES
        header_len = 0xA
        chunk_len = self.get_long()
        nc_byte = self.get_word()
        compressed = nc_byte & 0x8000 > 0
        num_colors = nc_byte & 0b0011_1111_1111_1111
        self.debuglog(f'nc_byte: {nc_byte:016b}')
        self.debuglog(f'chunk_len: {chunk_len}  compressed: {compressed}  num_colors: {num_colors}')
        self.debuglog(f'chunk data starts at 0x{self.bytes_cursor:06x}')
        self.debuglog(f' {self.bytes[self.bytes_cursor]:02x} {self.bytes[self.bytes_cursor+1]:02x} {self.bytes[self.bytes_cursor+2]:02x} {self.bytes[self.bytes_cursor+3]:02x}')
        data = self.get_byte_stream(chunk_len-header_len)

        if compressed:
            data = lzsa_expand(data)
        clut = CLUT(num_colors, data)
        self.cluts.append(clut)
        self.debuglog('----- END CLUT ----')



    def get_chunk_tmap(self):
        self.debuglog("----- TMAP -----")
        self.curadvstr(self.CHUNK_PIXL_STR_CONST)   # SKIP ID BYTES
        header_len = 0xE
        chunk_len = self.get_long()
        num_blobs = self.get_word()
        self.debuglog(f'chunk_len: {chunk_len}  num_blobs: {num_blobs}')
        ## SKIP CHUNK FOR NOW
        self.debuglog(' ...skipping')
        a= self.get_byte_stream(chunk_len-header_len)
        self.debuglog('----- END TMAP ----')



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python i256info.py <filename>")
    else:
        filename = sys.argv[1]
        img = I256()
        img.debug = True
        img.load(filename)
        img.get_header()
        while (img.data_remaining()):
            img.get_chunk()   
        # print(len(i.cluts))
        # print(len(i.pixls))
        # for n in range(len(i.pixls)):
        #     print(f'  pixl[{n}].len = {len(i.pixls[n].pixl_data_blobs)}')
        # print(img.pixls[0].pixl_data_blobs[1])
        if True:
            render_defaults(img)