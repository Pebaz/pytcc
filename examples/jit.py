import time, ctypes, sys
import pytcc as pcc

program =b"""
int foobar(int n)
{
	int i = 0;
	for (int r = 0; r < n; r++)
	{
		i += r;
	}
    return i;
}

// Needed to appease TCC:
int main() { }
"""

def py_foobar(n):
	""
	i = 0
	for r in range(n):
		i += r
	return i

jit_code = pcc.TCCState()
jit_code.add_include_path('C:/Python37/include')
jit_code.add_library_path('C:/Python37')
jit_code.add_library('python37')
jit_code.compile_string(program)
jit_code.relocate()

rettype = ctypes.c_int
foobar_proto = ctypes.CFUNCTYPE(rettype, ctypes.c_int)
foobar = foobar_proto(jit_code.get_symbol('foobar'))

rettype = ctypes.py_object
pop_proto = ctypes.CFUNCTYPE(rettype)
pop = pop_proto(jit_code.get_symbol('pop'))

print(pop(133))


times = 3000  # Call the C/Python function this many times

start = time.time_ns()
for i in range(times):
	py_foobar(times)
py_end = (time.time_ns() - start) / 1000000000
print(f'Took {py_end}s to complete.')

start = time.time_ns()
for i in range(times):
	foobar(times)
c_end = (time.time_ns() - start) / 1000000000
print(f'Took {c_end}s to complete.')

print(f'The C version is around {int(py_end / c_end)} times faster.')
