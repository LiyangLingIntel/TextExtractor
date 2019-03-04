import os
import re

from src.py.settings import resource_folder, cove_folder, toc_folder, text_folder
from timeout_decorator import timeout
from src.py.utils import find_txt_files, roman_num, num_roman


# pattern_line = r"\s*(?:ARTICLE|SECTION|Section)?\s+(?:\d{1,2}|[IVX]{1,4}\.?)\s*(?:[A-Za-z0-9;., \-]*)\n(?:\s*(?:SECTION|Section)?\s*\d{1,2}(?:[.0-9]{1,2})+\.?\s+[A-Za-z0-9;,.'/ \-]+[. ]{0,2}\n)*"
# mian_pat =
# sub_pat = ((?:SECTION|Section)?\s*\d{1,2}(?:[.0-9]{1,2})+\.?[A-Za-z0-9;,.'/ \-]+[. ]{0,2}\n)*


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

    @timeout(5)
    def toc_extractor(self, text: str) -> str:

        toc = re.findall(self.toc_line_pat, text)
        return ''.join(toc)

    @timeout(12)
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
    @timeout(15)
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


if __name__ == '__main__':

    """
    1. Traverse text folder and find all contract files
    2. Extract table of content from contract
    3. Find covenant section title
    4. Extract covenant section through corresponding main title
    """

    covenant_processor = ConvenantTools()
    # example = 'final-0000012355-02-000023.txt'

    for

    file_names = find_txt_files(text_folder)
    fail_list = []
    no_cove_files = []

    suc_counter = 0
    err_counter = 0

    for name in file_names:

        print(name)

        try:
            with open(os.path.join(text_folder, name), 'r') as f:
                text = f.read()
            toc_text = covenant_processor.toc_extractor(text)
            if not toc_text:
                raise Exception('toc extracting error')

            with open(os.path.join(toc_folder, name), 'w') as f:
                f.write(toc_text)
            cove_titles = covenant_processor.covenant_title_finder(toc_text)
            if not cove_titles:
                no_cove_files.append(name)
                continue

            cove_section = covenant_processor.section_extractor(cove_titles, text)
            if not cove_section:
                raise Exception('section extracting error')
            with open(os.path.join(cove_folder, name), 'w') as f:
                f.write(cove_section)

            suc_counter += 1

        except Exception as e:

            fail_list.append(name)
            err_counter += 1

    print(f'successful: {suc_counter}')
    print(f'fail: {err_counter}')

    print('finished!')