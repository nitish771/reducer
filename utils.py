import os
import re
from itertools import combinations, product
import string
import multiprocessing as mp


def download(url, loc=None):
    if loc:
        os.chdir(loc)
    os.system('wget -c ' + url)


def copy_to(src, dest, delete=False):
    '''copy content from one place to another'''
    import shutil

    if delete:
        os.system('cp -ru "{}" "{}" '.format(src, dest))    
        shutil.rmtree(src)
    else:
        os.system('cp -ru "{}" "{}" '.format(src, dest))


def posix_name(name):
    """return space seperated string into closed double quotes"""
    return f'"{name}"'


####### Remove Content source from names #########

def get_sources(name):
    """Returns sources of files recursively"""
    
    res = []
    if '@' in name: # channel id
        user_name = re.compile(r'(@\w+)')
        res.append(user_name.search(name).group())
    if '.com' in name: # website url
        website = re.compile(r'(\[?(https://)?\w+\.(com|io|eu|us)?)\]?')
        res.append(website.search(name).group())
    return res


def rename(file_name, *args):
    replace_with = get_sources(file_name)
    # web_url   # channel_id
    user_id_1 = user_id_2 = '' # to replace id1 with link and id2 with channel

    if len(args)==1:
        user_id_1 = user_id_2 = args[0]
    if len(args)==2:
        user_id_1 = args[0] # link
        user_id_2 = args[0] # id
        
    try:
        cur_dir, new_name = os.path.dirname(file_name), os.path.basename(file_name)

        if len(replace_with):
            for replace_string in replace_with:
                if '@' in replace_string:
                    new_name = new_name.replace(replace_string, user_id_2).strip()
                else:
                    new_name = new_name.replace(replace_string, user_id_1).strip()

        # Rename file now
        new_name = ' '.join([name for name in new_name.split(' ') if name!=''])
        new_name = os.path.join(cur_dir, new_name)
        if file_name != new_name:
            print('renaming', posix_name(file_name.split('/')[-1]), posix_name(os.path.join(cur_dir, new_name)))
        #     os.system('mv ' + posix_name(file_name)  + ' ' +  posix_name(new_name))
    except Exception as e:
        print('error in renaming', e)


def rename_files(folder=None, **user_ids):
    if not folder :# or folder == '..':
        folder = os.getcwd()

    for file_ in os.listdir(folder):
        new_content = os.path.join(folder, file_)
        if os.path.isfile(new_content):
            for  item in user_ids.values():
                if item in file_:
                    new_name = new_content.replace(item, '')
                    try:
                        os.system('mv "' + new_content + '"' + ' "' + new_name + '"')
                    except Exception as e:
                        print(e)
        else:
            rename_files(new_content, **user_ids)

    for item in user_ids.values():
        if item in folder.split('/')[-1]:
            new_name = folder.replace(item, '')
            try:
                os.system('mv "' + folder + '"' + ' "' + new_name + '"')
                return
            except Exception as e:
                print(e)

#####################

def convert(file_name, saveas=None,  to="mp3"):
    try:
        file_ext = file_name.split('.')[-1]
        if not saveas:
            saveas = os.path.dirname(file_name) + '/' + file_name.split('/')[-1].replace(file_ext, to)

        # if exists quit
        if os.path.exists(saveas):
            print('Skipping', file_name)
            return

        print(file_name, saveas, end='\n')
        ffmpeg_cmd = "ffmpeg -i " + posix_name(file_name) + "\
                -map 0:a:0? -b:a 26k -y " + posix_name(saveas) + \
                '>  /dev/null'
        print('Converting\t', file_name)
        os.system(ffmpeg_cmd)
    except Exception as e:
        print(e)


def extract(file, loc=None):
    name, format = ".".join(file.split('.')[:-1]), file.split('.')[-1]
    if loc:
        os.chdir(loc)
    if format == 'zip':
        print('unzipping')
        os.system('unzip ' + posix_name(name) + '.zip')
    elif format == 'tar':
        print('extracting tar')
        os.system('tar xvf ' + posix_name(name) + 'tar')
    elif format == 'rar':
        print("unarchiving rar")
        os.system('rar e ' + posix_name(name) + '.rar')


