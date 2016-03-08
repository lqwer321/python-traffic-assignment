__author__ = "Jerome Thai, Nicolas Laurent-Brouty"
__email__ = "jerome.thai@berkeley.edu, nicolas.lb@berkeley.edu"


'''
Scripts for the I-210 sketch
'''

from process_data import extract_features, process_links, geojson_link, \
    process_trips, process_net, process_node, array_to_trips, process_results,output_file
# from frank_wolfe import solver, solver_2, solver_3
from frank_wolfe_2 import solver, solver_2, solver_3
import numpy as np
from metrics import average_cost, cost_ratio, cost, save_metrics
# from heterogeneous_solver import gauss_seidel, jacobi
from multi_types_solver import gauss_seidel


def load_I210():
    net = np.loadtxt('data/I210_net.csv', delimiter=',', skiprows=1)
    demand = np.loadtxt('data/I210_od.csv', delimiter=',', skiprows=1)
    node = np.loadtxt('data/I210_node.csv', delimiter=',', skiprows=1)
    geometry = extract_features('data/I210Sketch_net.csv')
    net[:,1] = net[:,1]-1
    net[:,2] = net[:,2]-1
    demand[:,0] = demand[:,0]-1
    demand[:,1] = demand[:,1]-1
    demand = np.reshape(demand[0,:], (1,3))
    return net, demand, node, geometry


def process_I210_net():
    process_net('data/I210Sketch_net.csv', 'data/I210_net.csv')


def frank_wolfe_on_I210():
    '''
    Frank-Wolfe on I210
    '''    
    graph = np.loadtxt('data/I210_net.csv', delimiter=',', skiprows=1)
    demand = np.loadtxt('data/I210_od.csv', delimiter=',', skiprows=1)
    demand[:,2] = 1. * demand[:,2] / 4000 
    # run solver
    f = solver_3(graph, demand, max_iter=1000, q=50, display=1, stop=1e-2)
    # display cost
    for a,b in zip(cost(f, graph), f*4000): print a,b
    # visualization
    node = np.loadtxt('data/I210_node.csv', delimiter=',', skiprows=1)
    # extract features: 'capacity', 'length', 'fftt'
    feat = extract_features('data/I210Sketch_net.csv')
    ratio = cost_ratio(f, graph)
    # merge features with the cost ratios
    features = np.zeros((feat.shape[0],4))
    features[:,:3] = feat
    features[:,3] = ratio
    # join features with (lat1,lon1,lat2,lon2)
    links = process_links(graph, node, features)
    color = features[:,3] # we choose the costs
    names = ['capacity', 'length', 'fftt', 'tt_over_fftt']
    geojson_link(links, names, color)


def heterogeneous_demand(d, alpha):
    d_nr = np.copy(d)
    d_r = np.copy(d)
    d_nr[:,2] = (1-alpha) * d_nr[:,2]
    d_r[:,2] = alpha * d_r[:,2]
    return d_nr, d_r


def I210_parametric_study():
    '''
    study the test_*.csv files generated by I210_parametric_study_2()
    in particular, display the average costs for each type of users
    alpha = 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0
    '''
    # graphs
    g_r = np.loadtxt('data/I210_net.csv', delimiter=',', skiprows=1)
    g_nr = np.copy(g_r)
    features = extract_features('data/I210Sketch_net.csv')
    for row in range(g_nr.shape[0]):
        if features[row,0] < 3000.:
            g_nr[row,3] = g_nr[row,3] + 100.
    # demand
    d = np.loadtxt('data/I210_od.csv', delimiter=',', skiprows=1)
    d[:,2] = d[:,2] / 4000 

    # print 'non-routed = 1.0, routed = 0.0'
    # fs = solver_3(g_nr, d, max_iter=1000, q=100, display=1, stop=1e-2)    
    # np.savetxt('data/test_0.csv', fs, delimiter=',')

    # print 'non-routed = 0.0, routed = 1.0'
    # fs = solver_3(g_r, d, max_iter=1000, q=100, display=1, stop=1e-2)    
    # np.savetxt('data/test_100.csv', fs, delimiter=',')

    alpha = 0.5
    print 'non-routed = {}, routed = {}'.format(1-alpha, alpha)
    d_nr, d_r = heterogeneous_demand(d, alpha)
    fs = gauss_seidel([g_nr,g_r], [d_nr,d_r], solver_3, max_iter=1000, display=1,\
        stop=1e-2, q=50)
    np.savetxt('data/test_{}.csv'.format(int(alpha*100)), fs, delimiter=',')

    # visualization
    node = np.loadtxt('data/I210_node.csv', delimiter=',', skiprows=1)
    # extract features: 'capacity', 'length', 'fftt'
    feat = extract_features('data/I210Sketch_net.csv')
    ratio = cost_ratio(fs, g_r)
    # merge features with the cost ratios
    features = np.zeros((feat.shape[0],4))
    features[:,:3] = feat
    features[:,3] = ratio
    # join features with (lat1,lon1,lat2,lon2)
    links = process_links(graph, node, features)
    color = features[:,3] # we choose the costs
    names = ['capacity', 'length', 'fftt', 'tt_over_fftt']
    geojson_link(links, names, color)

