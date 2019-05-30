# 2019-05-28
# Full Text Search

import os, re, xlwt
from py.extractor import InfoTools, ConvenantTools


if __name__ == '__main__':

    info_tool = InfoTools()
    covenant_processor = ConvenantTools()
    fail_list = []

    text_folder = './text/txt_result/'

    suc_counter = 0
    err_counter = 0
    date_dict = {}

    year_file_dic = {}
    years = [1996, 2017]
    # years = [2007, 2010]
    for year in range(*years):
        year_folder = os.path.join(text_folder, str(year))
        year_file_dic[year] = [file for file in os.listdir(year_folder) if file.endswith('.txt')]

    for year, file_names in tuple(year_file_dic.items()):

        # 初始化excel workbook，否则信息会累加到后面的文件中
        date_book = xlwt.Workbook()
        headers = ['name', 'is_original', 'is_debt', 'first_lines', 'shorten_sen', 'due_date_sen']
        sheet_name = 'month'

        # init headers for sheet
        xls_sheet = date_book.add_sheet(sheet_name)
        for col, head in enumerate(headers):
            xls_sheet.write(0, col, head)
        row_iter = 1

        date_dict[year] = {'month': 0}

        year_folder = os.path.join(text_folder, str(year))

        for name in file_names:

            is_debt = False
            # check first line to get origin and debt info about this contract
            with open(os.path.join(year_folder, name), 'r', encoding='utf-8') as f:
                lines = [line for line in f.readlines() if line.strip()]
                first_lines = covenant_processor.get_n_lines(5, lines)
                is_origin = True if covenant_processor.is_original(first_lines) else False
                is_debt = True if re.search(info_tool.debt_pat, covenant_processor.get_n_lines(10, lines)) else False
                content = '\n'.join(lines)
            del lines

            # cleaning
            content = re.subn(r'\-[0-9]{1,2}\-', '', content)[0]
            content = re.subn(r'[-=_ ]{5,}', '', content)[0]

            # date_sens = []
            # for para in paras:
            #     sens = info_tool.get_duedate_sens(para)  # get a list
            #
            #     if sens:
            #         date_sens.extend(sens['month'])
            sens = info_tool.global_search_by_fin_key(content, 150)
            full_shorten_sens = [('', '')]
            full_shorten_sens.extend(info_tool.global_filter_by_mounthly_key(sens))

            # write info into xls by each file iteration
            if len(full_shorten_sens) > 1:
                date_dict[year]['month'] += 1
            xls_sheet, row_iter = info_tool.write_xls_sheet(sheet=xls_sheet, row=row_iter,
                                                       name=name, is_original=is_origin, is_debt=is_debt,
                                                       first_lines=first_lines,
                                                       due_date_sen=full_shorten_sens)
        date_book.save(os.path.join('./output/fulltext', f'due_date_{year}.xls'))
        del date_book

        print(f'{year}: ', date_dict[year]['month'], ' / ', len(year_file_dic[year]))

    print('due date finished!')
    # print(date_dict[year]['month'], ' / ', len(year_file_dic[year]))