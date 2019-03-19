import os
import re
import json

from src.py.settings import resource_folder, cove_folder, toc_folder, text_folder, truncated_cove_folder
from src.py.utils import find_txt_files, roman_num, num_roman
# from settings import resource_folder, cove_folder, toc_folder, text_folder
# from utils import find_txt_files, roman_num, num_roman
from timeout_decorator import timeout

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

        overlook_keys = ['AMENDED', 'AMENDMENT', 'RESTATED', 'revis',
                         'amend', 'modif', 'restate', 'supplement', 'addendum']
        self.amend_pat = re.compile('|'.join(overlook_keys), re.IGNORECASE)

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

        if re.search(self.amend_pat, key_text):
            return False
        else:
            return True


if __name__ == '__main__':

    """
    1. Traverse text folder and find all contract files
    2. Extract table of content from contract
    3. Find covenant section title
    4. Extract covenant section through corresponding main title
    """

    covenant_processor = ConvenantTools()

    year_file_dic ={}
    for year in range(1996, 2007):
        year_folder = os.path.join(text_folder, str(year), 'result')
        year_file_dic[year] = [file for file in os.listdir(year_folder) if file.endswith('.txt')]

    origin_files = {}
    toc_problems = {}
    cove_problems = {}
    no_cove_files = {}
    suc_files = {}

    for year, file_paths in tuple(year_file_dic.items()):

        print(year)

        origin_files[year] = [len(file_paths), len(file_paths)]
        toc_problems[year] = 0
        no_cove_files[year] = 0
        cove_problems[year] = 0
        suc_files[year] = 0

        year_folder = os.path.join(text_folder, str(year), 'result')
        target_folder = os.path.join(truncated_cove_folder, str(year))
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        for file_name in file_paths:
            try:
                # define output dict
                op_dict = {}        # keys: name, first_lines, is_original, covenant
                op_dict['name'] = file_name.split('.')[0]

                # 1. read file content and extract valid table of content
                with open(os.path.join(year_folder, file_name), 'r') as f:

                    # filter amended contract
                    op_dict['first_lines'] = covenant_processor.get_n_lines(5, f.readlines())
                    op_dict['is_original'] = covenant_processor.is_original(op_dict['first_lines'])

                    f.seek(0)
                    text = f.read()
                    toc_text = covenant_processor.toc_extractor(text)

                if not toc_text:
                    toc_problems[year] += 1
                    raise Exception('toc extracting error')

                # with open(os.path.join(toc_folder, file_name), 'w') as f:
                #     f.write(toc_text)

                # 2. from toc extract title number of covenant section
                cove_titles = covenant_processor.covenant_title_finder(toc_text)
                if not cove_titles:
                    # no_cove_files.append(file_name)
                    no_cove_files[year] += 1
                    continue

                # 3. from contract file extract covenant section and save to local disk
                cove_section = covenant_processor.section_extractor(cove_titles, text)
                if not cove_section:
                    cove_problems[year] += 1
                    raise Exception('section extracting error')
                op_dict['covenant'] = cove_section

                with open(os.path.join(target_folder, f"{op_dict['name']}.json"), 'w') as f:
                    # f.write(cove_section)
                    json.dump(op_dict, f)

                suc_files[year] += 1

            except Exception as e:

                # fail_list.append(name)
                # err_counter += 1
                print(e)
                pass

    print(f'\norigin files: {origin_files}')
    print(f'\ntoc_problems: {toc_problems}')
    print(f'\nno cove files: {no_cove_files}')
    print(f'\nsuc files: {suc_files}')



    # file_names = find_txt_files(text_folder)
    # fail_list = []
    # no_cove_files = []

    # suc_counter = 0
    # err_counter = 0

    # for name in file_names:

    #     print(name)

    #     try:
    #         with open(os.path.join(text_folder, name), 'r') as f:
    #             text = f.read()
    #         toc_text = covenant_processor.toc_extractor(text)
    #         if not toc_text:
    #             raise Exception('toc extracting error')

    #         with open(os.path.join(toc_folder, name), 'w') as f:
    #             f.write(toc_text)
    #         cove_titles = covenant_processor.covenant_title_finder(toc_text)
    #         if not cove_titles:
    #             no_cove_files.append(name)
    #             continue

    #         cove_section = covenant_processor.section_extractor(cove_titles, text)
    #         if not cove_section:
    #             raise Exception('section extracting error')
    #         with open(os.path.join(cove_folder, name), 'w') as f:
    #             f.write(cove_section)

    #         suc_counter += 1

    #     except Exception as e:

    #         fail_list.append(name)
    #         err_counter += 1

    # print(f'successful: {suc_counter}')
    # print(f'fail: {err_counter}')

    # print('finished!')