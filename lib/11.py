from PyCRC.CRC16 import CRC16
import bitarray
import random

m = [123, 456, 345]
mm = ['12', '23', '34']
mmm = [b'123', b'0x\ff', b'hdf']

byte_factory2 = bitarray.bitarray(endian='big')
byte_factory2.frombytes(mmm[0])

# print(byte_factory2)
# print(byte_factory2 and byte_factory2)
#
# byte_factory2[0] = True
# print(byte_factory2)
#
# num = random.randint(0, 5)
# yet = 0
#
#
# for i in range(len(byte_factory2)):
#     if yet <= num:
#         seed = random.randint(0, 1)
#         if seed == 1:
#             byte_factory2[i] = bool(1 - byte_factory2[i])
#             yet += 1
#
# print(byte_factory2)


# random.sample 是一个均匀分布的采样
# return random.sample(range(num_chunks), size)


# print(byte_factory2[0])
# a = str(byte_factory2).replace('0', '1', 3)
#
# print(a)
# byte_factory3 = bitarray.bitarray(endian='big')
# byte_factory3.fromstring(a)
# print(type(byte_factory3))
# print(byte_factory3)


# test_bytes = b'yyou should consider upgrading via the command.'
# a = b''
# test_string = 'You should consider upgrading via the command.'
#
#
# crc = CRC16().calculate(test_bytes)
#
#
# def x_o_r(bytes1, bytes2):  # 传入两个数，并返回它们的异或结果，结果为16进制数
#     length = max(len(bytes1), len(bytes2))
#
#     if len(bytes1) < len(bytes2):
#         add_num = len(bytes2) - len(bytes1)
#         bytes1_array = bytearray(bytes1)
#         add = b'0'*add_num
#
#         for ii in range(add_num):
#             bytes1_array.insert(0, add[ii])
#             bytes1 = bytes(bytes1_array)
#
#     else:
#         add_num = len(bytes1) - len(bytes2)
#         bytes2_array = bytearray(bytes2)
#         add = b'0' * add_num
#
#         for ii in range(add_num):
#             bytes2_array.insert(0, add[ii])
#             bytes2 = bytes(bytes2_array)
#
#     result_bytes = b''
#     for i in range(length):
#         result_bytes += (bytes1[i] ^ bytes2[i]).to_bytes(1, 'little')
#
#     return result_bytes
#
# b1 = b'\xfe'
# b2 = b'\xfe\x05'
#
# # print(b1[0].to_bytes(1, 'little'))
# print(())
















#
# def send_check(send_bytes):
#     data_array = bytearray(send_bytes)
#     sum = int(0)
#     zero = bytes(0)
#
#     frame_start = b'ok'
#     frame_end = b'fuck'
#     odd_flag = False
#     if not len(data_array) % 2 == 0:
#         odd_flag = True
#         data_array.insert(len(data_array), 0)
#
#     for i in range(0, len(data_array), 2):
#         val = int.from_bytes(data_array[i:i + 2], 'little')
#         sum = sum + val
#         sum = sum & 0xffffffff
#
#     sum = (sum >> 16) + (sum & 0xffff)
#     while sum > 65535:
#         sum = (sum >> 16) + (sum & 0xffff)
#
#     get_reverse = 65535 - sum
#     check_sum = get_reverse.to_bytes(2, 'little')
#
#     data_array.insert(0, check_sum[0])
#     data_array.insert(1, check_sum[1])
#     data_array.insert(0, frame_start[0])
#     data_array.insert(1, frame_start[1])
#
#     if odd_flag:
#         data_array.pop()
#
#     data_array.insert(len(data_array), frame_end[0])
#     data_array.insert(len(data_array), frame_end[1])
#     data_array.insert(len(data_array), frame_end[2])
#     data_array.insert(len(data_array), frame_end[3])
#
#     data_array.pop()
#     data_array.pop()
#     data_array.pop()
#     data_array.pop()
#     # return data_array[len(data_array)-4:len(data_array)]
#     return bytes(data_array)
#
# chunk_bit_size = 7500
# # print('self.glass.chunk_bit_size : ', self.glass.chunk_bit_size)
# #  bits.tofile(open(str(self.drop_id), 'w'))
# each_chunk_size = int((chunk_bit_size / 3))
# print(chunk_bit_size)
# print(each_chunk_size)
#
# print(send_check(test_bytes))
#
#
# def recv_check(recv_data):
#     data_array = bytearray(recv_data)
#     sum = int(0)
#     zero = bytes(0)
#
#     odd_flag = False
#     if not len(data_array) % 2 == 0:
#         odd_flag = True
#         data_array.insert(len(data_array) - 1, 0)
#
#     for i in range(0, len(data_array), 2):
#         val = int.from_bytes(data_array[i:i + 2], 'little')
#         sum = sum + val
#         sum = sum & 0xffffffff
#
#     sum = (sum >> 16) + (sum & 0xffff)
#     while sum > 65535:
#         sum = (sum >> 16) + (sum & 0xffff)
#
#     print(sum)
#     if sum == 65535:
#         if odd_flag:
#             data_array.pop()
#             data_array.pop(0)
#             data_array.pop(0)
#         else:
#             data_array.pop(0)
#             data_array.pop(0)
#
#     return bytes(data_array)
#
#
# print(recv_check(send_check(test_bytes))[0:2])
print(mm[0])
print(mm[0][0])

print(type(mm[0][0]))