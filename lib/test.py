import bitarray
import os,base64
num_chunks = 12
seed = 387658945
LIB_PATH = os.path.dirname(__file__)
DOC_PATH = os.path.join(LIB_PATH, '../doc')
LENA_IMG = os.path.join(DOC_PATH, 'lena.png')

data = 'fuck you 你妈嗨'

num_chunks_bits = format(int(num_chunks), "016b")
seed_bits = format(int(seed), "032b")
print('发送的数据：', bitarray.bitarray(num_chunks_bits + seed_bits).tobytes() + bytes(data, encoding='gb18030', errors='ignore'))




# send_data = []
# send_data.append(bitarray.bitarray(num_chunks_bits + seed_bits).tobytes())
# send_data.append(bytes(data, encoding='gb18030', errors='ignore'))
# print('发送的数据：', send_data)

byte_factory = bitarray.bitarray(endian='big')
byte_factory.frombytes((bitarray.bitarray(num_chunks_bits + seed_bits).tobytes() + bytes(data, encoding='gb18030', errors='ignore'))[0:2])
num_chunks = int(byte_factory.to01(), base=2)

byte_factory1 = bitarray.bitarray(endian='big')
byte_factory1.frombytes((bitarray.bitarray(num_chunks_bits + seed_bits).tobytes() + bytes(data, encoding='gb18030', errors='ignore'))[2:6])
seed = int(byte_factory1.to01(), base=2)

data = (bitarray.bitarray(num_chunks_bits + seed_bits).tobytes() + bytes(data, encoding='gb18030', errors='ignore'))[6:]
byte_factory = bitarray.bitarray(endian='big')
byte_factory.frombytes(data)
#
# print('num_chunks:', num_chunks)
# print('seed:', seed)
# print('data:', data)
# # send_data = []
# send_data.append(bitarray.bitarray(num_chunks_bits + seed_bits).tobytes())
# send_data.append(bytes(self.data, encoding='gb18030', errors='ignore'))
# return send_data
num_chunks_bits = format(int(num_chunks), "016b")
seed_bits = format(int(seed), "032b")

a = bitarray.bitarray(num_chunks_bits + seed_bits).tobytes() + data
print(a)