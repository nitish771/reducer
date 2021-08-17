import os
import sys
from multiprocessing import Process, Value
from random import shuffle
from shutil import copy


CPU_COUNT = os.cpu_count()


class Compress:

    def __init__(self, remote=None, local=None, **kwargs):
        self.kwargs = kwargs
        self.remote = remote
        self.local = local
        # Semaphore to count files compressed
        self.value = Value('i', 0)

        if self.remote is None:
            self.remote = input("Enter Remote URL : ")
        if self.local is None:
            self.local = input("Enter Local URL : ")

        self.quitIfFolderExists = kwargs.get('quitIfFolderExists')
        self.encrypt_ = kwargs.get('encrypt_')
        self.skip = 0

        self.top_dir = self.remote.split('/')[-1]        # name of the main folder
        self.local = os.path.join(self.local, self.top_dir)   # local abs path
        self.files = []                                  # files to compress
        self.video = ['mkv', 'mov', 'mp4']
        
        # resolution
        if kwargs.get('res'):
            self.res = kwargs.get('res')
        else:
            self.res = '720'

        self.not_down = ['vtt']

        if kwargs.get('count', 1):
            self.count = self.count_files(self.remote,
                hidden=kwargs.get('hidden'))

        self.main(kwargs)                    # start compressing

        if kwargs.get('delete_dup'):
            remove(self.local)

        if kwargs.get('encrypt_'):
            encrypt(self.local)

    def __str__(self):
        return '''
Parms  :-
    remote :- From Where | Gdrive url
    local  :- To Where | gdrive url
'''

    def add_not_down(self, xt):
        self.not_down.append(xt)

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
            if os.path.isfile(file):
                total += 1
            elif kwargs.get('hidden'):
                total += self.count_files(folder+'/'+file)
            elif not file.startswith('.'):
                total += self.count_files(folder+'/'+file)
        return total

    def counter(self):
        with self.value.get_lock():
                self.value.value += 1
        print('T', self.count, '-C', self.value.value, '-S', self.skip,
            '-R', (self.count-self.value.value-self.skip), ' || ', end='', sep='')

    def make_dirs(self, folder):
        # Making Directories Copy
        os.chdir(folder)
        os.system('mkdir -p ' +
              self.valid_unix_name(self.to_local(folder)))

        if self.quitIfFolderExists and os.path.exists(self.to_local(folder)):
                print('Quitting Folder Exists', folder)
                sys.exit()

        for dirs in os.listdir(folder):
            if not dirs.split('/')[-1].startswith('.'):
                new_content = folder + '/' + dirs
                if os.path.isdir(new_content):
                    self.make_dirs(new_content)

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
            orig_size, comp_size, status = is_incomplete(local_file, file)
            if status:  # incomplete
                print(saveas.replace(self.local, ''))
                print(f'AC/CS {orig_size//1024**2}MB/{comp_size//1024**2}MB')
                os.unlink(local_file)
                self.compress(file)
        else:
            ffmpeg_cmd = "ffmpeg -i " + self.valid_unix_name(file) + "\
                    -b:a 64k -ac 1 -vf scale=\"'w=-2:h=trunc(min(ih," + str(self.res) + ")/2)*2'\" \
                    -crf 32 -profile:v baseline -level 3.0 -preset slow -v error -strict -2 -stats \
                    -y -r 20 " + saveas
            print('compressing\t', self.shorten_name(self.shorten_name(file_name)))
            os.system(ffmpeg_cmd + '  >  /dev/null')

            if self.count:
                self.counter()

            print('Compressed\t', self.shorten_name(file_name.split('/')[-1]))

    def convert(self, file, ext="mp3"):
        file_ext = file.split('.')[-1]
        saveas = (file.replace(file_ext, ext)).replace(self.remote, self.local)
        # print(saveas)
        convert(file, saveas=saveas, to=ext)

    def get_file(self, folder):
        os.chdir(folder)
        for file in os.listdir(folder):
            if not file.startswith('.'):
                new_file = folder + '/' + file
                if os.path.isfile(new_file):
                    local_file = self.to_local(new_file)
                    file_ext = new_file.split('.')[-1].lower()

                    if file_ext in self.video:
                        self.files.append(new_file)
                    elif file_ext in self.not_down:
                        self.skip += 1
                    elif self.should(local_file):
                        try:
                            print('copy : ', self.shorten_name(new_file.replace(self.remote, '')))
                            print(new_file, local_file)
                            copy(new_file, local_file)
                            self.skip += 1
                            if self.count:
                                self.counter()
                        except Exception as e:
                            print(e)
                            print(e)
                    else:
                        self.skip += 1
                else:
                    self.get_file(new_file) 

    def main(self, kwargs):

        ## Get all files recursively
        self.make_dirs(self.remote)    # make copies
        self.get_file(self.remote)     # list all files

        if kwargs.get('shuffle'):
            shuffle(self.files)
        else:
            try:
                self.files = sorted(self.files, key=sort_func)
                print(self.files)
            except Exception as e:
                print('Can\'t sort with custom function\n', str(e))
                self.files = sorted(self.files)
        len_ = len(self.files)

        if self.count:
            print('Total files', self.count)

        target = eval(f"self.{kwargs.get('cmd', 'compress')}")

        for i in range(0, len_-1, 2):
            p1 = Process(target=target, args=(self.files[i], kwargs.get('ext', 'mp3')))
            p2 = Process(target=target, args=(self.files[i+1], kwargs.get('ext', 'mp3')))
            p1.start()
            p2.start()
            p1.join()
            p2.join()

        if len_%2:
            if kwargs.get('ext'):
                p3 = Process(target=target, args=(self.files[-1], "mp3"))
            else:
                p3 = Process(target=target, args=(self.files[-1], ))
            p3.start()
            p3.join()

        print("Done")


def sort_func( name):
    import re
    regex = re.compile(r'\d+$')
    string = name.split('/')[-1].split('.')[0]
    num = int(regex.findall(string)[0])
    return num


if __name__ == '__main__':
    from utils import encrypt, is_incomplete, convert
    from removeDups import remove
else:
    from .utils import encrypt, is_incomplete, convert
    from .removeDups import remove
