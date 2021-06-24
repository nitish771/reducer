import os
from multiprocessing import Pool, Process, Value
from random import shuffle
from .utils import encrypt, is_incomplete
from .removeDups import remove


class Compress:

    def __init__(self, remote=None, local=None, res="720",
                delete=False, encrypt_=False, quitIfFolderExists=0):
        self.remote = remote
        self.local = local
        self.encrypt_ = encrypt_
        
        if self.remote is None:
            self.remote = input("Enter Remote URL : ")
        if self.local is None:
            self.local = input("Enter Local URL : ")

        self.top_dir = self.remote.split('/')[-1]        # name of the main folder
        self.local = os.path.join(self.local, self.top_dir)   # local abs path
        self.files = []                                  # files to compress
        self.video = ['mkv', 'mov', 'mp4']
        self.res = res # resolution
        self.not_down = ['vtt']
        self.quitIfFolderExists = quitIfFolderExists
        self.make_dirs(self.remote)                     # make copies
        self.main()                                     # start compressing
        if delete:
            remove(self.local)
        if encrypt_:
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

    def make_dirs(self, folder):
        # Making Directories Copy
        os.chdir(folder)
        os.system('mkdir -p ' +
              self.valid_unix_name(folder.replace(self.remote, self.local)))

        if self.quitIfFolderExists and os.path.exists(
            folder.replace(self.remote, self.local)):
                return

        for dirs in os.listdir(folder):
            if not dirs.split('/')[-1].startswith('.'):
                new_content = folder + '/' + dirs
                if os.path.isdir(new_content):
                    self.make_dirs(new_content)

    def should(self, file_name):
        s = os.path.exists(file_name)
        return not s

    def compress(self, file):
        local_file = file.replace(self.remote, self.local)
        saveas = self.valid_unix_name(local_file)
        file_name = file.replace(self.remote, '')

        # if exists check for size
        if os.path.exists(local_file):
            orig_size, comp_size, status = is_incomplete(local_file, file)
            if status:  # incomplete
                print(saveas.replace(self.local, ''))
                print(f'AC/CS {orig_size//1024**2}MB/{comp_size//1024**2}MB')
                os.unlink(local_file)
        else:
            ffmpeg_cmd = "ffmpeg -i " + self.valid_unix_name(file) + "\
                    -b:a 64k -ac 1 -vf scale=\"'w=-2:h=trunc(min(ih," + str(self.res) + ")/2)*2'\" \
                    -crf 32 -profile:v baseline -level 3.0 -preset slow -v error -strict -2 -stats \
                    -y -r 20 " + saveas
            print('compressing\t', file_name)
            os.system(ffmpeg_cmd + '  >  /dev/null')
            print('Compressed\t', file_name)

    def get_file(self, folder):
        os.chdir(folder)
        for file in os.listdir(folder):
            if not file.startswith('.'):
                new_file = folder + '/' + file
                if os.path.isfile(new_file):
                    local_file = new_file.replace(self.remote, self.local)
                    saveas = self.valid_unix_name(local_file)
                    file_ext = new_file.split('.')[-1].lower()
        
                    if file_ext in self.video:
                        self.files.append(new_file)
                    elif file_ext in self.not_down:
                        pass
                    elif self.should(local_file):                
                        print('copy :  ', new_file.replace(self.remote, ''))
                        os.system('cp -r ' + self.valid_unix_name(new_file) + ' ' + saveas)
                else:
                    self.get_file(new_file) 

    def main(self):
        pool = Pool()

        ## Get all files recursively
        self.get_file(self.remote)
        shuffle(self.files)
        pool.map(self.compress, self.files)
        print("Done")
