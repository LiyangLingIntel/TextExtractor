import os
import re
import json

from py.settings import resource_folder, cove_folder, toc_folder, text_folder, truncated_cove_folder
from py.utils import roman_num, num_roman
from timeout_decorator import timeout

import sys
import importlib as imp
imp.reload(sys)
# sys.setdefaultencoding('utf8')


class ConvenantTools:

    def __init__(self):

        self.toc_pat = re.compile(r"""
            (?:\s*
                (?:ARTICLE|SECTION|Section)\s+
                (?:\d{1,2}|[IVX]{1,4}\.?)\s*
                (?:[A-Za-z0-9;.,&# \-]*)\n
                (?:(?:SECTION|Section)?\s*\d{1,2}(?:[.0-9]{1,2})+\.?\s+[A-Za-z0-9;,.'/&# \-]+[. ]{0,2}\n
                (?:SECTION|Section)?\s*\d{1,2}(?:[.0-9]{1,2})+\.?[A-Za-z0-9;,.'/ \-]+[. ]{0,2}\n
                )*
            )
            """, re.VERBOSE)

        self.toc_line_pat = re.compile(r"""
            (?:ARTICLE|SECTION|Section)\s+(?:\d{1,2}|[IVX]{1,4}\.?)\s*(?:[A-Za-z0-9;.,&# \-]*)\n
            |(?:SECTION|Section)?\s*\d{1,2}(?:[.0-9]{1,2}){0,2}[A-Za-z0-9;,'/&# \n\-]+[. ]+\d{1,2}\n
            """, re.VERBOSE)

        self.title_pat = re.compile(r"^\s*(ARTICLE|SECTION|Section)\s+(\d{1,2}|[IVX]{1,4})")

        overlook_keys = ['AMENDED', 'AMENDMENT', 'RESTATED', 'revis',
                         'amend', 'modif', 'restate', 'supplement', 'addendum']
        self.amend_pat = re.compile('|'.join(overlook_keys), re.IGNORECASE)

    @timeout(5)
    def toc_extractor(self, text: str) -> str:

        toc = re.findall(self.toc_line_pat, text)
        return ''.join(toc)

    @timeout(10)
    def covenant_title_finder(self, toc: str) -> list:

        title_list = []
        last_num = 0

        for toc_section in re.finditer(self.toc_pat, toc):
            toc_section = toc_section.group(0)
            title_matched = re.search(self.title_pat, toc_section)    # definitely successful, cos of the similar regex with toc_section

            # toc extracted is not clean, below is to garantee only match content part
            title_num = title_matched.group(2)
            current_num = roman_num(title_num ) if title_num.isalpha() else int(title_num)

            if last_num > current_num:
                break
            else:
                last_num = current_num

            if not re.compile('covenant', re.IGNORECASE).search(toc_section):
                continue
                    
            title_list.append((title_matched.group(1), title_matched.group(2)))

        if title_list:
            main_title = title_list[0][0]
            title_list = [t for t in title_list if t[0] == main_title]

        return title_list

    # extract covenant section according to its main section title
    @timeout(10)
    def section_extractor(self, title_list: list, text: str) -> str:

        if not isinstance(title_list, list):
            title_list = [title_list]

        covenant_sections = []

        for title in title_list:
            title_number = title[1]
            if title_number.isalpha():
                next_number = roman_num(title_number) + 1
                next_number = num_roman(next_number)
            else:
                next_number = str(int(title_number) + 1)

            sec_pattern = re.compile(rf"\s+{title[0]}\s+{title[1]}.*?(?={title[0]}\s+{next_number})", re.DOTALL)
            covenant_section = sec_pattern.findall(text)
            covenant_sections.extend(list(set(covenant_section)))

        return '\n'.join(covenant_sections)

    def section_cleaner(self):
        """
        remove page number
        remove redundant toc part
        """
        pass

    def get_n_lines(self, n: int, lines: list) -> str:
        # get first n lines of text
        res = []
        for line in lines:
            if len(res) >= n:
                break
            line = re.subn(r'[-= ]{5,}', '', line.strip())[0]
            if not line:
                continue
            res.append(line)
        return ' '.join(res)

    def is_original(self, key_text):

        return False if re.search(self.amend_pat, key_text) else True

