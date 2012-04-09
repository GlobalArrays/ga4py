"""A way over-simplified SRUMMA matrix multiplication implementation.

Assumes square matrices with the shape as a multiple of the block size.

"""
import mpi4py.MPI
from ga4py import ga
import numpy as np

CHUNK_SIZE = 256
MULTIPLIER = 3
N = CHUNK_SIZE*MULTIPLIER

### assign to 'me' this processor's ID
### assign to 'nproc' how many processors in the world

class Task(object):
    def __init__(self, alo, ahi, blo, bhi, clo, chi):
        self.alo = alo
        self.ahi = ahi
        self.blo = blo
        self.bhi = bhi
        self.clo = clo
        self.chi = chi
    def __repr__(self):
        return "Task(%s,%s,%s,%s,%s,%s)" % (
                self.alo, self.ahi, self.blo, self.bhi, self.clo, self.chi)

def get_task_list(chunk_size, multiplier):
    count = 0
    task_list = [None]*multiplier**3
    for row_chunk in range(multiplier):
        for col_chunk in range(multiplier):
            clo = [ row_chunk   *chunk_size,  col_chunk   *chunk_size]
            chi = [(row_chunk+1)*chunk_size, (col_chunk+1)*chunk_size]
            for i in range(multiplier):
                alo = [ row_chunk   *chunk_size,  i   *chunk_size]
                ahi = [(row_chunk+1)*chunk_size, (i+1)*chunk_size]
                blo = [ i   *chunk_size,  col_chunk   *chunk_size]
                bhi = [(i+1)*chunk_size, (col_chunk+1)*chunk_size]
                task_list[count] = Task(alo, ahi, blo, bhi, clo, chi)
                count += 1
    return task_list

def srumma(g_a, g_b, g_c, chunk_size, multiplier):
    # statically partition the task list among nprocs
    task_list = get_task_list(chunk_size, multiplier)
    ntasks = multiplier**3 // nproc
    start = me*ntasks
    stop = (me+1)*ntasks
    if me+1 == nproc:
        stop += multiplier**3 % nproc
    # the srumma algorithm, more or less
    task_prev = task_list[start]
    ### use a nonblocking get to request first block and nb handle from 'g_a'
    ###     and assign to 'a_prev' and 'a_nb_prev'
    ### use a nonblocking get to request first block and nb handle from 'g_b'
    ###     and assign to 'b_prev' and 'b_nb_prev'
    for i in range(start+1,stop):
        task_next = task_list[i]
        ### use a nonblocking get to request next block and nb handle from 'g_a'
        ###     and assign to 'a_next' and 'a_nb_next'
        ### use a nonblocking get to request next block and nb handle from 'g_b'
        ###     and assign to 'b_next' and 'b_nb_next'
        ### wait on the previoius nb handle for 'g_a'
        ### wait on the previoius nb handle for 'g_b'
        result = np.dot(a_prev,b_prev)
        ### accumulate the result into 'g_c' at the previous block location
        task_prev = task_next
        a_prev,a_nb_prev = a_next,a_nb_next
        b_prev,b_nb_prev = b_next,b_nb_next
    ### wait on the previoius nb handle for 'g_a'
    ### wait on the previoius nb handle for 'g_b'
    ga.nbwait(a_nb_prev)
    ga.nbwait(b_nb_prev)
    result = np.dot(a_prev,b_prev)
    ### accumulate the result into 'g_c' at the previous block location
    ### synchronize

def verify_using_ga(g_a, g_b, g_c):
    g_v = ga.duplicate(g_c)
    ga.gemm(False,False,N,N,N,1,g_a,g_b,0,g_v)
    c = ga.access(g_c)
    v = ga.access(g_v)
    if c is not None:
        val = int(np.abs(np.sum(c-v))>0.0001)
    else:
        val = 0
    val = ga.gop_add(val)
    ga.destroy(g_v)
    return val == 0

def verify_using_np(g_a, g_b, g_c):
    a = ga.get(g_a)
    b = ga.get(g_b)
    c = ga.get(g_c)
    v = np.dot(a,b)
    val = int(np.abs(np.sum(c-v))>0.0001)
    val = ga.gop_add(val)
    return val == 0

if __name__ == '__main__':
    if nproc > MULTIPLIER**3:
        if 0 == me:
            print "You must use less than %s processors" % (MULTIPLIER**3+1)
    else:
        g_a = ga.create(ga.C_DBL, [N,N])
        g_b = ga.create(ga.C_DBL, [N,N])
        g_c = ga.create(ga.C_DBL, [N,N])
        # put some fake data into input arrays A and B
        if me == 0:
            ga.put(g_a, np.random.random(N*N))
            ga.put(g_b, np.random.random(N*N))
        ga.sync()
        if me == 0:
            print "srumma...",
        srumma(g_a, g_b, g_c, CHUNK_SIZE, MULTIPLIER)
        if me == 0:
            print "done"
        if me == 0:
            print "verifying using ga.gemm...",
        ok = verify_using_ga(g_a, g_b, g_c)
        if me == 0:
            if ok:
                print "OKAY"
            else:
                print "FAILED"
        if me == 0:
            print "verifying using np.dot...",
        ok = verify_using_np(g_a, g_b, g_c)
        if me == 0:
            if ok:
                print "OKAY"
            else:
                print "FAILED"
        ga.destroy(g_a)
        ga.destroy(g_b)
        ga.destroy(g_c)
