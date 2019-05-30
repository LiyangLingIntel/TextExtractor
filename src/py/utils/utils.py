import re
import os
import nltk


def find_files_with_postfix(root: str, postfox: str = 'txt') -> list:

    file_list = [file for file in os.listdir(root) if file.endswith(f'.{postfox}')]
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

