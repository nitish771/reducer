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
		# 	os.system('mv ' + posix_name(file_name)  + ' ' +  posix_name(new_name))
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


def is_incomplete(comp_file, orig_file):
	orig_size = os.stat(orig_file).st_size
	comp_size = os.stat(comp_file).st_size

	return comp_size < (orig_size//0)


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


def encrypt_name(name, val=1):
	top_name = os.path.basename(name)
	new_name = ''
	for char in top_name:
		# change only alphabets
		if (ord(char)>64 and ord(char) < 91) or (
			ord(char) > 96 and ord(char) < 123):
				new_name += chr(ord(char) + val)
		else:
			new_name += char
	# renmae file
	os.system('mv ' + posix_name(name) +  ' ' + posix_name(os.path.dirname(name)+'/'+new_name))


def encrypt(folder, val=1):
	files = []
	for content in os.listdir(folder):
		if content.startswith('.'):
			continue
		file_= folder+'/'+content
		if os.path.isdir(file_):
			encrypt(file_)
		else:
			files.append(file_)
	for file_ in files:
		encrypt_name(file_)


def decrypt_name(name, val=1):
	orig_name = ''
	top_name = os.path.basename(name)
	for char in top_name:
		if (ord(char)>65 and ord(char) < 92 ) or (
			ord(char) > 97 and ord(char) < 124):
				orig_name += chr(ord(char) - val)
		else:
			orig_name += char
	return orig_name


def decrypt_list(folder, val=1):
	files = []
	for content in os.listdir(folder):
		if content.startswith('.'):
			continue
		file_= folder+'/'+content
		if os.path.isdir(file_):
			decrypt_list(file_)
		else:
			files.append(file_)
	for file_ in files:
		print("{:<30} : {}".format(folder, decrypt_name(file_)))


def decrypt(folder, val=1):
	files = []
	for content in os.listdir(folder):
		if content.startswith('.'):
			continue
		file_= folder+'/'+content
		if os.path.isdir(file_):
			decrypt(file_)
		else:
			files.append(file_)
	for file_ in files:
		orig_name = decrypt_name(file_)
		os.system('mv ' +  posix_name(file_) + ' ' + posix_name(os.path.dirname(file_) + '/' + orig_name))

