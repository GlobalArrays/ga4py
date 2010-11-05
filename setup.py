from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import os

ga_install = '/home/d3n000/ga/ga-dev/bld_openmpi_shared'
if not os.path.exists(ga_install):
    ga_install = "/Users/d3n000/ga/ga-dev/bld_openmpi_shared"
if not os.path.exists(ga_install):
    raise ValueError, 'cannot locate GA installation'

try:
    import numpy
except ImportError:
    print "numpy is required"
    raise

numpy_include = numpy.get_include()
if os.uname()[0] == 'Darwin':
    linalg_include = []
    linalg_library = ["/System/Library/Frameworks/Accelerate.framework/Frameworks/vecLib.framework/Versions/A"]
    linalg_lib = ["LAPACK","BLAS"]
else:
    linalg_include = []
    linalg_library = []
    linalg_lib = []

include_dirs = [ga_install+"/include",numpy_include]
library_dirs = [ga_install+"/lib"]
libraries = ["ga"]

for dir in linalg_include:
    include_dirs.append(dir)
for dir in linalg_library:
    library_dirs.append(dir)
for lib in linalg_lib:
    libraries.append(lib)

ext_modules = [
    Extension(
        name="ga",
        sources=["ga.pyx"],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        libraries=libraries
    )
]

setup(
        name = "Global Arrays",
        cmdclass = {"build_ext": build_ext},
        ext_modules = ext_modules
)
