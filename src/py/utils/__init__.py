from py.utils.utils import find_files_with_postfix, roman_num, num_roman
import re, nltk

def split_para(text: str) -> str:
    """
    put sentences in the same paragraph to the same line
    :param text:
    :return:
    """
    paras = re.subn(r'(?<=[^:.?!])\n', ' ', text)[0]
    paras = re.subn(r' +', ' ', paras)[0]
    return paras.split('\n')


def indent_para(text: str) -> str:
    pass


def split_sen(para: str) -> list:

    # Remove interference for sentence split from expression like No. 8
    dot_p = re.compile(r'(?<=No)\.\s+(?=\d)', re.IGNORECASE)
    para = dot_p.subn('-', para)[0]

    sens = nltk.sent_tokenize(para)

    return sens