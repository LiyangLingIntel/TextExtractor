import re
import os
import json
import xlwt
import sys

from py.settings import cove_folder, output_folder, truncated_cove_folder, truncated_dd_folder, text_folder
from py.utils import roman_num, num_roman
from py.utils import split_sen, split_para, find_files_with_postfix
from py.extractor import ConvenantTools


class InfoTools:

    def __init__(self):

        # self.time_pat = r'\s(?:month|quarter|annual|end|day)\s'
        # self.month_pat = re.compile(r'(?<=\s)(?:months|monthly|month)(?=\s)', re.IGNORECASE)     # 需要做等值比较的，不能有空格
        self.month_pat = re.compile(r'(?<=[ -])(?:|monthly|month)(?=[ -])', re.IGNORECASE)     # 需要做等值比较的，不能有空格
        self.date_pat = re.compile(r'(?<=[ -])(?:days|year|annual|quarterly|quarter|monthly|month)(?=[ -])', re.IGNORECASE)

        self.number_pat = re.compile(r'(?<=[ -])(?:one|two|three|four|five|six|seven|eight|nine|ten|'
                                     r'eleven|twelve|thir|forty|'
                                     r'first|second|fif|nin)', re.IGNORECASE)

        self.quarter_pat = r'quarter'
        self.annual_pat = r'annual'
        self.time_pat = r'(?:end|day)'
        self.cont_pat = r'\s(?:report|financial statement)\s'

        self.routine_pat = re.compile(r'\s(?:each|every)\s', re.IGNORECASE)
        self.fin_pat1 = re.compile(r'\s(?:financial_statement|financial_report|consolidated|consolidating|'
                                   r'balance_sheet|cash_flow|income|earning|profit|revenue|sale|'
                                   r'unaudited|audited)\s', re.IGNORECASE)
        self.fin_pat2 = re.compile(r'EBIT|EBDIT|EPS')
        self.debt_pat = re.compile(r'bank|debt|loan|credit|borrow', re.IGNORECASE)

        # projection info
        self.proj_pat = re.compile(r'budgeted|budgets|budget|projections|projected|projection|forecasted|'
                                   r'forecast|anticipated|anticipations|anticipation|plans|plan', re.IGNORECASE)

        # self.date_pat = re.compile(r'(?<=\s)(?:days|year|annual|quarterly|quarter|monthly|month)(?=\s)', re.IGNORECASE)

    def get_duedate_sens(self, para: str) -> dict:
        """
        return the sentence that contains the due date in this paragraph
        if None, that means it does not has due date info
        """

        possible_sens = []
        due_date_sens = {'month': [], 'quarter': [], 'annual': [], 'others': []}

        # 首先在段落中查找包含 financial 相关的关键词的句子
        sens = split_sen(para)
        for sen in sens:

            fin_keys = []
            fin_keys.extend([fk.strip() for fk in self.fin_pat1.findall(sen)])
            fin_keys.extend([fk.strip() for fk in self.fin_pat2.findall(sen)])
            fin_keys = list(set(fin_keys))
            if fin_keys:
                possible_sens.append((sen, fin_keys))

        del sens, para      # 手动释放内存

        # 在候选句子中选择 monthly 信息的句子
        # month前后五个词之内 each/every
        for psen, fin_keys in possible_sens:

            is_true = False
            shorten_month_sen = []

            month_words = [month_word.strip() for month_word in self.month_pat.findall(psen)]
            psen_words = psen.strip().split()

            m_pointer = 0
            s_pointer = 0
            for p_w in psen_words:
                if m_pointer >= len(month_words):
                    break
                if month_words[m_pointer] != p_w:
                    s_pointer += 1
                    continue
                else:
                    try:
                        start = max(0, s_pointer - 6)
                        end = min(s_pointer + 5, len(psen_words))
                        short_sen = ' '.join(psen_words[start: end])
                        routine_key = self.routine_pat.search(short_sen)
                        if routine_key:
                            routine_key = routine_key.group().strip()
                            shorten_month_sen = psen_words[start: end]

                            rk_index = shorten_month_sen.index(routine_key)

                            psen_words[start+rk_index] = f'****{routine_key}****'
                            psen_words[s_pointer] = f'****{month_words[m_pointer]}****'
                            shorten_month_sen[rk_index] = f'****{routine_key}****'
                            shorten_month_sen[s_pointer-start] = f'****{month_words[m_pointer]}****'

                            is_true = True
                        m_pointer += 1
                        s_pointer += 1
                    except:
                        print('error: 91: ', short_sen)

            if is_true:
                due_date_sens['month'].append((' '.join(psen_words), ' '.join(shorten_month_sen), fin_keys))

        return due_date_sens

    def get_shorten_sen(self, key_word: str, sentence: str) -> str:
        sen_list = sentence.strip().split()
        key_position = 0
        try:
            key_position = sen_list.index(key_word.strip())
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
        if type(key_words) is not list:
            key_words = [key_words]
        # remove duplicated keys
        for w in set(key_words):
            sentence = sentence.replace(w, f'****{w}****', 100)
        return sentence

    def write_xls_header(self, headers, xls_book, sheet_name='sheet1'):
        """
        :param xls_book:
        :param headers:
        :return: xls_sheet, row_iter
        """
        # init headers for sheet
        xls_sheet = xls_book.add_sheet(sheet_name)
        for col, head in enumerate(headers):
            xls_sheet.write(0, col, head)
        row_iter = 1

        return xls_sheet, row_iter

    def write_xls_sheet(self, sheet, row, headers, **content: dict):
        """
        :param sheet: target sheet
        :param row: new row to be wrote
        :param content: dict to be write into sheet, which should contain
                        name, is_original, first_lines, shorten_sen, due_date_sen
        :return: sheet object, next row number
        """

        matched_sens = content.pop('matched_sens', None)
        if matched_sens:
            for sen, short_sen in set(matched_sens):
                # re-clean
                sen = re.subn(r'[-= ]{5,}', '', sen)[0]

                sheet.write(row, 0, content['name'])
                sheet.write(row, 1, short_sen)
                sheet.write(row, 2, sen)
                row += 1
        else:
            # re-clean first lines
            content['first_lines'] = re.subn(r'[-= ]{5,}', '', content.get('first_lines', ''))[0]
            for i in range(len(headers)):
                sheet.write(row, i, content.get(headers[i], None))
            row += 1

        return sheet, row

    def global_search_by_fin_key(self, content, interval) -> list:

        # preprocessing
        content = re.subn(r'balance sheet', 'balance_sheet', content)[0]
        content = re.subn(r'financial statement', 'financial_statement', content)[0]
        content = re.subn(r'financial report', 'financial_report', content)[0]
        content = re.subn(r'cash flow', 'cash_flow', content)[0]

        def search_fin_keys(txt):
            fin_keys_1 = [fk.strip() for fk in self.fin_pat1.findall(txt)]
            fin_keys_2 = [fk.strip() for fk in self.fin_pat2.findall(txt)]
            return fin_keys_1, fin_keys_2

        sens_res = []

        fin_keys_1, fin_keys_2 = search_fin_keys(content)

        pter_content = 0
        pter_fk_1 = 0
        pter_fk_2 = 0

        content_words = [wd.strip() for wd in content.split()]
        total_length = len(content_words)
        while (pter_fk_1 < len(fin_keys_1) or pter_fk_2 < len(fin_keys_2)) and pter_content < total_length:

            fk_1 = fin_keys_1[pter_fk_1] if pter_fk_1 < len(fin_keys_1) else ''
            fk_2 = fin_keys_2[pter_fk_2] if pter_fk_2 < len(fin_keys_2) else ''

            if content_words[pter_content] == fk_1 or content_words[pter_content] == fk_2:
                start = max(0, pter_content-interval)
                end = min(total_length, pter_content+interval)
                sentence = ' '.join(content_words[start: end])
                tmp_fk_1, tmp_fk_2 = search_fin_keys((sentence))

                # highlight key words
                sentence = self.get_highlight_sen(tmp_fk_1, sentence)
                sentence = self.get_highlight_sen(tmp_fk_2, sentence)
                sens_res.append(sentence)

                # incease pointer index
                # pter_content += end
                # pter_fk_1 += len(tmp_fk_1)
                # pter_fk_2 += len(tmp_fk_2)
                pter_content += 1
                pter_fk_1 += 1
                pter_fk_2 += 1
            else:
                pter_content += 1

        return sens_res

    def global_search_by_proj_key(self, content, interval) -> list:

        # preprocessing
        content = re.subn(r'balance sheet', 'balance_sheet', content)[0]
        content = re.subn(r'financial statement', 'financial_statement', content)[0]
        content = re.subn(r'financial report', 'financial_report', content)[0]
        content = re.subn(r'cash flow', 'cash_flow', content)[0]

        def search_proj_keys(txt):
            proj_keys = [pk.strip() for pk in self.proj_pat.findall(txt)]
            return proj_keys

        sens_res = []

        proj_keys = search_proj_keys(content)

        pter_content = 0
        pter_pk = 0

        content_words = [wd.strip() for wd in content.split()]
        total_length = len(content_words)
        while pter_pk < len(proj_keys) and pter_content < total_length:

            pk = proj_keys[pter_pk] if pter_pk < len(proj_keys) else ''

            if content_words[pter_content] == pk:
                start = max(0, pter_content-interval)
                end = min(total_length, pter_content+interval)
                sentence = ' '.join(content_words[start: end])
                tmp_pk = search_proj_keys(sentence)

                # highlight key words
                sentence = self.get_highlight_sen(tmp_pk, sentence)
                sens_res.append(sentence)

                # incease pointer index
                # pter_content += end
                # pter_fk_1 += len(tmp_fk_1)
                # pter_fk_2 += len(tmp_fk_2)
                pter_content += 1
                pter_pk += 1
            else:
                pter_content += 1

        return sens_res

    def global_filter_by_key(self, content_list, pattern) -> list:


        full_shorten_res = []

        for content in content_list:

            matched_keys = getattr(self, pattern).findall(content)
            if not matched_keys:
                continue

            content_words = content.split()
            total_length = len(content_words)
            s_pointer = 0
            m_pointer = 0

            while m_pointer < len(matched_keys) and s_pointer < total_length:

                if content_words[s_pointer] == matched_keys[m_pointer]:
                    start = max(0, s_pointer - 10)
                    end = min(s_pointer + 10, total_length)
                    # # short_sen = ' '.join(content_words[start: end])
                    # # routine_key = self.routine_pat.search(short_sen)
                    # # if routine_key:
                    # #     routine_key = routine_key.group().strip()
                    # #     shorten_month_sen = content_words[start: end]
                    # #
                    # #     rk_index = shorten_month_sen.index(routine_key)
                    # #
                    # #     content_words[start + rk_index] = f'****{routine_key}****'
                    # #     content_words[s_pointer] = f'****{content_words[s_pointer]}****'
                    # #     shorten_month_sen[rk_index] = f'****{routine_key}****'
                    # #     shorten_month_sen[s_pointer - start] = f'****{matched_keys[m_pointer]}****'
                    # #
                    # #     full_shorten_res.append((' '.join(content_words), ' '.join(shorten_month_sen)))

                    # check if there number word in former 5 words,
                    # if yes, pass this sentence
                    tmp_former = ' '.join(content_words[max(0, s_pointer-3):s_pointer])
                    if self.number_pat.search(tmp_former):
                        break
                    if re.search(r'\d{1,}', tmp_former):
                        break

                    shorten_month_sen = content_words[start: end]
                    content_words[s_pointer] = f'****{content_words[s_pointer]}****'
                    shorten_month_sen[s_pointer - start] = f'****{matched_keys[m_pointer]}****'
                    full_shorten_res.append((' '.join(content_words), ' '.join(shorten_month_sen)))

                    m_pointer += 1
                s_pointer += 1

        return full_shorten_res


