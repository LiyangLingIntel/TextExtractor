import re
import os
import nltk


def find_txt_files(root: str) -> list:

    file_list = [file for file in os.listdir(root) if file.endswith('.txt')]
    return file_list


def num_roman(num: int) -> str:

    num2roman = {0: ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"),
                 1: ("", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX")}

    roman = []
    roman.append(num2roman[1][num // 10 % 10])
    roman.append(num2roman[0][num % 10])

    return ''.join(roman)


def roman_num(roman: str) -> int:

    roman2num = {'I': 1, 'V': 5, 'X': 10, 'L': 50}

    num, p = 0, 'I'
    for c in roman[::-1]:
        num, p = num - roman2num[c] if roman2num[c] < roman2num[p] else num + roman2num[c], c

    return num


def split_para(text: str) -> str:
    """
    put sentences in the same paragraph to the same line
    :param text:
    :return:
    """
    paras = re.subn(r'([^;:.?!])\n', ' ', text)[0]
    paras = re.subn(r' +', ' ', paras)[0]
    return paras


def indent_para(text: str) -> str:
    pass


def split_sen(para: str) -> list:

    # Remove interference for sentence split from expression like No. 8
    dot_p = re.compile(r'(?<=No)\.\s+(?=\d)', re.IGNORECASE)
    para = dot_p.subn('-', para)[0]

    sens = nltk.sent_tokenize(para)

    return sens
