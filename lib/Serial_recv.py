# _*_ coding=utf-8 _*_
from __future__ import print_function


import sys, os
import numpy as np
from math import ceil
from math import floor

import pywt
import bitarray
import matlab.engine
from PIL import Image
import time, serial
import logging

sys.path.append('.')
from dwt_lib import load_img
from fountain_lib import Fountain, Glass
from fountain_lib import EW_Fountain, EW_Droplet
from spiht_dwt_lib import spiht_encode, func_DWT, code_to_file, spiht_decode, func_IDWT

LIB_PATH = os.path.dirname(__file__)
DOC_PATH = os.path.join(LIB_PATH, '../doc')
LENA_IMG = os.path.join(DOC_PATH, 'lena.png')
TEST_PATH = os.path.join(DOC_PATH, 'test')
SIM_PATH = os.path.join(LIB_PATH, '../simulation')
WHALE_IMG = os.path.join(DOC_PATH, 'whale.bmp')


BIOR = 'bior4.4'           # 小波基
MODE = 'periodization'
LEVEL = 3


def bitarray2str(bit):
    return bit.tobytes().decode('utf-8')


def recv_check(recv_data):
    data_array = bytearray(recv_data)
    sum = int(0)
    zero = bytes(0)
    odd_flag = False

    if not len(data_array) % 2 == 0:
        odd_flag = True
        data_array.insert(len(data_array), 0)

    for i in range(0, len(data_array), 2):
        val = int.from_bytes(data_array[i:i + 2], 'big')
        sum = sum + val
        sum = sum & 0xffffffff

    sum = (sum >> 16) + (sum & 0xffff)
    while sum > 65535:
        sum = (sum >> 16) + (sum & 0xffff)
    print('checksum:', sum)

    if sum == 65535:
        if odd_flag:
            data_array.pop()
            data_array.pop(0)
            data_array.pop(0)
        else:
            data_array.pop(0)
            data_array.pop(0)
        return bytes(data_array)
    else:
        print('Receive check wrong!')