def I210_ratio_r_total():
    '''
    study the test_*.csv files generated by I210_parametric_study()
    in particular, visualize the ratio each type of users on each link
    '''
    fs = np.loadtxt('data/test_50.csv', delimiter=',', skiprows=0)
    ratio = np.divide(fs[:,1], np.maximum(np.sum(fs, axis=1), 1e-8))
    net = np.loadtxt('data/I210_net.csv', delimiter=',', skiprows=1)
    node = np.loadtxt('data/I210_node.csv', delimiter=',', skiprows=1)
    geometry = extract_features('data/I210Sketch_net.csv')
    features = np.zeros((fs.shape[0], 4))
    features[:,:3] = geometry
    features[:,3] = ratio
    links = process_links(net, node, features)
    color = 2 * ratio # we choose the ratios of nr over r+nr
    geojson_link(links, ['capacity', 'length', 'fftt', 'r_routed'], color)
    #print(fs)
    #for a,b in zip(cost(f, graph), f*4000): print a,b

def multiply_cognitive_cost(net, feat, thres, cog_cost):
    net2 = np.copy(net)
    small_capacity = np.zeros((net2.shape[0],))
    for row in range(net2.shape[0]):
        if feat[row,0] < thres:
            small_capacity[row] = 1.0
            net2[row,3:] = net2[row,3:] * cog_cost
    return net2, small_capacity


def I210_parametric_study_2():
    '''
    study the test_*.csv files generated by I210_parametric_study()
    in particular, display the average costs for each type of users
    '''
    # load the network and its properties
    g_r, d, node, feat = load_I210()
    #modify the costs on non routed network
    g_nr, small_capacity = multiply_cognitive_cost(g_r, feat, 3000., 100.)
    #divide the demand by 4000 to computationally optimize
    d[:,2] = d[:,2] / 4000 

    for alpha in np.linspace(0.0, 1.0, num=11):
        #special case where in fact homogeneous game
        if alpha == 0.0:
            print 'non-routed = 1.0, routed = 0.0'
            f_nr = solver_3(g_nr, d, max_iter=1000, q=100, display=1, stop=1e-2) 
            fs=np.zeros((len(f_nr),2))
            fs[:,0]=f_nr
        elif alpha == 1.0:
            print 'non-routed = 0.0, routed = 1.0'
            f_r = solver_3(g_r, d, max_iter=1000, past=30, display=1, stop=1e-2)    
            fs=np.zeros((len(f_r),2))
            fs[:,1]=f_r            
        #run solver
        else:
            print 'non-routed = {}, routed = {}'.format(1-alpha, alpha)
            d_nr, d_r = heterogeneous_demand(d, alpha)
            fs = gauss_seidel([g_nr,g_r], [d_nr,d_r], solver_3, max_iter=1000, \
                display=1, stop=1e-2, q=50, stop_cycle=1e-3)
        #remultiply by 4000
        fs=fs*4000
        #save the result
        output_file('data/I210Sketch_net.csv', 'data/I210_node.csv', fs, \
            'data/I210/test_{}.csv'.format(int(alpha*100)))
        #np.savetxt('data/I210/test_{}.csv'.format(int(alpha*100)), fs, delimiter=',', fmt='%1.2e')


def I210_parametric_study_3(alphas):
    '''
    study the test_*.csv files generated by I210_parametric_study()
    in particular, display the average costs for each type of users
    '''
    # load the network and its properties
    g_r, d, node, feat = load_I210()
    #modify the costs on non routed network
    g_nr, small_capacity = multiply_cognitive_cost(g_r, feat, 3000., 100.)
    #divide the demand by 4000 to computationally optimize
    d[:,2] = d[:,2] / (1.9*4000.)

    for alpha in alphas:
        #special case where in fact homogeneous game
        if alpha == 0.0:
            print 'non-routed = 1.0, routed = 0.0'
            f_nr = solver_3(g_nr, d, max_iter=1000, q=100, display=1, stop=1e-3) 
            fs=np.zeros((len(f_nr),2))
            fs=f_nr
        elif alpha == 1.0:
            print 'non-routed = 0.0, routed = 1.0'
            f_r = solver_3(g_r, d, max_iter=1000, past=30, display=1, stop=1e-3)    
            fs=np.zeros((len(f_r),2))
            fs=f_r            
        #run solver
        else:
            print 'non-routed = {}, routed = {}'.format(1-alpha, alpha)
            d_nr, d_r = heterogeneous_demand(d, alpha)
            fs = gauss_seidel([g_nr,g_r], [d_nr,d_r], solver_3, max_iter=1000, \
                display=1, stop=1e-3, q=50, stop_cycle=1e-3)
        np.savetxt('data/I210/test_{}.csv'.format(int(alpha*100)), fs, delimiter=',')


def I210_metrics(alphas):
    '''
    study the test_*.csv files generated by chicago_parametric_study()
    in particular, display the average costs for each type of users
    '''
    out = np.zeros((len(alphas),6))
    net, d, node, features = load_I210()
    d[:,2] = d[:,2] / (1.9*4000.) 
    net2, small_capacity = multiply_cognitive_cost(net, features, 3000., 100.)
    save_metrics(alphas, net, net2, d, features, small_capacity, \
        'data/I210/test_{}.csv', 'data/I210/out.csv')


def check_results():
    # check highest ration of tt / fftt (should be less than 5)
    net, d, node, features = load_I210()
    f = np.loadtxt('data/I210/test_0.csv', delimiter=',')
    print np.max(cost_ratio(f, net))


def main():
    #process_I210_net()
    #frank_wolfe_on_I210()
    #I210_parametric_study()
    #I210_ratio_r_total()
    #I210_parametric_study_2()
    I210_parametric_study_3(np.linspace(0,.2,21))
    I210_metrics(np.linspace(0,.2,21))
    # check_results()


if __name__ == '__main__':
    main()