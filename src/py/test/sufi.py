# 2019-06-22
# Full Text Search on sufi contracts

import os, re, xlwt
from py.extractor import InfoTools, ConvenantTools


if __name__ == '__main__':

    info_tool = InfoTools()
    covenant_processor = ConvenantTools()
    fail_list = []

    text_folder = './text/publiccontracts/'

    suc_counter = 0
    err_counter = 0
    date_dict = {}
    year_file_dic = {'sufi': []}
    year_file_dic['sufi'] = [file for file in os.listdir(text_folder) if file.endswith('.txt')]

    types = ['basic', 'duedate', 'proj']
    headers = {}
    headers['basic'] = ['name', 'is_original', 'is_debt', 'first_lines']
    headers['duedate'] = ['name', 'shorten_sen', 'is_new', 'due_date_sen']
    headers['proj'] = ['name', 'shorten_sen', 'is_new', 'projection_sen']
    books = {}
    sheets = {}
    row_counter = {}

    for year, file_names in tuple(year_file_dic.items()):

        # 初始化excel workbook，否则信息会累加到后面的文件中
        for t in types:
            books[t] = xlwt.Workbook()
            sheets[t], row_counter[t] = info_tool.write_xls_header(headers[t], books[t])

        date_dict[year] = {'duedate': 0, 'proj': 0}

        year_folder = text_folder

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

            fin_sens = info_tool.global_search_by_fin_key(content, 150)
            proj_sens = info_tool.global_search_by_proj_key(content, 150)

            fin_full_shorten_sens = info_tool.global_filter_by_key(fin_sens, pattern='month_pat')
            proj_full_shorten_sens = info_tool.global_filter_by_key(proj_sens, pattern='date_pat')

            # write info into xls by each file iteration

            sheets['basic'], row_counter['basic'] = info_tool.write_xls_sheet(sheet=sheets['basic'],
                                                                              row=row_counter['basic'],
                                                                              headers=headers['basic'],
                                                                              name=name,
                                                                              is_original=is_origin,
                                                                              is_debt=is_debt,
                                                                              first_lines=first_lines)
            if fin_full_shorten_sens:
                date_dict[year]['duedate'] += 1
                sheets['duedate'], row_counter['duedate'] = info_tool.write_xls_sheet(sheet=sheets['duedate'],
                                                                                      row=row_counter['duedate'],
                                                                                      headers=headers['duedate'],
                                                                                      name=name,
                                                                                      matched_sens=fin_full_shorten_sens)
            if proj_full_shorten_sens:
                date_dict[year]['proj'] += 1
                sheets['proj'], row_counter['proj'] = info_tool.write_xls_sheet(sheet=sheets['proj'],
                                                                                row=row_counter['proj'],
                                                                                headers=headers['proj'],
                                                                                name=name,
                                                                                matched_sens=proj_full_shorten_sens)

        for t in types:
            books[t].save(os.path.join('./output/fulltext', f'{t}_{year}.xls'))
            del books[t]

        print(f'{year}: ')
        print('monthly\t', date_dict[year]['duedate'], ' / ', len(year_file_dic[year]))
        print('project\t', date_dict[year]['proj'], ' / ', len(year_file_dic[year]))

    print('finished!')