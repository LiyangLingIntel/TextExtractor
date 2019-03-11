import re
import os
from src.py.settings import cove_folder, output_folder, truncated_cove_folder, truncated_dd_folder
from src.py.utils import roman_num, num_roman, find_txt_files

from src.py.utils import split_sen, split_para, find_txt_files
import xlwt


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
            if re.search(self.cont_pat, sen):
                if re.search(self.month_pat, sen):
                    due_date_sens['month'].append(sen)
                elif re.search(self.quarter_pat, sen):
                    due_date_sens['quarter'].append(sen)
                elif re.search(self.annual_pat, sen):
                    due_date_sens['annual'].append(sen)
                elif re.search(self.time_pat, sen):
                    due_date_sens['others'].append(sen)
                else:
                    return None

        return due_date_sens
        

if __name__ == '__main__':

    info_tool = InfoTools()

    # file_names = find_txt_files(cove_folder)
    fail_list = []

    suc_counter = 0
    err_counter = 0

    year_file_dic = {}
    for year in range(1996, 2007):
        year_folder = os.path.join(truncated_cove_folder, str(year))
        year_file_dic[year] = [file for file in os.listdir(year_folder) if file.endswith('.txt')]

    for year, file_names in tuple(year_file_dic.items()):

        print(year)

        date_dict = {'month': [], 'quarter': [], 'annual': [], 'others': []}

        year_folder = os.path.join(truncated_cove_folder, str(year))

        for name in file_names:

            # print(name)

            with open(os.path.join(year_folder, name), 'r') as f:
                content = f.read()
            paras = split_para(content)

            info_sens = []
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

            if date_sens:
                if date_sens.get('month'):
                    date_dict['month'].append((name, date_sens['month']))
                elif date_sens.get('quarter'):
                    date_dict['quarter'].append((name, date_sens['quarter']))
                elif date_sens.get('annual'):
                    date_dict['annual'].append((name, date_sens['annual']))
                elif date_sens.get('others'):
                    date_dict['others'].append((name, date_sens['others']))

        date_book = xlwt.Workbook()
        for key in date_dict.keys():

            print(f'{year}: {key}, {len(date_dict[key])}')

            file_extractions = date_dict[key]
            if not file_extractions:
                continue

            sheet = date_book.add_sheet(key)
            row = 0
            for i in range(len(file_extractions)):
                for j in range(len(file_extractions[i][1])):
                    sheet.write(row, 0, file_extractions[i][0])
                    sheet.write(row, 1, file_extractions[i][1][j])
                    row += 1
        date_book.save(os.path.join(truncated_dd_folder, f'due_date_{year}.xls'))

    print('due date finished!')


