#!/usr/
import sys
import struct
from mpmath import *
from bisect import bisect

def rawbytes(s):
    outlist = []
    for cp in s:
        num = ord(cp)
        if num < 256:
            outlist.append(struct.pack('B', num))
        elif num < 65535:
            outlist.append(struct.pack('>H', num))
        else:
            b = (num & 0xFF0000) >> 16
            H = num & 0xFFFF
            outlist.append(struct.pack('>bH', b, H))
    return b''.join(outlist)

def getCharscount(text):
    chars_count = dict()
    for ch in text:
        chars_count[ch] = chars_count.get(ch, 0) + 1
    return chars_count

def getModel(chars_count, len_text):
    model = dict()
    start = 0
    model.fromkeys(chars_count)
    for ch in chars_count.keys():
        width = chars_count[ch]/len_text
        model[ch] = width
        start += chars_count[ch]/len_text
    return model

def encode(plain_text):
    precision = 32
    one = int(2 ** precision - 1)
    quarter = int(ceil(one / 4))
    half = 2 * quarter
    threequarters = 3 * quarter

    chars_count = getCharscount(plain_text)
    model = getModel(chars_count, len(plain_text))

    f = [0.0]
    for a in model:
        f.append(f[-1] + model[a])
    f.pop()
    f = dict([(a, mf) for a, mf in zip(model, f)])

    res = []
    low, hight = 0, one
    straddle = 0

    for k in range(0, len(plain_text)):
        lohi_range = hight - low + 1

        low = low + ceil(lohi_range * f[plain_text[k]])
        hight = low + floor(lohi_range * model[plain_text[k]])

        while True:
            if hight < half:
                res.append(0)
                res.extend([1 for i in range(straddle)])
                straddle = 0
            elif low >= half:
                res.append(1)
                res.extend([0 for i in range(straddle)])
                straddle = 0
                low -= half
                hight -= half
            elif low >= quarter and hight < threequarters:
                straddle += 1
                low -= quarter
                hight -= quarter
            else:
                break
            low = 2 * low
            hight = 2 * hight + 1

    straddle += 1
    if low < quarter:
        res.append(0)
        res.extend([1 for i in range(straddle)])
    else:
        res.append(1)
        res.extend([0 for i in range(straddle)])

    return res

def write_header(file, dict_chars, len_text):
    file.write(len_text.to_bytes(4, byteorder='little'))
    col_letters = (len(dict_chars.keys())-1).to_bytes(1, byteorder='little')
    file.write(col_letters)
    for letter, code in dict_chars.items():
        file.write(letter.to_bytes(1, byteorder='little'))
        file.write(code.to_bytes(4, byteorder='little'))

def write_text(file, enc):
    enc = [str(i) for i in enc]
    enc = ''.join(enc)
    res = pad_encoded_text(enc)
    res = get_byte_array(res)
    file.write(bytes(res))

def enc_handler(inpath, outpath):
    f = open(inpath, 'rb')
    con = f.read()
    f.close()
    f = open(outpath, 'wb')
    enc = encode(con)
    print(enc)
    write_header(f, getCharscount(con), len(con))
    write_text(f, enc)

def decode(enc_num, model, len_text):
    precision = 32
    one = int(2 ** precision - 1)
    quarter = int(ceil(one / 4))
    half = 2 * quarter
    threequarters = 3 * quarter

    alphabet = list(model)
    f = [0]
    for a in model:
        f.append(f[-1] + model[a])
    f.pop()

    model = list(model.values())

    enc_num.extend(precision * [0]) 
    res = len_text * [0]  

    value = int(''.join(str(a) for a in enc_num[0:precision]), 2)
    y_position = precision  
    low, hight = 0, one

    res_position = 0
    while 1:
        lohi_range = hight - low + 1
        a = bisect(f, (value - low) / lohi_range) - 1
        res[res_position] = alphabet[a]

        low = low + int(ceil(f[a] * lohi_range))
        hight = low + int(floor(model[a] * lohi_range))

        while True:
            if hight < half:
                pass
            elif low >= half:
                low = low - half
                hight = hight - half
                value = value - half
            elif low >= quarter and hight < threequarters:
                low = low - quarter
                hight = hight - quarter
                value = value - quarter
            else:
                break
            low = 2 * low
            hight = 2 * hight + 1
            value = 2 * value + enc_num[y_position]
            y_position += 1
            if y_position == len(enc_num)+1:
                break

        res_position += 1
        if res_position == len_text or y_position == len(enc_num)+1:
            break
    return bytes(res)

def parse_header(input):
    len_text = int.from_bytes(input[0:4], byteorder='little')
    col_letters = input[4]+1
    header = input[5:5*col_letters + 5]
    dict_chars = dict()
    for i in range(col_letters):
        dict_chars[header[i*5]] = int.from_bytes(header[i*5+1:i*5+5], byteorder='little')
    return (dict_chars, len_text)

def parse_text(input):
    col_letters = input[4]+1
    enc_text_pad = input[5*col_letters + 5:]
    return enc_text_pad

def dec_handler(inpath, outpath):
    f = open(inpath, 'rb')
    con = f.read()
    f.close()
    f = open(outpath, 'wb')
    chars_count, len_text = parse_header(con)
    mp.dps = len_text * len_text
    model = getModel(chars_count, len_text)
    enc_text = parse_text(con)
    enc_pad = to_binary(enc_text)
    enc = remove_padding(enc_pad)
    enc = [int(i) for i in enc]
    dec = decode(enc, model, len_text)
    f.write(dec)
    f.close()

def floattobinary(value):
    result = mpf(0.0)
    power = mpf(1)
    fraction = value.split('.')[1]
    for i in fraction:
        result += mpf(mpf(2 ** (-power)) * mpf(int(i)))
        power += 1
    return result

def pad_encoded_text(encoded_text):
    extra_padding = 8 - len(encoded_text) % 8
    for _ in range(extra_padding):
        encoded_text += "0"
    padded_info = "{0:08b}".format(extra_padding)
    encoded_text = padded_info + encoded_text
    return encoded_text

def remove_padding(padded_encoded_text):
    padded_info = padded_encoded_text[:8]
    extra_padding = int(padded_info, 2)

    padded_encoded_text = padded_encoded_text[8:]
    encoded_text = padded_encoded_text[:-1*extra_padding]

    return encoded_text

def get_byte_array(padded_encoded_text):
    if (len(padded_encoded_text) % 8 != 0):
        print("Encoded text not padded")
        exit(0)
    b = bytearray()
    for i in range(0, len(padded_encoded_text), 8):
        byte = padded_encoded_text[i:i+8]
        b.append(int(byte, 2))
    return b

def to_binary(enc_text):
    result = ''
    for i in enc_text:
        bin_byte = bin(i)[2:].rjust(8, '0')
        result += bin_byte
    return result

def help():
    return "Using: python3 main.py [(c)ompress\\(d)ecompress] <input_file> <output_file>"

if __name__ == '__main__':
    if (len(sys.argv) != 4):
        print(help())
        exit(0)
    if (sys.argv[1] == 'c'):
        enc_handler(sys.argv[2], sys.argv[3])
    elif (sys.argv[1] == 'd'):
        dec_handler(sys.argv[2], sys.argv[3])
    else:
        print(help())