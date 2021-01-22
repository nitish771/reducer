import os
from itertools import permutations


files = []


def getFiles(fold):
	global files
	for i in os.listdir(fold):
		new = fold+'/'+i
		if os.path.isfile(new):
			files.append(new)
		else:
			getFiles(new)


def isDup(f1, f2):
	f1_ext = f1.split('.')[-1]
	f2_ext = f2.split('.')[-1]
	
	if f1_ext == f2_ext:
		return f2 in [".".join(f1.split('.')[:-1])+'('+str(i)+').'+f1_ext for i in range(1, 6)]
	return 0


def remove(fold):
	global files
	getFiles(fold)
	for i in permutations(files, 2):
		if isDup(*i):
			print('removing ', i[1])
			os.system('rm -rf "' + i[1] + '"')
