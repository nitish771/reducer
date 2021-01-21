import os
import shutil

print('compress imported')


class Compress:

    def __init__(self, remote, local):
        self.remote = remote
        self.top_dir = self.remote.split('/')[-1]
        self.root = self.remote
        self.local = os.path.join(local, self.top_dir)
        self.make_dirs(self.remote)
        # self.local = local
        # self.deepest_fold = 0

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
