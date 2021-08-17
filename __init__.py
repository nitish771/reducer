__title__ = "reducer"
__author__ = "Nitish Kumar"
__license__ = "MIT License"
__copyright__ = "Copyright 2021"


from .__main__ import Compress
from .removeDups import remove
from .utils import encrypt, decrypt, convert

__all__ = ["Compress", "down", "extract", "remove", "convert", "utils", "encrypt", "decrypt"]
