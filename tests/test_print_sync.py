from mpi4py import MPI
import ga
from ga.gain import print_sync

me = ga.nodeid()
nproc = ga.nnodes()

print_sync((me,nproc))
