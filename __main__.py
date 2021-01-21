import os
from multiprocessing import Pool
from random import shuffle


class Compress:

    def __init__(self, remote, local, res="720"):
        self.remote = remote
        self.top_dir = self.remote.split('/')[-1]
        self.root = self.remote
        self.local = os.path.join(local, self.top_dir)
        self.files = []
        self.video = ['mkv', 'mov', 'mp4']
        self.res = res
        self.not_down = ['srt', 'vtt']
        self.make_dirs(self.remote)
        self.main()


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


    def make_dirs(self, folder, quitIfMainFolderExists=1):
        os.chdir(folder)

        if quitIfMainFolderExists and os.path.exists(folder.replace(self.root, self.local)):
            print('exists', folder.replace(self.root, self.local))
            return

        # print(folder)
        for dirs in os.listdir(folder):
            new_content = folder + '/' + dirs
            if os.path.isdir(new_content):
                self.make_dirs(new_content)
                os.system('mkdir -p ' +
                          self.valid_unix_name(new_content.replace(self.root, self.local)))


    def should(self, file_name):
        # file_name = remote file name -> replace remote with local
        file_name = file_name.replace(self.root, self.local)
        print(file_name)
        return not os.path.exists(file_name.replace(self.root, self.local)) # not in self.remote.replace(self.root, self.local)


    def compress(self, file):
        saveas = self.valid_unix_name(file.replace(self.root, self.local))
        # print(saveas, 'saveas')
        file_ext = file.split('.')[-1]
        if self.should(file):
            if file_ext in self.video:
                ffmpeg_cmd = "ffmpeg -i " + self.valid_unix_name(file) + "\
                      -b:a 64k -ac 1 -vf scale=\"'w=-2:h=trunc(min(ih," + str(self.res) + ")/2)*2'\" \
                      -crf 32 -profile:v baseline -level 3.0 -preset slow -v error -strict -2 -stats \
                      -y -r 20 " + saveas
                print('compressing\t', file.split('/')[-1])
                os.system(ffmpeg_cmd + '  >  /dev/null')
            elif file_ext not in self.not_down:
                os.system('cp ' + self.valid_unix_name(file) + ' ' + saveas)
            print('Done ', file.split('/')[-1])
        else:
        	print('exists', file)


    def get_file(self, folder):
        os.chdir(folder)
        # print(folder)
        for file in os.listdir(folder):
            new_file = os.path.join(folder, file)
            if os.path.isfile(new_file):
                self.files.append(new_file)
            else:
                self.get_file(new_file)


    def main(self):
        pool = Pool()

        ## Get all files recursively
        self.get_file(self.remote)
        shuffle(self.files)
        pool.map(self.compress, self.files)

