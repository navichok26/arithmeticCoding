from mpmath import *


def getModel(plainText):
    model = dict()
    charsCount = dict()
    count = 0
    start = mpf(0)
    for ch in plainText:
        count += 1
        charsCount[ch] = charsCount.get(ch, 0) + 1

    mp.dps = count+1
    model.fromkeys(charsCount)
    for ch in charsCount.keys():
        width = mpf(charsCount[ch]/count)
        model[ch] = (start, width)
        start += charsCount[ch]/count
    return model

if __name__ == '__main__':
    plain = "abcabcbabcbaca"
    model = getModel(plain)
    print(model)