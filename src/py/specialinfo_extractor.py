import re
import os
import json
import xlwt

from src.py.settings import cove_folder, output_folder, truncated_cove_folder, truncated_dd_folder
from src.py.utils import roman_num, num_roman, find_txt_files
from src.py.utils import split_sen, split_para, find_txt_files


class InfoTools:

    def __init__(self):

        # self.time_pat = r'\s(?:month|quarter|annual|end|day)\s'
        self.month_pat = r'month'
        self.quarter_pat = r'quarter'
        self.annual_pat = r'annual'
        self.time_pat = r'(?:end|day)'
        self.cont_pat = r'\s(?:report|financial statement)\s'

    def get_duedate_sens(self, para: str) -> dict:
        """
        return the sentence that contains the due date in this paragraph
        if None, that means it does not has due date info
        """

        due_date_sens = {'month': [], 'quarter': [], 'annual': [], 'others': []}

        sens = split_sen(para)
        for sen in sens:
            fin_word = re.search(self.cont_pat, sen)
            if fin_word:

                month = re.search(self.month_pat, sen)
                if month:
                    due_date_sens['month'].append((sen, month.group(), fin_word.group()))
                    continue

                quarter = re.search(self.quarter_pat, sen)
                if quarter:
                    due_date_sens['quarter'].append((sen, quarter.group(), fin_word.group()))
                    continue

                annual = re.search(self.annual_pat, sen)
                if annual:
                    due_date_sens['annual'].append((sen, annual.group(), fin_word.group()))
                    continue

                others = re.search(self.time_pat, sen)
                if others:
                    due_date_sens['others'].append((sen, others.group(), fin_word.group()))

        return due_date_sens

    def get_shorten_sen(self, key_word: str, sentence: str) -> str:
        sen_list = sentence.strip().split()
        key_position = 0
        try:
            key_position = sen_list.index(key_word)
        except:
            count = 0
            for word in sen_list:
                if key_word in word:
                    # key_position = sen_list.index(word)
                    key_position = count
                    break
                count += 1
        start = max(0, key_position-6)
        end = min(key_position+5, len(sen_list))
        return ' '.join(sen_list[start:end])

    def get_highlight_sen(self, key_words: list, sentence: str) -> str:

        list_sens = sentence.strip().split()
        for w in key_words:
            # sentence = re.subn(r'w', f'****{w}****', sentence)[0]
            key = w
            if w not in list_sens:
                for word in list_sens:
                    if w in word:
                        key = word
                        break
            sentence = sentence.replace(key, f'****{key}****', 100)
        return sentence

    def write_xls_sheet(self, sheet, row, **content: dict):
        """
        :param sheet: target sheet
        :param row: new row to be wrote
        :param content: dict to be write into sheet, which should contain
                        name, is_original, first_lines, shorten_sen, due_date_sen
        :return: sheet object, next row number
        """
        due_date_sens = content.pop('due_date_sen')
        for sen, time, fin in due_date_sens:

            # reclean first lines
            first_lines = re.subn(r'[-= ]{5,}', '', content['first_lines'])[0]
            sen = re.subn(r'[-= ]{5,}', '', sen)[0]

            shorten_sen = self.get_shorten_sen(time, sen)
            shorten_sen = self.get_highlight_sen([time], shorten_sen)
            sen = self.get_highlight_sen([time, fin], sen)

            sheet.write(row, 0, content['name'])
            sheet.write(row, 1, content['is_original'])
            sheet.write(row, 2, first_lines)
            sheet.write(row, 3, shorten_sen)
            sheet.write(row, 4, sen)

            row += 1
        return sheet, row


if __name__ == '__main__':

    # initial variables
    info_tool = InfoTools()
    date_book = xlwt.Workbook()
    headers = ['name', 'is_original', 'first_lines', 'shorten_sen', 'due_date_sen']
    sheet_names = ['month', 'quarter', 'annual', 'others']

    # init headers for each type of sheets
    xls_sheets = {}
    for type in sheet_names:
        xls_sheets[type] = date_book.add_sheet(type)
        for col, head in enumerate(headers):
            xls_sheets[type].write(0, col, head)
    row_iter = dict.fromkeys(sheet_names, 1)

    # file_names = find_txt_files(cove_folder)
    fail_list = []

    suc_counter = 0
    err_counter = 0
    date_dict = {}

    year_file_dic = {}
    for year in range(1996, 2007):
        year_folder = os.path.join(truncated_cove_folder, str(year))
        year_file_dic[year] = [file for file in os.listdir(year_folder) if file.endswith('.json')]

    for year, file_names in tuple(year_file_dic.items()):

        print(year)

        date_dict[year] = {'month': 0, 'quarter': 0, 'annual': 0, 'others': 0}

        year_folder = os.path.join(truncated_cove_folder, str(year))

        for name in file_names:

            with open(os.path.join(year_folder, name), 'r') as f:
                src_dic = json.load(f)      # keys: name, first_lines, is_original, covenant
            paras = split_para(src_dic['covenant'])

            # info_sens = []
            date_sens = {'month': [], 'quarter': [], 'annual': [], 'others': []}
            for para in paras.split('\n'):
                sens = info_tool.get_duedate_sens(para)  # get a list

                if sens:
                    if sens['month']:
                        date_sens['month'].extend(sens['month'])
                    elif sens['quarter']:
                        date_sens['quarter'].extend(sens['quarter'])
                    elif sens['annual']:
                        date_sens['annual'].extend(sens['annual'])
                    elif sens['others']:
                        date_sens['others'].extend(sens['others'])

            # if

            # write info into xls by each file iteration
            for date_type in sheet_names:
                if not date_sens[date_type]:
                    continue
                date_dict[year][date_type] += 1
                _, row_iter[date_type] = info_tool.write_xls_sheet(sheet=xls_sheets[date_type], row=row_iter[date_type],
                                                                   name=src_dic['name'], is_original=src_dic['is_original'],
                                                                   first_lines=src_dic['first_lines'],
                                                                   due_date_sen=date_sens.get(date_type))
                break

        # # date_book = xlwt.Workbook()
        # for key in date_dict.keys():
        #
        #     print(f'{year}: {key}, {len(date_dict[key])}')
        #
        #     file_extractions = date_dict[key]
        #     if not file_extractions:
        #         continue
        #
        #     sheet = date_book.add_sheet(key)
        #     row = 0
        #     for i in range(len(file_extractions)):
        #         for j in range(len(file_extractions[i][1])):
        #             sheet.write(row, 0, file_extractions[i][0])
        #             sheet.write(row, 1, file_extractions[i][1][j])
        #             row += 1
        date_book.save(os.path.join(truncated_dd_folder, f'due_date_{year}.xls'))

    print('due date finished!')
    print(date_dict)


