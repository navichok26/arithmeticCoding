import sys
import struct
from mpmath import *

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
        model[ch] = (start, width)
        start += chars_count[ch]/len_text
    return model

def encode(plain_text):
    model = getModel(getCharscount(plain_text), len(plain_text))
    len_text = len(plain_text)
    mp.dps = len_text * len_text
    high = mpf(1.0)
    low = mpf(0.0)
    for ch in plain_text:
        ch_start, ch_width = model[ch]
        ch_end = ch_start + ch_width
        delta = mpf(high - low)
        high = low + (ch_end * delta)
        low = low + (ch_start * delta)
    result = ['0', '.']
    k = 2
    value = floattobinary("".join(result))
    while(value < low):
        result.append('1')
        value = floattobinary("".join(result))
        if (value > high):
            result[k] = '0'
        value = floattobinary("".join(result))
        k += 1
    return result[2:]

def write_header(file, dict_chars, len_text):
    file.write(len_text.to_bytes(4, byteorder='little'))
    col_letters = (len(dict_chars.keys())-1).to_bytes(1, byteorder='little')
    file.write(col_letters)
    for letter, code in dict_chars.items():
        file.write(letter.to_bytes(1, byteorder='little'))
        file.write(code.to_bytes(4, byteorder='little'))

def write_delta(file, delta):
    pass

def write_text(file, enc):
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
    write_header(f, getCharscount(con), len(con))
    write_text(f, enc)

def decode(enc_num, model, len_text):
    string = []
    enc_num = mpf(enc_num)
    high = mpf(1.0)
    low = mpf(0.0)
    d_range = mpf(high - low)
    while (len(string) < len_text):
        for c, (c_low, c_width) in model.items():
            c_high = mpf(c_low + c_width)
            d_range = mpf(high - low)
            if c_low <= (enc_num - low)/d_range < c_high:
                high = mpf(low + (d_range * c_high))
                low = mpf(low + (d_range * c_low))
                string.append(c)
    string = string[:len_text]
    return ''.join(string)

def parse_header(input):
    len_text = int.from_bytes(input[0:4], byteorder='little')
    col_letters = input[4]+1
    header = input[5:5*col_letters + 5]
    dict_chars = dict()
    for i in range(col_letters):
        dict_chars[chr(header[i*5])] = int.from_bytes(header[i*5+1:i*5+5], byteorder='little')
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
    enc_num = floattobinary('0.' + enc)
    dec = decode(enc_num, model, len_text)
    f.write(rawbytes(dec))

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