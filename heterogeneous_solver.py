__author__ = "Jerome Thai"
__email__ = "jerome.thai@berkeley.edu"

import numpy as np
from scipy import special as sp


def gauss_seidel(graphs, demands, solver, max_cycles=10, max_iter=100, \
    by_origin=False, q=10, display=0):
    # we are given a list of graphs and demands that are specific for different types of players
    # the gauss-seidel scheme updates cyclically for each type at a time

    # prepare arrays for assignment by type
    types = len(graphs)
    links = int(np.max(graphs[0][:,0])+1)
    fs = np.zeros((links,types),dtype="float64")
    g = np.copy(graphs[0])

    for cycle in range(max_cycles):
        if display >= 1: print 'cycle:', cycle
        for i in range(types):
            # construct graph with updated latencies
            shift = np.sum(fs[:,range(i)+range(i+1,types)], axis=1)
            shift_graph(graphs[i], g, shift)
            # update flow assignment for this type
            fs[:,i] = solver(g, demands[i], max_iter=max_iter, q=q, display=display)
    return fs


def jacobi(graphs, demands, solver, max_cycles=10, max_iter=100, \
    by_origin=False, q=10, display=0):
    # given a list of graphs and demands specific for different types of players
    # the jacobi scheme updates simultenously for each type at the same time

    # prepare arrays for assignment by type
    types = len(graphs)
    links = int(np.max(graphs[0][:,0])+1)
    fs = np.zeros((links,types),dtype="float64")
    updates = np.copy(fs)
    g = np.copy(graphs[0])

    for cycle in range(max_cycles):
        if display >= 1: print 'cycle:', cycle
        for i in range(types):
            # construct graph with updated latencies
            shift = np.sum(fs[:,range(i)+range(i+1,types)], axis=1)
            shift_graph(graphs[i], g, shift)
            # update flow assignment for this type
            updates[:,i] = solver(g, demands[i], max_iter=max_iter, q=q, display=display)
        # batch update
        fs = np.copy(updates)
    return fs


def shift_graph(graph1, graph2, d):
    # given a graph with polynomial latency functions sum_k a_k x^k and shift d
    # return a graph with updated latencies sum_k a_k (x+d)^k
    links = graph1.shape[0]
    for i in range(links):
        graph2[i,3:] = shift_polynomial(graph1[i,3:], d[i])
    return graph2


def shift_polynomial(coef, d):
    # given polynomial sum_k a_k x^k -> sum_k a_k (x+d)^k
    coef2 = np.zeros(5,dtype="float64")
    for i in range(5):
        for j in range(i,5):
            coef2[i] = coef2[i] + coef[j] * (d**(j-i)) * sp.binom(j,i)
    return coef2


# def shift_graph_2(graph1, graph2, d):
#     # numpy matrix implementation of shift_graph
#     A = np.zeros((5,5),dtype="float64")
#     for i in range(5):
#         for j in range(i,5):
#             A[j,i] = (d**(j-i)) * sp.binom(j,i)
#     graph2[:,3:] = graph2[:,3:].dot(A)
#     return graph2