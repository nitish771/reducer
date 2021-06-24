import os
from itertools import permutations
import shutil

files = []


def getFiles(fold):
    global files
    for i in os.listdir(fold):
        new = fold + '/' + i
        if os.path.isfile(new):
            files.append(new)
        else:
            getFiles(new)


def isDup(f1, f2):
    f1_ext = f1.split('.')[-1]
    f2_ext = f2.split('.')[-1]

    if f1_ext == f2_ext:
        return (f2 in [".".join(f1.split('.')[:-1]) +
                   '(' + str(i) + ').' + f1_ext for i in range(1, 6)] or
                f2 in [".".join(f1.split('.')[:-1]) + ' (' +
                   str(i) + ').' + f1_ext for i in range(1, 6)])
        return 0


def merge_items_and_delete(main_fold, copy_folders: list):
    for fold in copy_folders:
        for item in os.listdir(fold):
            try:
                shutil.copy(fold+'/'+item, main_fold)
            except Exception as e:
                continue
        print('deleting', fold)
        shutil.rmtree(fold)


def confirm_copy_folders(folders: dict):
    confirm = {}
    for key, values in folders.items():
        for value in values:
            if value in [ key + ' (' + str(i) + ')' for i in range(1, 6)] \
                or value in [ key + '(' + str(i) + ')' for i in range(1, 6)]:
                    if confirm.get(key):
                        confirm[key].append(value)
                    else:
                        confirm[key] = [value]
    return confirm


def possible_copy_folders(folder):
    folders = []
    possible = {}
    for fold in os.listdir(folder):
        new_content = folder+'/'+fold
        if os.path.isdir(new_content):
            folders.append(new_content)
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
    return confirm_copy_folders(possible)


def dup_folder(folder):
    for key, items in possible_copy_folders(folder).items():
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