class Sender:
    def __init__(self, port,
                 baudrate,
                 timeout,
                 img_path=LENA_IMG,
                 level=3,
                 wavelet='bior4.4',
                 mode='periodization',

                 fountain_chunk_size=7500,
                 fountain_type='normal',
                 drop_interval=5,

                 w1_size=0.1,
                 w1_pro=0.084,
                 seed=None):

        self.port = serial.Serial(port, baudrate)
        self.drop_id = 0
        self.eng = matlab.engine.start_matlab()
        self.eng.addpath(LIB_PATH)
        self.img_path = img_path
        self.fountain_chunk_size = fountain_chunk_size
        self.fountain_type = fountain_type
        self.drop_interval = drop_interval
        self.w1_p = w1_size
        self.w1_pro = w1_pro
        # self.port = port
        self.seed = seed

        # if self.port.is_open:
        #     print("串口{}打开成功".format(self.port.portstr))
        # else:
        #     print("串口打开失败")

        temp_file = self.img_path  # .replace(self.img_path.split('/')[-1], 'tmp')
        rgb_list = ['r', 'g', 'b']
        temp_file_list = [temp_file + '_' + ii for ii in rgb_list]
        if self.is_need_img_process():
            print('processing image: {:s}'.format(self.img_path))
            img = load_img(self.img_path)
            (width, height) = img.size
            mat_r = np.empty((width, height))
            mat_g = np.empty((width, height))
            mat_b = np.empty((width, height))
            for i in range(width):
                for j in range(height):
                    [r, g, b] = img.getpixel((i, j))
                    mat_r[i, j] = r
                    mat_g[i, j] = g
                    mat_b[i, j] = b
            self.img_mat = [mat_r, mat_g, mat_b]
            self.dwt_coeff = [func_DWT(ii) for ii in self.img_mat]                         # r,g,b小波变换得到系数
            self.spiht_bits = [spiht_encode(ii, self.eng) for ii in self.dwt_coeff]        # r,g,b的spiht编码

            a = [code_to_file(self.spiht_bits[ii],
                              temp_file_list[ii],
                              add_to=self.fountain_chunk_size / 3 * 8)
                 for ii in range(len(rgb_list))]
        else:
            print('temp file found : {:s}'.format(self.img_path))

        self.m, _chunk_size = self.compose_rgb(temp_file_list, each_chunk_size=int(self.fountain_chunk_size / 3))

        self.fountain = self.fountain_builder()

        #  a = [os.remove(ii) for ii in temp_file_list]
        self.show_info()
        # self.a_drop()


    def is_need_img_process(self):                       # 判断有没有rgb文件
        #  print(sys._getframe().f_code.co_name)

        doc_list = os.listdir(os.path.dirname(self.img_path))
        img_name = self.img_path.split('/')[-1]
        suffix = ['_' + ii for ii in list('rbg')]
        target = [img_name + ii for ii in suffix]
        count = 0
        for t in target:
            if t in doc_list:
                count += 1
        if count == 3:
            return False
        else:
            return True


    def compose_rgb(self, file_list, each_chunk_size=2500):
        '''
        将三个文件和并为一个文件
        '''

        m_list = []
        m_list.append(open(file_list[0], encoding='gb18030', errors='ignore').read())
        m_list.append(open(file_list[1], encoding='gb18030', errors='ignore').read())
        m_list.append(open(file_list[2], encoding='gb18030', errors='ignore').read())

        #  a = [print(len(ii)) for ii in m_list]
        m = ''
        for i in range(int(ceil(len(m_list[0]) / float(each_chunk_size)))):
            start = i * each_chunk_size
            end = min((i + 1) * each_chunk_size, len(m_list[0]))
            #  m += ''.join([ii[start:end] for ii in m_list])
            m += m_list[0][start: end]
            m += m_list[1][start: end]
            m += m_list[2][start: end]
        print('compose_rgb len(m):', len(m))                                       # r,g,b(size)+...+
        return m, each_chunk_size * 3

    def fountain_builder(self):
        if self.fountain_type == 'normal':
            return Fountain(self.m, chunk_size=self.fountain_chunk_size, seed=self.seed)
        elif self.fountain_type == 'ew':
            return EW_Fountain(self.m,
                               chunk_size=self.fountain_chunk_size,
                               w1_size=self.w1_p,
                               w1_pro=self.w1_pro,
                               seed=self.seed)

    def show_info(self):
        self.fountain.show_info()

    def a_drop(self):
        return self.fountain.droplet().toBytes()

    def send_drops_use_serial(self):
        #     send_data = a_drop.encode('utf-8')
        #     self.port.write(send_data)
        packet_discard_rate = 0.1
        discard_one = int(1 / packet_discard_rate)
        while True:
            time.sleep(self.drop_interval)
            self.drop_id += 1
            if self.drop_id % discard_one == 0:
                print("Discard one")
                self.a_drop()
            else:
                print('drop id : ', self.drop_id)
                self.port.write(self.a_drop())                         # write 须为str


class EW_Sender(Sender):
    def __init__(self, img_path, fountain_chunk_size, seed=None):
        Sender.__init__(self, img_path, fountain_chunk_size=fountain_chunk_size, fountain_type='ew', seed=seed)


