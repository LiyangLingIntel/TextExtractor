import re
import os
from src.py.settings import resource_folder, cove_folder, output_folder, toc_folder, date_folder, faildate_folder
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

    file_names = find_txt_files(cove_folder)
    fail_list = []

    suc_counter = 0
    err_counter = 0

    date_dict = {'month': [], 'quarter': [], 'annual': [], 'others': []}

    for name in file_names:

        print(name)

        with open(os.path.join(cove_folder, name), 'r') as f:
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

        print(f'{key}: {len(date_dict[key])}')

        file_extractions = date_dict[key]
        if not file_extractions:
            continue

        sheet = date_book.add_sheet(key)
        for i in range(len(file_extractions)):
            sheet.write(i, 0, file_extractions[i][0])
            for j in range(len(file_extractions[i][1])):
                sheet.write(i, j+1, file_extractions[i][1][j])

    date_book.save(os.path.join(output_folder, 'due_date_v2.xls'))

    print('due date finished!')


