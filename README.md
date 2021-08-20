# How It works

First of all clone the repository using this command
---

`$git clone https://github.com/nitish771/reducer`


Now import it inside your python/jupyter notebook
---

`$ import reducer as r`

Instanciate the class
---

`$ r.Compress(remote='/path/to/remote/directory/which/you/want/to/compress', local='/where/to/save', **kwargs)`

### Keyword Arguments

You can pass following keyword arguments

Args|use|
----|----|
res:int|sets compression resolution|
cmd:(convert or compress)|what to do|
quitIfFolderExists:bool|if local folder exists it will quit immediately|
encrypt:bool|after compression it will compress entire compressed folder with shift cipher|
shuffle:bool|shuffle compresssion|
delete_dup:bool|remove duplicates after compression|
hidden:bool|count hidden files too (e.g. - .git)|
