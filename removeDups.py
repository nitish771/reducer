import os
from itertools import permutations
import shutil
import re
# from pdb import set_trace


files = []


def getFiles(fold):
    global files
    for i in os.listdir(fold):
        new = fold + '/' + i
        if os.path.isfile(new):
            files.append(new)
        else:
            getFiles(new)


def regexify(name):
    new_name = ''
    for char in name:
        if char == '(':
            new_name += '\('
        elif char == ')':
            new_name += '\)'
        else:
            new_name += char
    return new_name


def isDup(f1, f2):
    f1_ext = f1.split('.')[-1]
    f2_ext = f2.split('.')[-1]

    if (f1_ext == f2_ext) or (len(f1.split('.')) == 1 and  len(f2.split('.')) == 1 ) :
        key = regexify(min(f1, f2))
        copy = f1 if key!=f1 else f2

        re_ptrn = re.compile(rf'^({key}(\s\(\d\))+)$')
        try:
            if (re_ptrn.findall(copy)[0][0]):
                return 1
        except Exception as e:
            pass
        return 0


def merge_items_and_delete(main_fold, copy_folders: list):
    for fold in copy_folders:
        for item in os.listdir(fold):
            try:
                shutil.copy(fold + '/' + item, main_fold)
            except Exception as e:
                continue
        print('deleting', fold)
        try:
            shutil.rmtree(fold)
        except Exception as e:
            print(e)


def get_folders(folder, folders):
    '''Get all the subfolders '''

    for i in os.listdir(folder):
        new = folder + '/' + i
        if os.path.isdir(new):
            get_folders(new, folders)
            folders.append(new)


def possible_copy_folders(folder):
    folders = []
    possible = {}
    top_dir = os.path.dirname(folder)

    get_folders(folder, folders)

    folders = sorted(folders)
    cur = 0

    for i in range(1, len(folders)):
        if folders[cur] in folders[i]:
            if possible.get(folders[cur]):
                possible[folders[cur]].append(folders[i])
            else:
                possible[folders[cur]] = [folders[i]]
        else:
            cur = i
    # print(possible)
    return possible


def confirm_copy_folders(folder):
    folders = possible_copy_folders(folder)  # dict
    confirm = {}
    for key, values in folders.items():
        re_ptrn = re.compile(rf'^({key}(\s\(\d\))+)$')
        for value in values:
            try:
                if re_ptrn.findall(value)[0][0] == value:
                    if confirm.get(key):
                        confirm[key].append(value)
                    else:
                        confirm[key] = [value]
            except IndexError as e:
                pass
    return confirm


def dup_folder(folder):
    for key, items in confirm_copy_folders(folder).items():
        merge_items_and_delete(key, items)


def remove(fold):
    global files

    dup_folder(fold)
    getFiles(fold)

    files.sort(key=lambda x: len(x))

    for i in permutations(files, 2):
        out = isDup(*i)
        if out:
            print('removing ', i[1])
            os.system('rm -rf "' + i[1] + '"')
    files = []
