# i256 file format
Why?  When there are so many image formats would we need another one?

The idea here is to have an image file format, that is specific to the C256/F256.   It is tailored to the specific video hardware, and specific 65816/65c02 CPU.   The idea is that it will be easy to deal with.

The file format makes easy work of storing 256 color bitmaps, and 256 color map data, with corresponding tile catalogs.  It can be used with either bitmap backgrounds, or tilemap backgrounds.

Compression is both fast, and does a great job of keeping the size down.  https://github.com/emmanuel-marty/lzsa, I have chosen LZSA version 2, both because it’s easy to use the compressor, and because the community has provided a nice 6502, and 65816 decompressors.

The file is defined as a byte stream.  It uses a header/length sort of chunk format, because I like this.  It offers the ability to expand the features after the fact.   A file loader can simply skip the chunks of data that it does not understand.

I will attempt to define the format as a "fileoffset:" -> "the thing at that offset"

Header of the File is 16 bytes as follows

File Offset | Data                   |  Comment
------------|:----------------------:|------------------------------------
|           | _File ID_              | 
0           | `0x49`                 |  'I'  Image
1           | `0x32`                 |  '2' 
2           | `0x35`                 |  '5'  
3           | `0x36`                 |  '6'  
4           | {FileLength}           | (32-bit long) File length in bytes
8           | {VL}                   | Version Low - File format Minor version
9           | {VH}                   | Version High - File format Major version.
|           |                        | Currently only version `0x0000` exists.
0xA         | {Width}                | (16-bit word) Display width in bytes
0xC         | {Height}               | (16-bit word) Display height in bytes
0xE         | _Reserved_             | ... 
0xF         | _Reserved_             | ...
0x10  ...   | ... first data chunk   | ... followed by more until end of file... see below

After header comes AIFF style chunks of data, basically a 4 byte chunk name, followed by a 4 byte length (inclusive of the chunk size). The idea is that you can skip chunks you don’t understand.

### Data Chunk Definitions
##### `PIXL`  -  Pixel Data, compressed in the lzsa2
Initial Frame Chunk, this is the data used to first initialize the playback buffer

Chunk Offset | Data                   |  Comment
-------------|:----------------------:|------------------------------------
0            | `0x50`                 |  'P'
1            | `0x49`                 |  'I'
2            | `0x58`                 |  'X'
3            | `0x4c`                 |  'L'
4            | {ChunkLength}          | (32-bit long) Chunk length in bytes, including this 10-byte header
8            | {NumBlobs}             | (16-bit word) Number of compressed blobs that follow

```
// For Each Blob
{
  Word (little endian), compressed size, 0 == raw non compressed data, 64K in size
  Compressed LZSA2 Raw format data
}
```
Total Decompressed size would fit the Frame Width * Frame Height, in bytes

##### `CLUT`  -  Color Lookup Table
Chunk Offset | Data                   |  Comment
-------------|:----------------------:|------------------------------------
0            | `0x43`                 |  'C'
1            | `0x4C`                 |  'L'
2            | `0x55`                 |  'U'
3            | `0x54`                 |  'T'
4            | {ChunkLength}          | (32-bit long) Chunk length in bytes, including this 10-byte header
8            | {NumColors}            | (16-bit word) Number of colors to follow
|            |                        | If high bit set then LZSA2 raw compressed data follows
|            |                        | Typically, this is going to be 256 colors
|            |                        | more than 16384 colors > 64K ... a problem for the compressor
|            |                        |`%10xx_xxxx_xxxx_xxxx` - compressed colors (1-16384 colors)
|            |                        |`%00xx_xxxx_xxxx_xxxx` - uncompressed colors (1-16384 colors)


- B,G,R,A for the Color Index Table, for num colors, or LZSA2 compressed color data, decompress length is 4 * num colors bytes
- The reason for encoding BGRA quads, is so the data can be directly copied, or directly decompressed into the hardware CLUT.

Example uncompressed  256 color entries, would have a length of 1024+10, or 1034 bytes
An encoder may compress this, unless the compressed size is larger than uncompressed



##### `TMAP`  -  Tile Map, compressed in the lzsa2
Chunk Offset | Data                   |  Comment
-------------|:----------------------:|------------------------------------
0            | `0x54`                 |  'T'
1            | `0x4D`                 |  'M'
2            | `0x41`                 |  'A'
3            | `0x50`                 |  'P'
4            | {ChunkLength}          | (32-bit long) Chunk length in bytes, including this 14-byte header
0x8          | {Width}                | (16-bit word) Display width in bytes
0xA          | {Height}               | (16-bit word) Display height in bytes
0xC          | {NumBlobs}             | (16-bit word) Number of blobs to follow

```
// For Each Blob
{
  Word (little endian), compressed size, 0 == raw non compressed data, 64K in size
  Compressed LZSA2 Raw format data
}
```

Uncompressed length should equal  (width * height * 2), since each map entry is 16 bits for the video hardware

## References
- (gone) https://c256foenix.com/?v=7516fd43adaa 
- https://docs.google.com/document/d/10ovgMClDAJVgbW0sOhUsBkVABKWhOPM5Au7vbHJymoA/edit
- https://github.com/FoenixRetro/dwsJason-f256/blob/main/merlin32/bitmap256/file256.s

