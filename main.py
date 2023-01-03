from mpmath import *


def getModel(plainText):
    model = dict()
    charsCount = dict()
    start = mpf(0)
    len_text = len(plainText)
    for ch in plainText:
        charsCount[ch] = charsCount.get(ch, 0) + 1

    mp.dps = len_text+1
    model.fromkeys(charsCount)
    for ch in charsCount.keys():
        width = mpf(charsCount[ch]/len_text)
        model[ch] = (start, width)
        start += charsCount[ch]/len_text
    return model

def encode(plain_text):
    model = getModel(plain_text)
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
    value = tobinary("".join(result))
    while(value < low):
        result.append('1')
        value = tobinary("".join(result))
        if (value > high):
            result[k] = '0'
        value = tobinary("".join(result))
        k += 1
    return (result, value)

def tobinary(value):
    result = 0
    power = 1
    fraction = value.split('.')[1]
    for i in fraction:
        result += ((2 ** (-power)) * int(i))
        power += 1
    return result

if __name__ == '__main__':
    plain = "abcabcbabcbaca"
    model = getModel(plain)
    print(model)
    enc, value = encode(plain)
    print(enc)
    print(value)