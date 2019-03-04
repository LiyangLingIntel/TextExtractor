

import os
import re
from src.py.settings import resource_folder, cove_folder, output_folder
from src.py.utils import split_para


class ReportTools:

    def __init__(self):

        self.keywords = ['information covenant', 'information requirement', 'reporting covenant', 'reporting requirement',
                         'financial statement']

def reports_para():

    pass


if __name__ == '__main__':


    # rc_file_names = []
    # for root, dirs, files in os.walk(resource_folder):
    #     print(files)
    #     for name in files:
    #         rc_file_names.append(os.path.join(root, name))

    example = 'final-0000012355-02-000023.txt'
    paras = split_para(example)

    print('ok')
