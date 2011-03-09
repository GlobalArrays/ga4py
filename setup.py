import os
from subprocess import Popen, PIPE
import sys

from distutils.core import setup
from distutils.extension import Extension
from distutils.spawn import find_executable

# numpy is required -- attempt import
try:
    import numpy
except ImportError:
    print "numpy is required"
    raise

# cython is optional -- attempt import
cythonize = False
try:
    from Cython.Distutils import build_ext
    cythonize = True
except:
    pass

# need to find 'ga-config.x' to gather how GA was configured
ga_config = find_executable("ga-config.x", None)
if not ga_config:
    raise ValueError, "ga-config.x not found in path -- required"
p = Popen("%s --cppflags" % ga_config, shell=True, stdout=PIPE, stderr=PIPE,
        close_fds=True)
ga_cppflags,ignore = p.communicate()
p = Popen("%s --ldflags" % ga_config, shell=True, stdout=PIPE, stderr=PIPE,
        close_fds=True)
ga_ldflags,ignore = p.communicate()
p = Popen("%s --clibs" % ga_config, shell=True, stdout=PIPE, stderr=PIPE,
        close_fds=True)
ga_clibs,ignore = p.communicate()

# On osx, '-framework Accelerate' doesn't link the actual LAPACK and BLAS
# libraries. Locate them manually if GA was configured to use them.
linalg_include = []
linalg_library = []
linalg_lib = []
if 'Accelerate' in ga_clibs or 'vecLib' in ga_clibs:
    path = "/System/Library/Frameworks/Accelerate.framework/Frameworks/vecLib.framework/Versions/A"
    linalg_include = []
    if os.path.exists(path):
        linalg_library = [path]
        linalg_lib = ["LAPACK","BLAS"]
    # remove '-framework Accelerate' from flags
    ga_clibs = ga_clibs.replace("-framework","")
    ga_clibs = ga_clibs.replace("Accelerate","")
    ga_clibs = ga_clibs.replace("vecLib","")

include_dirs = [numpy.get_include()]
library_dirs = []
libraries = []

# add the GA stuff
for dir in ga_cppflags.split():
    dir = dir.strip()
    include_dirs.append(dir.replace("-I",""))
for dir in ga_ldflags.split():
    dir = dir.strip()
    library_dirs.append(dir.replace("-L",""))
for part in ga_clibs.split():
    part = part.strip()
    if '-L' in part:
        library_dirs.append(part.replace("-L",""))
    elif '-l' in part:
        libraries.append(part.replace("-l",""))

include_dirs.extend(linalg_include)
library_dirs.extend(linalg_library)
libraries.extend(linalg_lib)

ga_ga_sources = ["ga/ga.c"]
if cythonize:
    ga_ga_sources = ["ga/ga.pyx"]

include_dirs.append(".")

ext_modules = [
    Extension(
        name="ga.ga",
        sources=ga_ga_sources,
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        libraries=libraries
    )
]

cmdclass = {}
if cythonize:
    cmdclass = {"build_ext":build_ext}

setup(
    name = "Global Arrays",
    packages = ["ga"],
    ext_modules = ext_modules,
    cmdclass = cmdclass,
)