# if __name__ == '__main__':
#
#     info_tool = InfoTools()
#     covenant_processor = ConvenantTools()
#     fail_list = []
#
#     text_folder = './text/txt_result/'
#
#     suc_counter = 0
#     err_counter = 0
#     date_dict = {}
#
#     year_file_dic = {}
#     year = 2007
#     year_folder = os.path.join(text_folder, str(year))
#     year_file_dic[year] = [file for file in os.listdir(year_folder) if file.endswith('.txt')]
#
#     for year, file_names in tuple(year_file_dic.items()):
#
#         # 初始化excel workbook，否则信息会累加到后面的文件中
#         date_book = xlwt.Workbook()
#         headers = ['name', 'is_original', 'is_debt', 'first_lines', 'shorten_sen', 'due_date_sen']
#         # sheet_names = ['month', 'quarter', 'annual', 'others']
#         sheet_names = ['month']
#
#         # init headers for each type of sheets
#         xls_sheets = {}
#         for type in sheet_names:
#             xls_sheets[type] = date_book.add_sheet(type)
#             for col, head in enumerate(headers):
#                 xls_sheets[type].write(0, col, head)
#         row_iter = dict.fromkeys(sheet_names, 1)
#
#         date_dict[year] = {'month': 0, 'quarter': 0, 'annual': 0, 'others': 0}
#
#         year_folder = os.path.join(text_folder, str(year))
#
#         for name in file_names:
#
#             is_debt = False
#
#             with open(os.path.join(year_folder, name), 'r', encoding='utf-8') as f:
#                 lines = [line for line in f.readlines() if line.strip()]
#                 first_lines = covenant_processor.get_n_lines(5, lines)
#                 is_origin = True if covenant_processor.is_original(first_lines) else False
#                 is_debt = True if re.search(info_tool.debt_pat, covenant_processor.get_n_lines(10, lines)) else False
#                 content = '\n'.join(lines)
#             del lines
#             # paras = split_para(src_dic['covenant'])
#             paras = split_para(content)
#
#             # info_sens = []
#             date_sens = {'month': [], 'quarter': [], 'annual': [], 'others': []}
#             for para in paras:
#                 sens = info_tool.get_duedate_sens(para)  # get a list
#
#                 if sens:
#                     if sens['month']:
#                         date_sens['month'].extend(sens['month'])
#                     elif sens['quarter']:
#                         date_sens['quarter'].extend(sens['quarter'])
#                     elif sens['annual']:
#                         date_sens['annual'].extend(sens['annual'])
#                     elif sens['others']:
#                         date_sens['others'].extend(sens['others'])
#
#             # write info into xls by each file iteration
#             for date_type in sheet_names:
#                 if not date_sens[date_type]:
#                     continue
#                 date_dict[year][date_type] += 1
#                 _, row_iter[date_type] = info_tool.write_xls_sheet(sheet=xls_sheets[date_type], row=row_iter[date_type],
#                                                                    name=name, is_original=is_origin, is_debt=is_debt,
#                                                                    first_lines=first_lines,
#                                                                    due_date_sen=date_sens.get(date_type))
#                 break
#             break
#         break
#         date_book.save(os.path.join('./output/fulltext', f'due_date_{year}.xls'))
#         del date_book
#
#     print('due date finished!')
#     print(date_dict)
#
#
#
#
#     #
#     # year_file_dic = {}
#     # year = 2007
#     # # year_folder = os.path.join(truncated_cove_folder, str(year))
#     # year_folder = os.path.join(text_folder, str(year))
#     # year_file_dic[year] = [file for file in os.listdir(year_folder) if file.endswith('.txt')]
#     #
#     # for year, file_names in tuple(year_file_dic.items()):
#     #
#     #     print(year)
#     #
#     #     # 初始化excel workbook，否则信息会累加到后面的文件中
#     #     date_book = xlwt.Workbook()
#     #     headers = ['name', 'is_original', 'is_debt', 'first_lines', 'shorten_sen', 'due_date_sen']
#     #     # sheet_names = ['month', 'quarter', 'annual', 'others']
#     #     sheet_names = ['month']
#     #
#     #     # init headers for each type of sheets
#     #     xls_sheets = {}
#     #     for type in sheet_names:
#     #         xls_sheets[type] = date_book.add_sheet(type)
#     #         for col, head in enumerate(headers):
#     #             xls_sheets[type].write(0, col, head)
#     #     row_iter = dict.fromkeys(sheet_names, 1)
#     #
#     #     date_dict[year] = {'month': 0, 'quarter': 0, 'annual': 0, 'others': 0}
#     #
#     #     year_folder = os.path.join(text_folder, str(year))
#     #
#     #     for name in file_names:
#     #
#     #         is_debt = False
#     #
#     #         with open(os.path.join(year_folder, name), 'r', encoding='utf-8') as f:
#     #             lines = [line for line in f.readlines() if not line.strip()]
#     #             first_lines = covenant_processor.get_n_lines(5, lines)
#     #             is_origin = True if covenant_processor.is_original(first_lines) else False
#     #             is_debt = True if re.search(info_tool.debt_pat, covenant_processor.get_n_lines(10, lines)) else False
#     #             content = ''.join(lines)
#     #             # src_dic = json.load(f)      # keys: name, first_lines, is_original, covenant
#     #         del lines
#     #         # paras = split_para(src_dic['covenant'])
#     #         paras = split_para(content)
#     #
#     #         # info_sens = []
#     #         date_sens = {'month': [], 'quarter': [], 'annual': [], 'others': []}
#     #         for para in paras.split('\n'):
#     #             sens = info_tool.get_duedate_sens(para)  # get a list
#     #
#     #             if sens:
#     #                 if sens['month']:
#     #                     date_sens['month'].extend(sens['month'])
#     #                 elif sens['quarter']:
#     #                     date_sens['quarter'].extend(sens['quarter'])
#     #                 elif sens['annual']:
#     #                     date_sens['annual'].extend(sens['annual'])
#     #                 elif sens['others']:
#     #                     date_sens['others'].extend(sens['others'])
#     #
#     #
#     #         # write info into xls by each file iteration
#     #         for date_type in sheet_names:
#     #             if not date_sens[date_type]:
#     #                 continue
#     #             date_dict[year][date_type] += 1
#     #             _, row_iter[date_type] = info_tool.write_xls_sheet(sheet=xls_sheets[date_type], row=row_iter[date_type],
#     #                                                                name=name, is_original=is_origin, is_debt=is_debt,
#     #                                                                first_lines=first_lines,
#     #                                                                due_date_sen=date_sens.get(date_type))
#     #             break
#     #         break
#     #     break
#     #     date_book.save(os.path.join('./output/duedate/2007', f'due_date_{year}.xls'))
#     #     del date_book
#     #
#     # print('due date finished!')
#     # print(date_dict)


