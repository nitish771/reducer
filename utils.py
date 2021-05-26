import os
import re
from itertools import combinations
import string


def download(url, loc=None):
	"""Download files using link
	Args:
		url : str (link)
		loc : str (path to save)
	"""
	if loc :
		os.chdir(loc)
	os.system('wget -c ' + url)


def copy_to(from_, to="/content/drive/MyDrive/Courses", delete=False):
	"""copy folders]
	Args:
		from_  : str (source path )
		to     : str (dest path)
		delete : bool (if True it move files)
	"""
	if delete:
		os.system('mv "{}" "{}" '.format(from_, to))
	else:
		os.system('cp -r "{}" "{}" '.format(from_, to))


def posix_name(name):
	"""return space seperated string into closed double quotes"""
	return f'"{name}"'


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
			print('renaming', posix_name(file_name), posix_name(os.path.join(cur_dir, new_name)))
		# 	os.system('mv ' + posix_name(file_name)  + ' ' +  posix_name(new_name))
	except Exception as e:
		print('error in renaming', e)


def rename_files(folder=None, *user_ids):
	print(folder)
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


def is_dup(file1, file2):
	criteria1 = (os.path.getsize(file1) == os.path.getsize(file2)) # equal size
	copy_file1 = file1
	copy_file2 = file2
	
	file1 = ".".join(file1.split('/')[-1].split('.')[:-1])
	file2 = ".".join(file2.split('/')[-1].split('.')[:-1])


	if (file1 in file2) and criteria1:
		return copy_file2 # file2 is copy
	elif criteria1 and file2 in file1: # len of file1 > file2
		return copy_file1 # file1 is copy


def delete_dups(folder):
	files = []
	deletable = []
	for dir_ in os.listdir(folder):
		new_content = os.path.join(folder, dir_)
		if os.path.isdir(new_content):
			delete_dups(new_content)
		else:
			files.append(new_content)
	for perm in combinations(files, 2): # Call the function for one folder
		dup_file = is_dup(*list(perm))
		if dup_file:
			deletable.append(dup_file)
	for dup_file in deletable:
		print('deleting', dup_file, sep='\n')
		os.system('rm ' + posix_name(dup_file))


def encrypt_name(name, val=1):
	top_name = os.path.basename(name)
	new_name = ''
	print('name', name)
	for char in top_name:
		if (char not in string.digits) and (
			char not in string.punctuation):
			new_name += chr(ord(char)+val)
		else:
			new_name += char
	os.system('mv ' + posix_name(name) +  ' ' + posix_name(os.path.dirname(name)+'/'+new_name))


def encrypt(folder, val=1):
	files = []
	print(folder)
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
		if (char not in string.digits) and (
			char not in string.punctuation):
				orig_name += chr(ord(char)-val)
		else:
			orig_name += char
	os.system('mv ' +  posix_name(name) + ' ' + posix_name(os.path.dirname(name)+'/'+orig_name))


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
		decrypt_name(file_)
