import os


class Compress:

    def __init__(self, remote, local):
        self.remote = remote
        self.top_dir = self.remote.split('/')[-1]
        self.root = self.remote
        self.local = os.path.join(local, self.top_dir)
        self.make_dirs(self.remote)

    def valid_unix_name(self, name):
        return '"'+name+'"'

    def make_dirs(self, folder, quitIfMainFolderExists=1):
        os.chdir(folder)

        if quitIfMainFolderExists and os.path.exists(folder.replace(self.root, self.local)):
            print('exists', folder, (folder.replace(self.root, self.local)))
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
        return file_name.replace(self.root, self.local) not in self.remote.replace(self.root, self.local)

    def compress(self, file, res="720"):
        saveas = file.replace(self.root, self.local)
        print(saveas, 'saveas')
        ffmpeg_cmd = "ffmpeg -i " + self.valid_unix_name(file) + "\
              -b:a 64k -ac 1 -vf scale=\"'w=-2:h=trunc(min(ih," + str(res) + ")/2)*2'\" \
              -crf 32 -profile:v baseline -level 3.0 -preset slow -v error -strict -2 -stats \
              -y -r 20 " + self.valid_unix_name(saveas)
        print(ffmpeg_cmd)



