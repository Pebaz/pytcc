"""
pytcc is a very simple wrapper around
libtcc, using ctypes. Requires Python 3.0
or newer.
"""

import ctypes

__all__ = ['TCCState', 'TCC_OUTPUT_MEMORY', 'TCC_OUTPUT_EXE', 'TCC_OUTPUT_DLL',
		'TCC_OUTPUT_OBJ', 'TCC_OUTPUT_PREPROCESS']

# constants for TCCState.set_output_type()
TCC_OUTPUT_MEMORY = 0
TCC_OUTPUT_EXE    = 1
TCC_OUTPUT_DLL    = 2
TCC_OUTPUT_OBJ    = 3
TCC_OUTPUT_PREPROCESS = 4

# constants for TCCState.relocate()
TCC_RELOCATE_AUTO = ctypes.c_void_p(1)

# internal typedefs
ERROR_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_char_p)

# libtcc DLL handle
libtcc = ctypes.cdll.LoadLibrary('libtcc.so')

# set return type and argument types for all functions in libtcc
tcc_funcs = {
	'tcc_new':             (ctypes.c_void_p,),
	'tcc_delete':          (None, ctypes.c_void_p,),
	
	# set up context
	'tcc_set_lib_path':    (None, ctypes.c_void_p, ctypes.c_char_p,),
	'tcc_set_error_func':  (None, ctypes.c_void_p, ctypes.c_void_p, ERROR_CALLBACK,),
	'tcc_set_options':     (ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p,),
	
	# preprocessor
	'tcc_add_include_path':    (ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p,),
	'tcc_add_sysinclude_path': (ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p,),
	'tcc_define_symbol':       (None, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p,),
	'tcc_undefine_symbol':     (None, ctypes.c_void_p, ctypes.c_char_p,),
	
	# compiling
	'tcc_add_file':        (ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p,),
	'tcc_compile_string':  (ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p,),
	
	# linking
	'tcc_set_output_type': (ctypes.c_int, ctypes.c_void_p, ctypes.c_int,),
	'tcc_add_library_path':(ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p,),
	'tcc_add_library':     (ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p,),
	'tcc_add_symbol':      (ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,),
	'tcc_output_file':     (ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p,),
	'tcc_run':             (ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_char_p),),
	'tcc_relocate':        (ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,),
	'tcc_get_symbol':      (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p,),
}
for func, types in tcc_funcs.items():
	f = getattr(libtcc, func)
	f.restype = types[0]
	f.argtypes = types[1:]
del tcc_funcs

# generic error class
class TCCError(Exception): pass

