import bitarray
import os, numpy


LIB_PATH = os.path.dirname(__file__)
DOC_PATH = os.path.join(LIB_PATH, '../doc')
SIM_PATH = os.path.join(LIB_PATH, '../simulation')
PRO_PATH = os.path.join(SIM_PATH, 'processing')

RS_FILE = "timg.jpg.rs"
RE_CONTRUCT_IMAGE = "timg_recontruct.jpg"
PACKET_SIZE = 73

WHALE_128_JPG = os.path.join(DOC_PATH, "whale_128.jpg")
TWINS_256_JPG = os.path.join(DOC_PATH, "twins_256.jpg")
FISH_128_JGP = os.path.join( DOC_PATH, "undwer_128.jpg")

with open(r'F:\lab_code\img_dwt\doc\barbara.jpg', 'rb') as f:
    image_contain = f.read()

print(image_contain)

s = int(4)

bits_n = format(s, "016b")
print(bits_n)

byte_n = bitarray.bitarray(bits_n).tobytes()
print(byte_n)


print(s.to_bytes(2, 'big'))


print(int.from_bytes(s.to_bytes(2, 'big'), 'big'))


output_rs_file = WHALE_128_JPG + '.rs'
print(output_rs_file)

mat = [(1, 2, 3), (4, 5, 6), (7, 8, 9)]
mat_arr_code = numpy.array(mat)
print(mat_arr_code[2, 2])

