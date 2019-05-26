

import os
import re
import nltk
from settings import resource_folder, cove_folder, output_folder


class ReportTools:

    def __init__(self):

        self.keywords = ['information covenant', 'information requirement', 'reporting covenant', 'reporting requirement',
                         'financial statement']

def reports_para():

    pass


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
