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
    '''
    copy content from one place to another
    '''
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


def rename_files(folder=None, *user_ids):
    if not folder :# or folder == '..':
        folder = os.getcwd()
    for file_ in os.listdir(folder):
        if '.com' in file_ or '@' in file_:
            new_content = os.path.join(folder, file_)
            if os.path.isfile(new_content):
                rename(new_content, *user_ids)
            else:
                rename_files(new_content, *user_ids)
            rename(folder, *user_ids) # when comes out from deepest folder change name

#####################

def compress(folder, format='zip', name=None, loc=None, delete=False):
    if name is None:
        name = folder.split('/')[-1]

    if loc:
        os.chdir(loc)
    if format == 'zip':
        print('cretaing zip')
        os.system('zip -r "{}".zip "{}"'.format(name, folder))

    elif format == 'tar':
        print('creating tar')
        os.system('tar cvf "{}".tar "{}"'.format(name, folder))

    elif format == 'rar':
        print('creating rar', 'rar a "{}".rar "{}"/*'.format(name, folder))
        os.system('rar a "{}".rar "{}"/*'.format(name, folder))
    if delete:
        os.system('rm -rf ' + posix_name(folder))


def convert(file_name, saveas=None,  to="mp3"):
    file_ext = file_name.split('.')[-1]
    if not saveas:
        saveas = os.path.dirname(file_name) + '/' + file_name.split('/')[-1].replace(file_ext, to)

    # if exists quit
    if os.path.exists(saveas):
        print('Skipping', file_name)
        return

    print(file_name, saveas, end='\n')
    print(os.system('ls -lh ' + posix_name(file_name)))
    ffmpeg_cmd = "ffmpeg -i " + posix_name(file_name) + "\
            -map 0:a:0 -b:a 26k -y " + posix_name(saveas) + \
            '>  /dev/null'
    print('Converting\t', file_name)
    os.system(ffmpeg_cmd)
    print('Compressed\t', file_name.split('/')[-1])


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


def readable_size(size):

    readable = 0
    unit = 'B'
    
    if size>1024:
        size /= 1024
        unit = " KB"
    if size>1024:
        size /= 1024
        unit = " MB"
    if size>1024:
        size /= 1024
        unit = " GB"
    return '{:.2f} {}'.format(size, unit)


def total_size(folder, total=0):
    from pathlib import Path
    
    if os.path.isfile(folder):
        return str(os.stat(folder).st_size/(1024**2)) + ' MB'
    
    root_directory = Path(folder)
    size = sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())
    return readable_size(size)


##########################

def is_incomplete(comp_file, orig_file):
    orig_size = os.stat(orig_file).st_size
    comp_size = os.stat(comp_file).st_size
    return (orig_size, comp_size, comp_size < (orig_size//18))


def is_dup(file1, file2):
    file1_sz = os.path.getsize(file1)
    file2_sz = os.path.getsize(file2)


    copy_file1 = file1
    copy_file2 = file2
    
    # if last name / original name of files are same
    file1 = ".".join(file1.split('/')[-1].split('.')[:-1])
    file2 = ".".join(file2.split('/')[-1].split('.')[:-1])

    criteria1 = (file1_sz == file2_sz) # equal size
    criteria2 = (file1 in file2)
    criteria3 = (file2 in file1)
    # print(file1, file2, criteria1, criteria2, criteria3)

    if  criteria1 and criteria2:
        return copy_file2 # file2 is copy
    elif criteria1 and criteria3: # len of file1 > file2
        return copy_file1 # file1 is copy
    elif criteria2 and file2_sz > file1_sz:
        return copy_file1  # file1 is incomplete copy
    elif criteria3 and file2_sz < file1_sz:
        return copy_file2  # file1 is incomplete copy


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


def encrypted_name(name, val=1):
    top_name = os.path.basename(name)
    new_name = ''
    for char in top_name:
        # change only alphabets (65=A, 97=a)
        if (ord(char)>64 and ord(char) < 91) or (
            ord(char) > 96 and ord(char) < 123):
                new_name += chr(ord(char) + val)
        else:
            new_name += char
    # renmae files and folder
    return os.path.join(os.path.dirname(name), new_name)


def encrypt(folder, val=1, start=True):
    files = []
    for content in os.listdir(folder):
        if content.startswith('.'):  # hidden files of dirs
            continue
        file_ = folder + '/' + content
        if os.path.isdir(file_):
            encrypt(file_, start=False)
        else:
            files.append(file_)

    # deepest dir
    for file_ in files:
        new_name = encrypted_name(file_)
        # print(file_, new_name)
        rename(file_, new_name)

    # now encrypt folder
    if start:
        rev_name = folder.split('/')[-1][::-1]
        rename(folder, os.path.join(os.path.dirname(folder) ,rev_name))
    if not start:
        new_folder = encrypted_name(folder)
        # print(folder, new_folder)
        rename(folder, new_folder)


###########################

def decrypt_name(name, val=1):
    orig_name = ''
    top_name = os.path.basename(name)
    for char in top_name:
        if (ord(char)>65 and ord(char) < 92 ) or (
            ord(char) > 97 and ord(char) < 124):
                orig_name += chr(ord(char) - val)
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
    if not start:
        dec_fold = decrypt_name(folder)
        rename(folder, dec_fold)