def get_size(file):
    if os.path.isfile(file):
        return os.stat(file).st_size
    return 0


def size(folder):
    folder_size = 0
    if os.path.isfile(folder):
        return get_size(folder)
    else:
        for file in os.listdir(folder):
            new_content = folder + '/' + file
            folder_size += size(new_content)
    return folder_size


def readable_size(size):

    readable = 0
    unit = 'B'
    
    if size>=pow(1024,3):
        size /= pow(1024,3)
        unit = "GB"
    elif size>=pow(1024,2):
        size /= pow(1024, 2)
        unit = "MB"
    elif size>=1024:
        size /= 1024
        unit = "KB"
    else:
        unit = 'B'
    return '{:.2f} {}'.format(size, unit)


def read_seconds(sec):
    minute = 0
    sec = int(sec)
    if sec < 60:
        pass
    else:
        minute = sec // 60
        rem_time = sec - minute*60
        sec = rem_time if rem_time<60 else -1
    return '{:0>2}:{:0>2}'.format(minute, sec)


def total_size(folder, total=0):
    from pathlib import Path
    
    if os.path.isfile(folder):
        return str(os.stat(folder).st_size/(1024**2)) + ' MB'
    
    root_directory = Path(folder)
    size = sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())
    return readable_size(size)


def compress(folder, format_='zip', name=None, loc=None, delete=False, subfolders=False):
    # if size is not given will compress entire folder
    if not loc:
        loc = "/".join(folder.split('/')[:-1])

    if not subfolders:
        cmd = ''
        if name is None:
            name = folder.split('/')[-1]

        if format_ == 'zip':
            cmd += f'zip -r "{loc}/{name}".zip "{folder}"'

        elif format_ == 'tar':
            cmd += f'tar cvf "{loc}/{name}".tar "{folder}"'

        elif format_ == 'rar':
            cmd += f'rar a "{loc}/{name}".rar "{folder}"/*'

    else:
        # if size is given 
        files = []  # compress files in folder 
        for fold in os.listdir(folder):
            new_content = folder + '/' + fold
            if os.path.isfile(new_content):
                files.append(new_content)
            else:
                compress(new_content, loc=loc, format_=format_, delete=delete, name=name)
        if files:
            name = folder.split('/')[-1]
            cmd = f'zip -r "{loc}//{name} files".zip '
            for file in files:
                cmd += f' "{file}" '

    if not os.path.exists(loc+'/'+name+' files.'+format_):
        print(cmd)
        os.system(cmd)

    if delete:
        os.system('rm -rf ' + posix_name(folder))


##########################