class Receiver:
    def __init__(self, port,
                 baudrate,
                 timeout,
                 ):

        self.port = serial.Serial(port, baudrate)
        # if (self.port.is_open):
        #     print("串口{}打开成功".format(self.port.portstr))
        # else:
        #     print("串口打开失败")

        self.eng = matlab.engine.start_matlab()
        self.eng.addpath(LIB_PATH)

        self.drop_id = 0
        self.glass = Glass(0)
        self.chunk_size = 0
        self.current_recv_bits_len = 0
        self.i_spiht = []
        self.i_dwt = [[], [], []]
        self.img_mat = []
        #  暂时
        self.idwt_coeff_r = None
        self.r_mat = None
        self.img_shape = [0, 0]
        self.recv_img = None
        self.drop_byte_size = 99999
        self.test_dir = os.path.join(TEST_PATH, time.asctime().replace(' ', '_').replace(':', '_'))
        self.w1_done = True

        # os.mkdir(self.test_dir)


        # while True:
        #     self.begin_to_catch()
        #     if self.glass.isDone():
        #
        #         print('recv done')
        #         break

    def begin_to_catch(self):
        a_drop_bytes = self.catch_a_drop_use_serial()          # bytes

        if a_drop_bytes is not None:
            check_data = recv_check(a_drop_bytes)

        # if check_data is None:
        #     self.begin_to_catch()
        # else:
            if not check_data == None:
                self.drop_id += 1
                print("recv drops id : ", self.drop_id)
                self.drop_byte_size = len(check_data)
                self.add_a_drop(check_data)                                           # bytes --- drop --- bits

    data_rec =''

    def catch_a_drop_use_serial(self):
        time.sleep(1)
        size1 = self.port.in_waiting
        if size1:
            self.data_rec = self.port.read_all()
            frame_len = len(self.data_rec)
            if self.data_rec[0:2] == b'ok' and self.data_rec[frame_len - 4:frame_len] == b'fuck':
                data_array = bytearray(self.data_rec)
                data_array.pop(0)
                data_array.pop(0)
                data_array.pop()
                data_array.pop()
                data_array.pop()
                data_array.pop()
                a = len(bytes(data_array))
                print('drop len(crc) :', a)

                return bytes(data_array)
            else:
                print('Wrong receive frame !')
        else:
            self.port.flushInput()


    def add_a_drop(self, d_byte):
        drop = self.glass.droplet_from_Bytes(d_byte)           # drop

        print('drop data len: ', len(drop.data))

        if self.glass.num_chunks == 0:
            print('init num_chunks : ', drop.num_chunks)
            self.glass = Glass(drop.num_chunks)                 # 初始化接收glass
            self.chunk_size = len(drop.data)

        self.glass.addDroplet(drop)                             # glass add drops

        logging.info('current chunks')
        logging.info([ii if ii == None else '++++' for ii in self.glass.chunks])

        if self.glass.isDone():
            self.recv_bit = self.glass.get_bits()                   # bits

            # a = self.recv_bit.length()
            print('recv bits length : ', int(self.recv_bit.length()))

            if (int(self.recv_bit.length()) > 0) and \
                    (self.recv_bit.length() > self.current_recv_bits_len):
                self.current_recv_bits_len = int(self.recv_bit.length())
                #  self.recv_bit.tofile(open('./recv_tmp.txt', 'w'))
                self.i_spiht = self._123(self.recv_bit)
                #  self.i_dwt = [spiht_decode(ii, self.eng) for ii in self.i_spiht]
                try:
                    self.i_dwt[0] = spiht_decode(self.i_spiht[0], self.eng)
                    self.i_dwt[1] = spiht_decode(self.i_spiht[1], self.eng)
                    self.i_dwt[2] = spiht_decode(self.i_spiht[2], self.eng)
                    self.img_mat = [func_IDWT(ii) for ii in self.i_dwt]

                    #  单通道处理
                    #  self.idwt_coeff_r = spiht_decode(self.recv_bit, self.eng)
                    #  self.r_mat =func_IDWT(self.idwt_coeff_r)
                    self.img_shape = self.img_mat[0].shape
                    self.show_recv_img()
                except:
                    print('Decode error in matlab')

    def show_recv_img(self):
        if self.recv_img == None:
            self.recv_img = Image.new('RGB', (self.img_shape[0], self.img_shape[0]), (0, 0, 20))
        for i in range(self.img_shape[0]):
            for j in range(self.img_shape[0]):
                R = self.img_mat[0][i, j]
                G = self.img_mat[1][i, j]
                B = self.img_mat[2][i, j]

                #  单通道处理
                #  G = self.r_mat[i, j]
                #  G = 255
                #  B = 255
                new_value = (int(R), int(G), int(B))
                self.recv_img.putpixel((i, j), new_value)
        self.recv_img.show()
        self.recv_img.save(os.path.join(self.test_dir, str(self.drop_id)) + ".bmp")

    def _123(self, bits):                          # 将rgb拆成r,g,b
        self.recv_bit_len = int(bits.length())
        i_spiht_list = []
        #  if bits % 3 == 0:
        #  print('')
        # chunk_size = self.chunk_size
        rgb_chunk_bit_size = 12000
        print('self.glass.chunk_bit_size : ', self.glass.chunk_bit_size)
        #  bits.tofile(open(str(self.drop_id), 'w'))
        each_chunk_size = int(rgb_chunk_bit_size / 3)
        r_bits = bitarray.bitarray('')
        g_bits = bitarray.bitarray('')
        b_bits = bitarray.bitarray('')
        print('recv_bit len : ', bits.length())

        for i in range(int(ceil(int(bits.length()) / float(rgb_chunk_bit_size)))):
            start = i * rgb_chunk_bit_size
            end = min((i + 1) * rgb_chunk_bit_size, int(bits.length()))
            tap_chunk = bits[start: end]
            r_bits += tap_chunk[each_chunk_size * 0: each_chunk_size * 1]
            g_bits += tap_chunk[each_chunk_size * 1: each_chunk_size * 2]
            b_bits += tap_chunk[each_chunk_size * 2:]
        rgb = list('rgb')
        #  r_bits.tofile(open("r_"+str(self.drop_id), 'w'))
        rgb_bits = [r_bits, g_bits, b_bits]
        return rgb_bits

    def w1_123(self, w1_bits):  # 将rgb拆成r,g,b
        self.recv_bit_len = int(w1_bits.length())
        i_spiht_list = []
        #  if bits % 3 == 0:
        #  print('')
        # chunk_size = self.chunk_size
        rgb_chunk_bit_size = 12000
        print('self.glass.chunk_bit_size : ', self.glass.chunk_bit_size)

        each_chunk_bit_size = int(rgb_chunk_bit_size / 3)
        r_bits = bitarray.bitarray('')
        g_bits = bitarray.bitarray('')
        b_bits = bitarray.bitarray('')
        print('w1_bit len : ', w1_bits.length())

        num_rgb_chunks = int(ceil(int(w1_bits.length()) / float(rgb_chunk_bit_size)))
        rgb_bits_left = int(w1_bits.length() % rgb_chunk_bit_size)

        for i in range(num_rgb_chunks):
            start = i * rgb_chunk_bit_size
            end = min((i + 1) * rgb_chunk_bit_size, int(w1_bits.length()))
            tap_chunk = w1_bits[start: end]

            if i == num_rgb_chunks - 1 and rgb_bits_left < each_chunk_bit_size:
                r_bits += tap_chunk[each_chunk_bit_size * 0:]
                break

            elif i == num_rgb_chunks - 1 and each_chunk_bit_size < rgb_bits_left < each_chunk_bit_size * 2:
                r_bits += tap_chunk[each_chunk_bit_size * 0: each_chunk_bit_size * 1]
                g_bits += tap_chunk[each_chunk_bit_size * 1:]
                break
            elif i == num_rgb_chunks - 1 and each_chunk_bit_size * 2 < rgb_bits_left < each_chunk_bit_size * 3:
                r_bits += tap_chunk[each_chunk_bit_size * 0: each_chunk_bit_size * 1]
                g_bits += tap_chunk[each_chunk_bit_size * 1: each_chunk_bit_size * 2]
                b_bits += tap_chunk[each_chunk_bit_size * 2:]

            r_bits += tap_chunk[each_chunk_bit_size * 0: each_chunk_bit_size * 1]
            g_bits += tap_chunk[each_chunk_bit_size * 1: each_chunk_bit_size * 2]
            b_bits += tap_chunk[each_chunk_bit_size * 2:]

        rgb = list('rgb')
        #  r_bits.tofile(open("r_"+str(self.drop_id), 'w'))
        rgb_bits = [r_bits, g_bits, b_bits]
        return rgb_bits

        # self.recv_bit_len = int(bits.length())
        # i_spiht_list = []
        # #  if bits % 3 == 0:
        # #  print('')
        # # chunk_size = self.chunk_size
        # bit_chunk_size = self.glass.chunk_bit_size
        #
        # print('self.glass.chunk_bit_size : ', self.glass.chunk_bit_size)
        # #  bits.tofile(open(str(self.drop_id), 'w'))
        # each_chunk_size = int(ceil(bit_chunk_size / 3))                         ###
        # # each_chunk_size = 2500                                              ###################
        # r_bits = bitarray.bitarray('')
        # g_bits = bitarray.bitarray('')
        # b_bits = bitarray.bitarray('')
        # print('recv_bit len : ', bits.length())
        #
        # for i in range(int(ceil(int(bits.length()) / float(bit_chunk_size)))):
        #     start = i * bit_chunk_size
        #     end = min((i + 1) * bit_chunk_size, int(bits.length()))                           ###*8
        #     tap_chunk = bits[start: end]
        #     r_bits += tap_chunk[each_chunk_size * 0: each_chunk_size * 1]
        #     g_bits += tap_chunk[each_chunk_size * 1: each_chunk_size * 2]
        #     b_bits += tap_chunk[each_chunk_size * 2:]
        # rgb = list('rgb')
        # #  r_bits.tofile(open("r_"+str(self.drop_id), 'w'))
        # rgb_bits = [r_bits, g_bits, b_bits]
        # return rgb_bits