class TCCState(object):
	"""Wrapper around the TCCState struct in libtcc."""
	
	def __init__(self):
		"""Create a new TCCState object."""
		self.__ptr = libtcc.tcc_new()
		self.__last_error = None
		
		# set error callback
		self.__error_callback = ERROR_CALLBACK(self._on_error)
		libtcc.tcc_set_error_func(self.__ptr, None, self.__error_callback)
	
	def __del__(self):
		"""Delete TCCState when collected by garbage collector."""
		libtcc.tcc_delete(self.__ptr)
	
	def _str(self, obj):
		"""Utility function: encode all objects as ASCII."""
		if isinstance(obj, (bytes, bytearray)):
			return bytes(obj)
		else:
			return str(obj).encode('ascii')
	
	def _on_error(self, opaque, message):
		"""Utility function: store latest error."""
		self.__last_error = message.decode('ascii')
	
	@property
	def last_error(self):
		"""Get last error message (or None if no error has occured)."""
		return self.__last_error
	
	# --------------
	# set up context
	
	def set_lib_path(self, path):
		"""Set CONFIG_TCCDIR at runtime."""
		libtcc.tcc_set_lib_path(self.__ptr, self._str(path))
	
	def set_options(self, options):
		"""Set options as from command line (multiple supported)."""
		r = libtcc.tcc_set_options(self.__ptr, self._str(options))
		if r == -1: raise TCCError(self.__last_error)
	
	# ------------
	# preprocessor
	
	def add_include_path(self, pathname):
		"""Add include path."""
		return libtcc.tcc_add_include_path(self.__ptr, self._str(pathname))
		if r == -1: raise TCCError(self.__last_error)
	
	def add_sysinclude_path(self, pathname):
		"""Add system include path."""
		return libtcc.tcc_add_sysinclude_path(self.__ptr, self._str(pathname))
		if r == -1: raise TCCError(self.__last_error)
	
	def define_symbol(self, sym, value=b''):
		"""Define preprocessor symbol 'sym'. Can put optional value."""
		libtcc.tcc_define_symbol(self.__ptr, self._str(sym), self._str(value))
		if r == -1: raise TCCError(self.__last_error)
	
	def undefine_symbol(self, sym):
		"""Undefine preprocessor symbol 'sym'."""
		libtcc.tcc_undefine_symbol(self.__ptr, self._str(sym))
		if r == -1: raise TCCError(self.__last_error)
	
	# ---------
	# compiling
	
	def add_file(self, filename):
		"""Add a file (C file, DLL, object, library, ld script)."""
		r = libtcc.tcc_add_file(self.__ptr, self._str(filename))
		if r == -1: raise TCCError(self.__last_error)
	
	def compile_string(self, buf):
		"""Compile a string containing C source."""
		r = libtcc.tcc_compile_string(self.__ptr, self._str(buf))
		if r == -1: raise TCCError(self.__last_error)
	
	# -------
	# linking
	
	def set_output_type(self, output_type):
		"""Set output type. Must be called before any compilation."""
		r = libtcc.tcc_set_output_type(self.__ptr, output_type)
		if r == -1: raise TCCError(self.__last_error)
	
	def add_library_path(self, pathname):
		"""Add to library path."""
		r = libtcc.tcc_add_library_path(self.__ptr, self._str(pathname))
		if r == -1: raise TCCError(self.__last_error)
	
	def add_library(self, libraryname):
		"""Add library."""
		r = libtcc.tcc_add_library(self.__ptr, self._str(libraryname))
		if r == -1: raise TCCError(self.__last_error)
	
	def add_symbol(self, name, val):
		"""Add symbol to the compiled program."""
		r = libtcc.tcc_add_symbol(self.__ptr, self._str(name), val)
		if r == -1: raise TCCError(self.__last_error)
	
	def output_file(self, filename):
		"""Output an executable, library or object file. DO NOT CALL relocate() before."""
		r = libtcc.tcc_output_file(self.__ptr, self._str(filename))
		if r == -1: raise TCCError(self.__last_error)
	
	def run(self, *args):
		"""Link and run main() function and return its value. DO NOT CALL relocate() before."""
		if not args:
			args = [b'']
		else:
			args = [ self._str(a) for a in args ]
		
		argc = len(args)
		argv = (ctypes.c_char_p * argc)(*args)
		
		return libtcc.tcc_run(self.__ptr, argc, argv)
	
	def relocate(self, ptr=TCC_RELOCATE_AUTO):
		"""Do all relocations (needed before using get_symbol()).
		Possible values for 'ptr':
		 - TCC_RELOCATE_AUTO : Allocate and manage memory internally
		 - None              : Return required memory size for the step below
		 - memory address    : Copy code to the memory passed by the caller (see get_bytes())
		"""
		r = libtcc.tcc_relocate(self.__ptr, ptr)
		if r == -1: raise TCCError(self.__last_error)
		return r
	
	def get_bytes(self):
		"""Reallocate into a Python byte object."""
		size = libtcc.tcc_relocate(self.__ptr, None)
		if size == -1:
			raise TCCError(self.__last_error)
		
		buf = ctypes.create_string_buffer(size)
		r = libtcc.tcc_relocate(self.__ptr, buf)
		if r == -1:
			raise TCCError(self.__last_error)
		return bytes(buf)
	
	def get_symbol(self, name):
		"""Return symbol pointer or None if none is found."""
		return libtcc.tcc_get_symbol(self.__ptr, self._str(name))