def is_incomplete(comp_file, orig_file, factor=18):
    orig_size = os.stat(orig_file).st_size
    comp_size = os.stat(comp_file).st_size
    return (orig_size, comp_size, comp_size < (orig_size//factor))


def is_dup(file1, file2):
    ''' 
    Checks if size of both file is same and one file's name contains another's name
    '''

    file1_sz = os.path.getsize(file1)
    file2_sz = os.path.getsize(file2)

    copy_file1 = file1
    copy_file2 = file2
    
    # if last name / original name of files are same
    file1 = ".".join(file1.split('/')[-1].split('.')[:-1])
    file2 = ".".join(file2.split('/')[-1].split('.')[:-1])

    criteria1 = (file1_sz == file2_sz)
    criteria2 = (file1 in file2)
    criteria3 = (file2 in file1)

    # print(file1, file2, criteria1, criteria2, criteria3)
    # 4096 is size of folder
    if file1_sz != 4096 and criteria1: # equal size
        if criteria2:
            return file2 # file2 is copy
        elif criteria3: # len of file1 > file2
            return file1 # file1 is copy
    return False


def delete_dups(folder, sema=0):
    files = []
    deletable = []
    pool = mp.Pool()

    if not sema:
        print('deleting dumplicates files from ', folder)

    print(folder)
    for dir_ in os.listdir(folder):
        new_content = os.path.join(folder, dir_)
        if os.path.isdir(new_content):
            delete_dups(new_content, 1)
        else:
            files.append(new_content)

    for comb in combinations(files, 2):  # Call the function for one folder
        # print(comb)
        dup_file = is_dup(*list(comb))
        if dup_file:
            deletable.append(dup_file)


    for dup_file in deletable:
        print("=> {:<50}".format(dup_file.replace(folder, '')))
        os.unlink(dup_file)

############################

def rename(old_name, new_name):
    os.system('mv ' + posix_name(old_name) +  ' ' + posix_name(new_name))


def encrypted_name(name, shift=1):
    top_name = os.path.basename(name)
    new_name = ''
    for char in top_name:
        # change only alphabets (65=A, Z=90, 97=a, z=122)
        if (ord(char)>64 and ord(char) < 91) or (
            ord(char) > 96 and ord(char) < 123):
                new_name += chr(ord(char) + shift)
        elif ord(char)==91:
            new_name += '~'
        else:
            new_name += char
    # renmae files and folder
    return os.path.join(os.path.dirname(name), new_name)


def encrypt(folder, val=1, start=True):
    files = []

    if os.path.isfile(folder):
        return rename(folder, encrypted_name(folder, val))

    for content in os.listdir(folder):
        file_ = folder + '/' + content
        if os.path.isdir(file_):
            encrypt(file_, start=False)
        else:
            files.append(file_)

    # from deepest dir
    for file_name in files:
        new_name = encrypted_name(file_name)
        # print(file_name, new_name)
        rename(file_name, new_name)

    # now encrypt folder
    if start:
        rev_name = folder.split('/')[-1][::-1]
        rename(folder, os.path.join(os.path.dirname(folder) ,rev_name))
    if not start:
        new_folder = encrypted_name(folder)
        rename(folder, new_folder)


###########################

def decrypt_name(name, shift=1):
    orig_name = ''
    top_name = os.path.basename(name)
    for char in top_name:
        if (ord(char)>65 and ord(char) < 92 ) or (
            ord(char) > 97 and ord(char) < 124):
                orig_name += chr(ord(char) - shift)
        elif ord(char) == 126:
            orig_name += '['
        else:
            orig_name += char
    return os.path.join(os.path.dirname(name), orig_name)


def decrypt_list(folder, val=1, start=True, level=1, **kwargs):
    copy_fold = folder
    files = []
    folders = []
    search = kwargs.get('search')

    for content in os.listdir(folder):
        new_content = folder + '/' + content
        if not content.startswith('.'):
            if os.path.isfile(new_content):
                files.append(new_content)
            else:
                folders.append(new_content)
    if start:
        print('='*50)
        folder = os.path.dirname(folder) + '/' + os.path.basename(folder)[::-1]
        print('    ' * (level - 1) + folder + '/')
    else:
        folder = decrypt_name(folder)
        print('    ' * (level - 1)  + folder.split('/')[-1] + '/')

    for file_ in files:
        dec_name = decrypt_name(file_).replace(copy_fold+'/', '')
        print(f"{'    ' * level}{dec_name}")

        if search:
            results = []
            if search == dec_name:
                print(search , 'found in ', folder)
                return folder
            elif search in dec_name:
                results.append(folder)

    for fold in folders:
        if search:
            return decrypt_list(fold, start=False, level=level+1, search=search)
        else:
            decrypt_list(fold, start=False, level=level+1)


def decrypt(folder, val=1, start=True):
    files = []
    if os.path.isfile(folder):
        return rename(folder, decrypt_name(folder, val))

    for content in os.listdir(folder):
        if content.startswith('.'):
            continue
        content = folder+'/'+content
        if os.path.isdir(content):
            decrypt(content, start=False)
        else:
            files.append(content)
    for file in files:
        dec_name = decrypt_name(file)
        rename(file, dec_name)
    if start:
        rev_name = folder.split('/')[-1][::-1]
        rename(folder, os.path.join(os.path.dirname(folder) ,rev_name))
    if not start:
        dec_fold = decrypt_name(folder)
        rename(folder, dec_fold)