class EW_Receiver(Receiver):
    def __init__(self, port, baudrate, timeout, recv_img=None):
        Receiver.__init__(self, port=port, baudrate=baudrate, timeout=timeout)

    def add_a_drop(self, d_byte):
        a_drop = self.glass.droplet_from_Bytes(d_byte)
        print("seed: {}\tnum_chunk : {}\tdata len: {}".format(a_drop.seed, a_drop.num_chunks, len(a_drop.data)))
        ew_drop = EW_Droplet(a_drop.data, a_drop.seed, a_drop.num_chunks)

        if self.glass.num_chunks == 0:
            print('init num_chunks : ', a_drop.num_chunks)
            self.glass = Glass(a_drop.num_chunks)
            self.chunk_size = len(a_drop.data)

        self.glass.addDroplet(ew_drop)

        logging.info('current chunks')
        logging.info([ii if ii == None else '++++' for ii in self.glass.chunks])

        # 解码w1信息
        w1_size = 0.1
        if self.glass.is_w1_done(w1_size) and self.w1_done:
            print('w1_data complete!')
            w1_bits = self.glass.get_w1_bits(int(round(self.glass.num_chunks * w1_size)))
            self.w1_done = False
            if (int(w1_bits.length()) > 0) and \
                    (w1_bits.length() > self.current_recv_bits_len):
                self.current_recv_bits_len = w1_bits.length()
                self.i_spiht = self.w1_123(w1_bits)

                try:
                    self.i_dwt[0] = spiht_decode(self.i_spiht[0], self.eng)
                    self.i_dwt[1] = spiht_decode(self.i_spiht[1], self.eng)
                    self.i_dwt[2] = spiht_decode(self.i_spiht[2], self.eng)
                    self.img_mat = [func_IDWT(ii) for ii in self.i_dwt]

                    #  单通道处理
                    #  self.idwt_coeff_r = spiht_decode(self.recv_bit, self.eng)
                    #  self.r_mat =func_IDWT(self.idwt_coeff_r)
                    self.img_shape = self.img_mat[0].shape
                    self.show_recv_img()
                except:
                    print('decode error in matlab')

        # 解码全部信息
        if self.glass.isDone():                                                       # 喷泉码接收译码完成
            self.recv_bit = self.glass.get_bits()
            #  print('recv bits length : ', int(self.recv_bit.length()))
            if (int(self.recv_bit.length()) > 0) and \
                    (self.recv_bit.length() > self.current_recv_bits_len):
                self.current_recv_bits_len = self.recv_bit.length()
                self.i_spiht = self._123(self.recv_bit)
                try:
                    self.i_dwt[0] = spiht_decode(self.i_spiht[0], self.eng)
                    self.i_dwt[1] = spiht_decode(self.i_spiht[1], self.eng)
                    self.i_dwt[2] = spiht_decode(self.i_spiht[2], self.eng)
                    self.img_mat = [func_IDWT(ii) for ii in self.i_dwt]

                    #  单通道处理
                    #  self.idwt_coeff_r = spiht_decode(self.recv_bit, self.eng)
                    #  self.r_mat =func_IDWT(self.idwt_coeff_r)
                    self.img_shape = self.img_mat[0].shape
                    self.show_recv_img()
                except:
                    print('decode error in matlab')


if __name__ == "__main__":
    # receiver = Receiver('COM7', baudrate=921600, timeout=1)
    receiver = EW_Receiver('COM7', baudrate=921600, timeout=1)
    os.mkdir(receiver.test_dir)
    while True:
        receiver.begin_to_catch()
        if receiver.glass.isDone():
            print('recv done')
            # receiver.show_recv_img()
            break
