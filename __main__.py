import os
import sys
from multiprocessing import Process, Value
from random import shuffle
from shutil import copy


class Compress:

    def __init__(self, remote=None, local=None, **kwargs):
        self.kwargs = kwargs
        self.remote = remote
        self.local = local

        # Semaphore to count files compressed
        self.value = Value('i', 0)
        self.count = 0

        if self.remote is None:
            self.remote = input("Enter Remote URL : ")
        if self.local is None:
            self.local = input("Enter Local URL : ")

        self.encrypt_ = kwargs.get('encrypt_')  # encrypt while compressing
        self.skip = 0

        self.top_dir = self.remote.split('/')[-1]    # name of the main folder
        self.local = os.path.join(self.local, self.top_dir)   # local abs path
        self.files = []                                    # files to compress
        self.files_by_ext = {}
        self.video = ['mkv', 'mov', 'mp4']
        self.not_down = ['vtt']
        # resolution
        if kwargs.get('res'):
            self.res = kwargs.get('res')
        else:
            self.res = '720'

        if kwargs.get('quitIfFolderExists'):
            if os.path.exists(self.local):
                sys.exit('Exiting - folder exists')

        if kwargs.get('count', 1):
            self.count = self.count_files(self.remote,
                hidden=kwargs.get('hidden'))
            print('total files in folder : ', self.count, '\n')
            for ext, item_no in self.files_by_ext.items():
                print(ext , ':', item_no)
            print()
        
        self.main(kwargs)                    # start compressing
        
        if kwargs.get('delete_dup'):
            remove(self.local)
        
        if kwargs.get('encrypt_'):
            encrypt(self.local)

    def add_not_down(self, xt):
        '''Files whose extension is xt will be ignored (not copied or
        compressed)'''
        self.not_down.append(xt)

    def _top_dir(self, folder):
        return folder.split('/')[-1]

    def valid_unix_name(self, name):
        return '"'+name+'"'

    def to_local(self, content):
        return content.replace(self.remote, self.local)

    def count_files(self, folder, **kwargs):
        total=0
        if os.path.isfile(folder):
            return 1
        # folder
        for file in os.listdir(folder):
            if os.path.isfile(folder + '/' + file):
                ext = file.split('.')[-1].lower()
                if self.files_by_ext.get(ext):
                    self.files_by_ext[ext] += 1
                else:
                    self.files_by_ext[ext] = 1    
                total += 1
            elif kwargs.get('hidden'):
                total += self.count_files(folder+'/'+file)
            elif not file.startswith('.'):
                total += self.count_files(folder+'/'+file)
        return total

    def counter(self):
        print('T', self.count, '-C', self.value.value, '-S', self.skip,
            '-R', (self.count-self.value.value-self.skip), ' || ', end='', sep='')

    def make_dirs(self, folder):
        # Making Directory Copy
        os.chdir(folder)
        
        for dirs in os.listdir(folder):
            if not dirs.split('/')[-1].startswith('.'):
                new_content = folder + '/' + dirs
                if os.path.isdir(new_content):
                    self.make_dirs(new_content)
        
        if not os.path.exists(self.to_local(folder)):
            os.system('mkdir -p ' +
              self.valid_unix_name(self.to_local(folder)))

    def should(self, file_name):
        s = os.path.exists(file_name)
        return not s

    def shorten_name(self, name):
        short = lambda x : x[:3]
        shorten = '/'

        for i in name.split('/')[:-1]:
            if i:
                if len(i)>10:
                    for word in i.split()[:3]:
                        shorten += short(word)+ '.. '
                    shorten += '/'
                else:
                    shorten += short(i) + '/'
        shorten += name.split('/')[-1]
        return shorten

    def compress(self, file, *args):
        local_file = self.to_local(file)
        saveas = self.valid_unix_name(local_file)
        file_name = file.replace(self.remote, '')


        # if exists check for size
        if os.path.exists(local_file):
            # checking here if incomplete recompress
            orig_size, comp_size, status = is_incomplete(local_file, file)

            if not status:  # not incomplete
                return 
            elif comp_size > orig_size:
                # check here if res in wrong
                raise ValueError("Incorrect resolution. Try lower resolution\nFile", file_name)        
            else:
                print(f'AC/CS {orig_size//1024**2}MB/{comp_size//1024**2}MB',
                    os.path.basename(local_file))
                os.unlink(local_file)
        
        ffmpeg_cmd = "ffmpeg -i " + self.valid_unix_name(file) + "\
                -b:a 64k -ac 1 -vf scale=\"'w=-2:h=trunc(min(ih," + str(self.res) + ")/2)*2'\" \
                -crf 32 -profile:v baseline -level 3.0 -preset slow -v error -strict -2 -stats \
                -y -r 20 " + saveas

        if self.count:
            self.counter()

        print('compressing\t', self.shorten_name(self.shorten_name(file_name)))
        
        os.system(ffmpeg_cmd)

        # increase compresed files value
        with self.value.get_lock():
            self.value.value += 1
        
        print('Compressed\t', self.shorten_name(file_name.split('/')[-1]))
        
    def convert(self, file, ext="mp3"):
        file_ext = file.split('.')[-1]
        saveas = (file.replace(file_ext, ext)).replace(self.remote, self.local)
        # print(saveas)
        local_name = self.to_local(file)
        file_name = file.replace(self.remote, '')

        # if exists check for size
        if os.path.exists(file_name):
            orig_size, comp_size, status = is_incomplete(file_name, file)
            if not status:  # not incomplete
                return 
            else:
                print(file_name)
                print(f'AC/CS {orig_size//1024**2}MB/{comp_size//1024**2}MB')
                os.unlink(local_name)
        
        if self.count:
            self.counter()
        
        # print('converting', self.shorten_name(file))
        convert(file_name=file, saveas=saveas, to=ext)

        # increase compresed files value
        with self.value.get_lock():
            self.value.value += 1

        # print('Converted\t', self.shorten_name(file_name.split('/')[-1]))

    def get_file(self, folder):
        os.chdir(folder)
        for file in os.listdir(folder):
            if not file.startswith('.'):
                new_file = folder + '/' + file
                if os.path.isfile(new_file):
                    self.local_file = self.to_local(new_file)
                    file_ext = new_file.split('.')[-1].lower()

                    if file_ext in self.video:
                        self.files.append(new_file)
                    elif file_ext in self.not_down:
                        self.skip += 1
                    elif self.should(self.local_file):  # check if file exists or not
                        try:
                            if self.count:
                                self.counter()
                            print('copy || ', self.shorten_name(self.local_file.replace(self.local, '')))
                            copy(new_file, self.local_file)
                        except Exception as e:
                            print(e)
                    else:
                        # check if file is complete (zip, rar)
                        self.skip += 1
                        orig_size, comp_size, status = is_incomplete(self.local_file, new_file)
                        if orig_size != comp_size:  # incomplete
                            try:
                                os.unlink(self.local_file)
                                if self.count:
                                    self.counter()
                                print('replace || ', self.shorten_name(self.local_file.replace(self.local, '')))
                                copy(new_file, self.local_file)
                            except Exception as e:
                                print(e)
                        else:  # file is already copied and is complete
                            if self.count:
                                self.counter()
                        print('copied || ', self.shorten_name(self.local_file.replace(self.local, '')))
                else:  # new content in folder
                    self.get_file(new_file) 

    def main(self, kwargs):
        if self.count:
            print('Total files', self.count)


        ## Get all files recursively
        self.make_dirs(self.remote)    # make copies
        self.get_file(self.remote)     # list all files

        if kwargs.get('shuffle'):
            shuffle(self.files)
        else:
            try:
                self.files = sorted(self.files, key=sort_func)
            except Exception as e:
                print('Can\'t sort with custom function\n', str(e))
                self.files = sorted(self.files)
        len_ = len(self.files)

        target = eval(f"self.{kwargs.get('cmd', 'compress')}")

        for i in range(0, len_-1, 2):
            p1 = Process(target=target, args=(self.files[i], kwargs.get('ext', 'mp3')))
            p2 = Process(target=target, args=(self.files[i+1], kwargs.get('ext', 'mp3')))
            p1.start()
            p2.start()
            p1.join()
            p2.join()

        if len_%2:
            p3 = Process(target=target, args=(self.files[-1], "mp3"))
            p3.start()
            p3.join()

        print("Done")

    @staticmethod
    def calc_size(folder):
        return str(utils.readable_size(utils.size(folder)))

    def __str__(self):
        return '''
        Parms  :-
            remote :- From Where | Gdrive url
            local  :- To Where | gdrive url
        '''

    def __repr__(self):
        return '''
        Parms  :-
            remote :- From Where | Gdrive url
            local  :- To Where | gdrive url
        '''


def sort_func( name):
    import re
    regex = re.compile(r'\d+$')
    string = name.split('/')[-1]
    try:
        num = int(regex.findall(string)[0])
    except:
        num = ''
    return num


if __name__ == '__main__':
    import utils
    from utils import encrypt, is_incomplete, convert, get_size
    from removeDups import remove
else:
    from .utils import encrypt, is_incomplete, convert
    from .removeDups import remove
