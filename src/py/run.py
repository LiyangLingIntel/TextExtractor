from py.extractor.covenant_extractor import ConvenantTools
from py.extractor.specialinfo_extractor import InfoTools
from py.extractor.reports_extractor import split_para, split_sen

import os, json


if __name__ == '__main__':

    """
    Extract covenant Section from original text
    1. Traverse text folder and find all contract files
    2. Extract table of content from contract
    3. Find covenant section title
    4. Extract covenant section through corresponding main title
    """

    covenant_processor = ConvenantTools()

    year_file_dic ={}
    # for year in range(1996, 2018):
    year = 2007
    year_folder = os.path.join(text_folder, str(year))
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

        year_folder = os.path.join(text_folder, str(year))
        target_folder = os.path.join('./output/', str(year))
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



    # file_names = find_files_with_postfix(text_folder, 'txt')
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