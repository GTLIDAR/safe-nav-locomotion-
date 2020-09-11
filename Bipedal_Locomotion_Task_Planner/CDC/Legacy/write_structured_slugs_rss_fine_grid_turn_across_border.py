
import numpy as np
import copy
import itertools
from tqdm import *
import simplejson as json
import math
from gridworld import *
import time


def parseJson(filename):
    automaton = dict()
    file = open(filename)
    data = json.load(file)
    file.close()
    variables = dict()
    for var in data['variables']:
            v = var.split('@')[0]
            if v not in variables.keys():
                for var2ind in range(data['variables'].index(var),len(data['variables'])):
                    var2 = data['variables'][var2ind]
                    if v != var2.split('@')[0]:
                        variables[v] = [data['variables'].index(var), data['variables'].index(var2)]
                        break
                    if data['variables'].index(var2) == len(data['variables'])-1:
                        variables[v] = [data['variables'].index(var), data['variables'].index(var2) + 1]

    for s in data['nodes'].keys():
        automaton[int(s)] = dict.fromkeys(['State','Successors'])
        automaton[int(s)]['State'] = dict()
        automaton[int(s)]['Successors'] = []
        for v in variables.keys():
            if variables[v][0] == variables[v][1]:
                bin  = [data['nodes'][s]['state'][variables[v][0]]]
            else:
                bin = data['nodes'][s]['state'][variables[v][0]:variables[v][1]]
            automaton[int(s)]['State'][v] = int(''.join(str(e) for e in bin)[::-1], 2)
            automaton[int(s)]['Successors'] = data['nodes'][s]['trans']
    return automaton

def reach_statesMO(gw,states):
    t =set()
    for state in states:
        for action in gw.actlistMO:
            ########## Jonas ##########
            t.update(set(np.nonzero(gw.probMO[action][state])[0]))
    return t

########## Jonas ##########
def reach_statesR(gw,states):
    t =set()
    for state in states:
        for action in gw.actlistR:
            t.update(set(np.nonzero(gw.probR[action][state])[0]))
    return t
########## Jonas ##########

def powerset(s):
    x = len(s)
    a = []
    then_PS = time.time()
    for i in range(1,1<<x):
        a.append({s[j] for j in range(x) if (i &(1<<j))})
    now_PS = time.time()
    print 'Power set took ', now_PS - then_PS, ' seconds'
    return a
    #then_PS = time.time()
    #pow_set_lists = reduce(lambda result, x: result + [subset + [x] for subset in result],s, [[]])
    #pow_set_lists.remove([])
    #i = 0
    #for specific_list in pow_set_lists:
    #    pow_set_lists[i] = set(specific_list)
    #    i +=1
    #now_PS = time.time()
   # print 'Power set took ', now_PS - then_PS, ' seconds'
    #return pow_set_lists

def cartesian (lists):
    if lists == []: return [()]
    return [x + (y,) for x in cartesian(lists[:-1]) for y in lists[-1]]

def target_visibility(gw):
    return

##################################################################################
def card_to_slugs_int(card):
    if card == 'N':
        slugs_int = 0
    elif card == 'S':
        slugs_int = 1
    elif card == 'W':
        slugs_int = 2
    elif card == 'E':
        slugs_int = 3
    else:
        print('___-------> ERROR. The only inputs accepted by "card_to_slugs_int" are {N,S,W,E} <-------___')
        slugs_int = 4
    return slugs_int
##################################################################################
def slugs_int_to_card(slugs_int):
    if slugs_int == 0:
        card = 'N'
    elif slugs_int == 1:
        card = 'S'
    elif slugs_int == 2:
        card = 'W'
    elif slugs_int == 3:
        card = 'E'
    else:
        print('___-------> ERROR. The only inputs accepted by "slugs_int_to_card" are {0,1,2,3} <-------___')
        card = None
    return card
##################################################################################
def target_visibility(gw, invisibilityset, partitionGrid, target_vision_dist, filename_target_vis, allowed_states, visset_target):
    nonbeliefstates = gw.states
    beliefcombs = powerset(partitionGrid.keys())
    allstates = copy.deepcopy(nonbeliefstates)
    for i in range(gw.nstates,gw.nstates + len(beliefcombs)):
        allstates.append(i)
    allstates.append(len(allstates)) # nominal state if target leaves allowed region
    # Open a new file
    f = open(filename_target_vis,'w+')
    # Start the loop for determining vision
    counter1 = 0
    counter2 = 0
    print '(1) Looping Through Belief States'
    print '(2) Looping Through Physical States'
    print '(3) Looping Through Invisible Belief States to Determine Target Vision'
    for st in tqdm(set(allstates) - (set(nonbeliefstates) - set(allowed_states))):
        if (st in allowed_states) or (st == allstates[-1]):
            continue
        else:
            for s in tqdm(allowed_states):
                invisstates = invisibilityset[s]
                visstates = set(nonbeliefstates) - invisstates
                beliefcombstate = beliefcombs[st - len(nonbeliefstates)]
                beliefstates = set()
                for currbeliefstate in beliefcombstate:
                    beliefstates = beliefstates.union(partitionGrid[currbeliefstate])
                # beliefstates = beliefstates - set(targets) # remove target positions (no transitions from target positions)
                beliefstates_vis = beliefstates.intersection(visstates)
                beliefstates_invis = beliefstates - beliefstates_vis
                if not bool(beliefstates_invis):
                    continue
                string = '{}'.format(st) + ';' + '{}'.format(s) + ':'
                # # Determine which states are visible from the states (in the belief set) that cannot be seen by agent
                repeat = set()
                for iState in tqdm(beliefstates_invis):
                    for key,value in visset_target[iState].items():
                        if not bool(value):
                            continue
                        for item_2 in value:
                            if item_2 not in repeat:
                                string += ('{}'.format(item_2) + ',')
                                repeat.add(item_2)
                string = string[:-1] + '\n'
                f.write(string)
    f.close()
    return filename_target_vis
##################################################################################
def vis_parser(file_target_vis):
    vis_dict = dict()
    f2parse = open(file_target_vis, 'r')
    for lines in f2parse:
        # First split apart the belief state from the rest of the string
        array1 = lines.split(';')
        st_key = int(array1[0])
        # Next split the agent state from the rest of the string
        array2 = array1[1].split(':')
        s_key = int(array2[0])
        value = list(map(int, array2[1].split(',')))
        if st_key not in vis_dict:
            vis_dict[st_key] = dict()
        vis_dict[st_key][s_key] = value
    f2parse.close()
    return vis_dict
##################################################################################
def write_to_slugs_part_dist(infile,gw,init,initmovetarget,invisibilityset,PUDO_targets,visset_target = [],targets = [],vel=1,visdist = 5,allowed_states = [],
    fullvis_states = [],partitionGrid =dict(), belief_safety = 0, belief_liveness = 0, target_reachability = False,
    target_has_vision = False, target_vision_dist = 1.1, filename_target_vis = None, compute_vis_flag = False):
    nonbeliefstates = gw.states
    beliefcombs = powerset(partitionGrid.keys())
    #beliefcombs is all possible combination of belief states defined in main file
    allstates = copy.deepcopy(nonbeliefstates)
    for i in range(gw.nstates,gw.nstates + len(beliefcombs)):
        allstates.append(i)
    allstates.append(len(allstates)) # nominal state if target leaves allowed region

    # target_total_vis = target_visibility(gw)

    filename = infile+'.structuredslugs'
    file = open(filename,'w')
    file.write('[INPUT]\n')
    # print('nonbeliefstates: ' + str(nonbeliefstates))
    # print('allstates: ' + str(allstates))
    # print('len(allstates): ' + str(len(allstates)))
    file.write('st:0...{}\n'.format(len(allstates) -1))
    file.write('orientation:0...11\n')
    file.write('s:0...{}\n'.format(len(gw.states)-1))
    file.write('directionrequest:0...4\n')
    file.write('stair\n')
    file.write('border_trans\n')
    # file.write('sOld:0...{}\n'.format(len(gw.states)-1))
    # file.write('pastTurnStanceMatchFoot:0...2\n')

    file.write('\n[OUTPUT]\n')
    file.write('forward\n')
    # file.write('turnLeft\n')
    # file.write('turnRight\n')
    file.write('stepL:0...3\n')
    file.write('stop\n')
    file.write('requestPending1:0...5\n')
    # file.write('requestPending2\n')
    file.write('stepH:0...6\n')
    file.write('turn:1...3\n')
    # file.write('stanceFoot:0...2\n')
    # file.write('s:0...{}\n'.format(len(gw.states)-1))
    if target_reachability:
        file.write('c:0...1\n')

    file.write('\n[ENV_INIT]\n')
    file.write('s = {}\n'.format(init))
    file.write('orientation = 6\n')
    file.write('directionrequest = 0\n')
    file.write('!stair\n')
    # file.write('pastTurnStanceMatchFoot = 2\n')

    if initmovetarget in allowed_states:
        file.write('st = {}\n'.format(initmovetarget))
    else:
        file.write('st = {}\n'.format(allstates[-1]))

    # file.write('sOld = {}\n'.format(init))
    

    file.write('\n[SYS_INIT]\n')
    # file.write('s = {}\n'.format(init))
    if target_reachability:
        file.write('c = 0\n')

    file.write('!forward\n')
    # file.write('!turnLeft\n')
    # file.write('!turnRight\n')
    file.write('turn = 2\n')
    file.write('stop\n')
    file.write('stepH = 3\n')
    # file.write('!stop\n')

    # writing env_trans
    file.write('\n[ENV_TRANS]\n')
    print 'Writing ENV_TRANS'
    file.write("st' = {}\n".format(initmovetarget))

    ##################### Jonas Action Based Specs ###################
    print 'Writing Action Based Environment Transitions'
    stri = ''
    stri += '\n'
    stri += '\n'
    file.write(stri)


    # file.write("# rules governing when the border transition flag can be true")
    # stri = "(orientation=9 | orientation=10 | orientation=11 | orientation=0 | orientation=1 | orientation=2 | orientation =3) & ("
    # for edgeS in gw.top_edge + gw.top_edge2 + gw.top_edge3:
    #     stri += "s = {} | ".format(edgeS)
    # stri = stri[:-3]
    # stri += ") & ("
    # for edgeS in gw.bottom_edge + gw.bottom_edge2 + gw.bottom_edge3:
    #     stri += "s' = {} | ".format(edgeS)
    # stri = stri[:-3]
    # stri += ") -> border_trans'"


    # walking straight or exiting turn
    # can I get rid of border cases if I add a system condition that the state can't go from the left to the right or from the right to the left?
    # stri =""
    # for edgeS in gw.edges:
    #     stri += "st' != {}\n".format(edgeS)
    # stri += "\n"
    # file.write(stri)

    # for s in allowed_states:
    #     file.write("s = {} -> sOld' = {}".format(s,s))

    # file.write("sOld' = s\n\n")

    #### Walking North ####
    stri = "(orientation=0 | orientation=11 | orientation=1)  & s>{} & forward & stepL=0 -> s' + {} = s\n".format(gw.ncols-1, gw.ncols)
    stri += "(orientation=0 | orientation=11 | orientation=1) & s>{} & forward & stepL=1 -> s' + {} = s\n".format(2*gw.ncols-1, 2*gw.ncols)
    stri += "(orientation=0 | orientation=11 | orientation=1) & s>{} & forward & stepL=2 -> s' + {} = s\n\n".format(3*gw.ncols-1, 3*gw.ncols)
    
    stri += "(orientation=0 | orientation=11 | orientation=1) & "
    stri += "s<{} & ".format(gw.ncols)
    stri += "forward & stepL=0 -> s' = s + {}\n".format((gw.nrows-1)*(gw.ncols))

    stri += "(orientation=0 | orientation=11 | orientation=1) & "
    stri += "s<{} & ".format(2*gw.ncols)
    stri += "forward & stepL=1 -> s' = s + {}\n".format((gw.nrows-2)*(gw.ncols))

    stri += "(orientation=0 | orientation=11 | orientation=1) & "
    stri += "s<{} & ".format(3*gw.ncols)
    stri += "forward & stepL=2 -> s' = s + {}\n".format((gw.nrows-3)*(gw.ncols))


    #### Walking East ####
    # stri += "(orientation=3 | orientation=4 | orientation=2) & forward & stepL=0 -> s'=s+1\n"
    # stri += "(orientation=3 | orientation=4 | orientation=2) & forward & stepL=1 -> s'=s+2\n"
    # stri += "(orientation=3 | orientation=4 | orientation=2) & forward & stepL=2 -> s'=s+3\n\n"

    stri += "\n(orientation=3 | orientation=4 | orientation=2) & "
    for row in range(gw.nrows):
        stri += "s != {} & ".format((row+1)*gw.ncols-1)
    stri += "forward & stepL=0 -> s' = s+1\n"

    stri += "(orientation=3 | orientation=4 | orientation=2) & "
    for row in range(gw.nrows):
        stri += "s != {} & s != {} & ".format((row+1)*gw.ncols-2, (row+1)*gw.ncols-1)
    stri += "forward & stepL=1 -> s' = s+2\n"

    stri += "(orientation=3 | orientation=4 | orientation=2) & "
    for row in range(gw.nrows):
        stri += "s != {} & s != {} & s != {} & ".format((row+1)*gw.ncols-3, (row+1)*gw.ncols-2, (row+1)*gw.ncols-1)
    stri += "forward & stepL=2 -> s' = s+3\n"


    stri += "\n(orientation=3 | orientation=4 | orientation=2) & ("
    for row in range(gw.nrows):
        stri += "s = {} \\/ ".format((row+1)*gw.ncols-1)
    stri = stri[:-4]
    stri += ") & forward & stepL=0 -> s' + {} = s\n".format(gw.ncols-1)

    stri += "(orientation=3 | orientation=4 | orientation=2) & ("
    for row in range(gw.nrows):
        stri += "s = {} \\/ s = {}  \\/ ".format((row+1)*gw.ncols-2, (row+1)*gw.ncols-1)
    stri = stri[:-4]
    stri += ") & forward & stepL=1 -> s' + {} = s\n".format(gw.ncols-2)

    stri += "(orientation=3 | orientation=4 | orientation=2) & ("
    for row in range(gw.nrows):
        stri += "s = {} \\/ s = {} \\/ s = {} \\/ ".format((row+1)*gw.ncols-3, (row+1)*gw.ncols-2, (row+1)*gw.ncols-1)
    stri = stri[:-4]
    stri += ") & forward & stepL=2 -> s' + {} = s\n".format(gw.ncols-3)




    # ##################### Jonas test ###################


    #### Walking South ####
    stri += "\n(orientation=6 | orientation=7 | orientation=5) & s<{} & forward & stepL=0 -> s' = s + {}\n".format((gw.nrows-1)*gw.ncols, gw.ncols)
    stri += "(orientation=6 | orientation=7 | orientation=5) & s<{} & forward & stepL=1 -> s' = s + {}\n".format((gw.nrows-2)*gw.ncols, 2*gw.ncols)
    stri += "(orientation=6 | orientation=7 | orientation=5) & s<{} & forward & stepL=2 -> s' = s + {}\n".format((gw.nrows-3)*gw.ncols, 3*gw.ncols)

    stri += "\n(orientation=6 | orientation=7 | orientation=5) & "
    stri += "s>{} &".format((gw.nrows-1)*gw.ncols-1)
    stri += "forward & stepL=0 -> s' + {} = s\n".format(gw.ncols*(gw.nrows-1))

    stri += "(orientation=6 | orientation=7 | orientation=5) & "
    stri += "s>{} &".format((gw.nrows-2)*gw.ncols-1)
    stri += "forward & stepL=1 -> s' + {} = s\n".format(gw.ncols*(gw.nrows-2))

    stri += "(orientation=6 | orientation=7 | orientation=5) & "
    stri += "s>{} &".format((gw.nrows-3)*gw.ncols-1)
    stri += "forward & stepL=2 -> s' + {} = s\n".format(gw.ncols*(gw.nrows-3))

    #### Walking West ####
    stri += "\n(orientation=9 | orientation=10 | orientation=8) & "
    for row in range(gw.nrows):
        stri += "s != {} & ".format(row*gw.ncols)
    stri += "forward & stepL=0 -> s' + 1 = s\n"

    stri += "(orientation=9 | orientation=10 | orientation=8) & "
    for row in range(gw.nrows):
        stri += "s != {} & s != {} & ".format(row*gw.ncols+1 , row*gw.ncols)
    stri += "forward & stepL=1 -> s' + 2 = s\n"

    stri += "(orientation=9 | orientation=10 | orientation=8) & "
    for row in range(gw.nrows):
        stri += "s != {} & s != {} & s != {} & ".format(row*gw.ncols+2 , row*gw.ncols+1 , row*gw.ncols)
    stri += "forward & stepL=2 -> s' + 3 = s\n"


    stri += "\n(orientation=9 | orientation=10 | orientation=8) & ("
    for row in range(gw.nrows):
        stri += "s = {} \\/ ".format(row*gw.ncols)
    stri = stri[:-4]
    stri += ") & forward & stepL=0 -> s' = s + {}\n".format(gw.ncols-1)

    stri += "(orientation=9 | orientation=10 | orientation=8) & ("
    for row in range(gw.nrows):
        stri += "s = {} \\/ s = {} \\/ ".format(row*gw.ncols+1 , row*gw.ncols)
    stri = stri[:-4]
    stri += ")  &forward & stepL=1 -> s' = s + {}\n".format(gw.ncols-2)

    stri += "(orientation=9 | orientation=10 | orientation=8) & ("
    for row in range(gw.nrows):
        stri += "s = {} \\/ s = {} \\/ s = {} \\/ ".format(row*gw.ncols+2 , row*gw.ncols+1 , row*gw.ncols)
    stri = stri[:-4]
    stri += ") & forward & stepL=2 -> s' = s + {}\n".format(gw.ncols-3)
    
    file.write(stri)

    # stri = "\nforward & turnLeft & orientation>0 -> orientation'+1 = orientation\n"
    # stri += "forward & turnRight & orientation<11 -> orientation' = orientation+1\n"
    # stri += "forward & turnLeft & orientation=0 -> orientation' = 11\n"
    # stri += "forward & turnRight & orientation=11 -> orientation' = 0\n"
    # stri += "\n"
    # file.write(stri)
    ###45deg change###
    stri = "\nforward & turn=1 & orientation>0 -> orientation'+1 = orientation\n"
    stri += "forward & turn=3 & orientation<11 -> orientation' = orientation+1\n"
    stri += "forward & turn=1 & orientation=0 -> orientation' = 11\n"
    stri += "forward & turn=3 & orientation=11 -> orientation' = 0\n"
    # stri += "(orientation=3 | orientation=6 | orientation=9) & turn=0 -> orientation'+2 = orientation\n"
    # stri += "orientation=0 & turn=0 -> orientation' = 10\n"
    # stri += "(orientation=0 | orientation=3 | orientation=6 | orientation=9) & turn=4 -> orientation' = orientation+2\n"
    # stri += "forward & turn=0 & orientation>0 & orientation!=0 & orientation!=3 & orientation!=6 & orientation!=9 -> orientation'+1 = orientation\n"
    # stri += "forward & turn=4 & orientation<11 & orientation!=0 & orientation!=3 & orientation!=6 & orientation!=9 -> orientation' = orientation+1\n"
    stri += "\n"
    file.write(stri)
    ###45deg change###

    ###45deg change###
    # stri = "((orientation=0 | orientation=1) & turn=3 & stepL=3) -> s' + {} = s\n".format(gw.ncols-1)
    # stri += "((orientation=3 | orientation=4) & turn=3 & stepL=3) -> s' = s + {}\n".format(gw.ncols+1)
    # stri += "((orientation=6 | orientation=7) & turn=3 & stepL=3) -> s' = s + {}\n".format(gw.ncols-1)
    # stri += "((orientation=9 | orientation=10) & turn=3 & stepL=3) -> s' + {} = s\n".format(gw.ncols+1)
    # stri += "\n"

    # stri += "((orientation=0 | orientation=11) & turn=1 & stepL=3) -> s' + {} = s\n".format(gw.ncols+1)
    # stri += "((orientation=3 | orientation=2) & turn=1 & stepL=3) -> s' + {} = s\n".format(gw.ncols-1)
    # stri += "((orientation=6 | orientation=5) & turn=1 & stepL=3) -> s' = s + {}\n".format(gw.ncols+1)
    # stri += "((orientation=9 | orientation=8) & turn=1 & stepL=3) -> s' = s + {}\n".format(gw.ncols-1)
    # stri += "\n"
    # file.write(stri)
    ###45deg change###
    # stri = "(s > {} & (orientation=0 | orientation=1) & turn=3 & stepL=3) -> s' + {} = s\n".format(gw.ncols-1,gw.ncols-1)
    # stri = "(s < {} & (orientation=0 | orientation=1) & turn=3 & stepL=3) -> s' + {} = s\n".format(gw.ncols,gw.ncols-1)



    file.write("\n\n\n #specs_for_turning\n\n")
    ##### Grid transitions when turning right with orientation 0 or 1
    top_right_edge = gw.top_edge+gw.right_edge
    stri = "\n("
    for edgeS in top_right_edge:
        stri += "s != {} & ".format(edgeS)
    stri += "(orientation=0 | orientation=1) & turn=3 & stepL=3) -> s' + {} = s\n".format(gw.ncols-1)
    file.write(stri)

    top_edge_minus_right = list(set(gw.top_edge) - set(gw.right_edge))
    stri = "("
    for edgeS in top_edge_minus_right:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=0 | orientation=1) & turn=3 & stepL=3 -> s' = s + {}\n".format(gw.ncols*(gw.nrows-1)+1)
    file.write(stri)

    right_edge_minus_top = list(set(gw.right_edge) - set(gw.top_edge))
    stri = "("
    for edgeS in right_edge_minus_top:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=0 | orientation=1) & turn=3 & stepL=3 -> s' + {} = s\n".format(gw.ncols*2-1)
    file.write(stri)
    
    ##### Grid transitions when turning right with orientation 3 or 4
    right_bottom_edge = gw.right_edge + gw.bottom_edge
    stri = "\n("
    for edgeS in right_bottom_edge:
        stri += "s != {} & ".format(edgeS)
    stri += "(orientation=3 | orientation=4) & turn=3 & stepL=3) -> s' = s + {}\n".format(gw.ncols+1)
    file.write(stri)

    right_edge_minus_bottom = list(set(gw.right_edge) - set(gw.bottom_edge))
    stri = "("
    for edgeS in right_edge_minus_bottom:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=3 | orientation=4) & turn=3 & stepL=3 -> s' = s + 1\n"
    file.write(stri)

    bottom_edge_minus_right = list(set(gw.bottom_edge) - set(gw.right_edge))
    stri = "("
    for edgeS in bottom_edge_minus_right:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=3 | orientation=4) & turn=3 & stepL=3 -> s' + {} = s\n".format(gw.ncols*(gw.nrows-1))
    file.write(stri)

    ##### Grid transitions when turning right with orientation 6 or 7
    bottom_left_edge = gw.bottom_edge + gw.left_edge
    stri = "\n("
    for edgeS in bottom_left_edge:
        stri += "s != {} & ".format(edgeS)
    stri += "(orientation=6 | orientation=7) & turn=3 & stepL=3) -> s' = s + {}\n".format(gw.ncols-1)
    file.write(stri)

    bottom_edge_minus_left = list(set(gw.bottom_edge) - set(gw.left_edge))
    stri = "("
    for edgeS in bottom_edge_minus_left:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=6 | orientation=7) & turn=3 & stepL=3 -> s' + {} = s\n".format(gw.ncols*(gw.nrows-1)+1)
    file.write(stri)

    left_edge_minus_bottom = list(set(gw.left_edge) - set(gw.bottom_edge))
    stri = "("
    for edgeS in left_edge_minus_bottom:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=6 | orientation=7) & turn=3 & stepL=3 -> s' = s + {}\n".format(2*gw.ncols-1)
    file.write(stri)
    
    ##### Grid transitions when turning right with orientation 9 or 10
    left_top_edge = gw.left_edge + gw.top_edge
    stri = "\n("
    for edgeS in left_top_edge:
        stri += "s != {} & ".format(edgeS)
    stri += "(orientation=9 | orientation=10) & turn=3 & stepL=3) -> s' + {} = s\n".format(gw.ncols+1)
    file.write(stri)

    left_edge_minus_top = list(set(gw.left_edge) - set(gw.top_edge))
    stri = "("
    for edgeS in left_edge_minus_top:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=9 | orientation=10) & turn=3 & stepL=3 -> s' + 1 = s\n"
    file.write(stri)

    top_edge_minus_left = list(set(gw.top_edge) - set(gw.left_edge))
    stri = "("
    for edgeS in top_edge_minus_left:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=9 | orientation=10) & turn=3 & stepL=3 -> s' = s + {}\n".format((gw.nrows-1)*gw.ncols-1)
    file.write(stri)

    




    ##### Grid transitions when turning left with orientation 0 or 11
    # stri += "((orientation=0 | orientation=11) & turn=1 & stepL=3) -> s' + {} = s\n".format(gw.ncols+1)
    stri = "\n("
    for edgeS in left_top_edge:
        stri += "s != {} & ".format(edgeS)
    stri += "(orientation=0 | orientation=11) & turn=1 & stepL=3) -> s' + {} = s\n".format(gw.ncols+1)
    file.write(stri)

    stri = "("
    for edgeS in top_edge_minus_left:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=0 | orientation=11) & turn=1 & stepL=3 -> s' = s + {}\n".format((gw.nrows-1)*gw.ncols-1)
    file.write(stri)

    stri = "("
    for edgeS in left_edge_minus_top:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=0 | orientation=11) & turn=1 & stepL=3 -> s' + 1 = s\n"
    file.write(stri)
    
    ##### Grid transitions when turning left with orientation 3 or 2
    # stri += "((orientation=3 | orientation=2) & turn=1 & stepL=3) -> s' + {} = s\n".format(gw.ncols-1)
    stri = "\n("
    for edgeS in top_right_edge:
        stri += "s != {} & ".format(edgeS)
    stri += "(orientation=3 | orientation=2) & turn=1 & stepL=3) -> s' + {} = s\n".format(gw.ncols-1)
    file.write(stri)

    stri = "("
    for edgeS in top_edge_minus_right:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=3 | orientation=2) & turn=1 & stepL=3 -> s' = s + {}\n".format(gw.ncols*(gw.nrows-1)+1)
    file.write(stri)

    stri = "("
    for edgeS in right_edge_minus_top:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=3 | orientation=2) & turn=1 & stepL=3 -> s' + {} = s\n".format(gw.ncols*2-1)
    file.write(stri)

    ##### Grid transitions when turning left with orientation 6 or 5
    # stri += "((orientation=6 | orientation=5) & turn=1 & stepL=3) -> s' = s + {}\n".format(gw.ncols+1)
    stri = "\n("
    for edgeS in right_bottom_edge:
        stri += "s != {} & ".format(edgeS)
    stri += "(orientation=6 | orientation=5) & turn=1 & stepL=3) -> s' = s + {}\n".format(gw.ncols+1)
    file.write(stri)

    stri = "("
    for edgeS in right_edge_minus_bottom:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=6 | orientation=5) & turn=1 & stepL=3 -> s' = s + 1\n"
    file.write(stri)

    stri = "("
    for edgeS in bottom_edge_minus_right:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=6 | orientation=5) & turn=1 & stepL=3 -> s' + {} = s\n".format(gw.ncols*(gw.nrows-1))
    file.write(stri)
    
    
    ##### Grid transitions when turning left with orientation 9 or 8
    # stri += "((orientation=9 | orientation=8) & turn=1 & stepL=3) -> s' = s + {}\n".format(gw.ncols-1)
    stri = "\n("
    for edgeS in bottom_left_edge:
        stri += "s != {} & ".format(edgeS)
    stri += "(orientation=9 | orientation=8) & turn=1 & stepL=3) -> s' = s + {}\n".format(gw.ncols-1)
    file.write(stri)

    stri = "("
    for edgeS in bottom_edge_minus_left:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=9 | orientation=8) & turn=1 & stepL=3 -> s' + {} = s\n".format(gw.ncols*(gw.nrows-1)+1)
    file.write(stri)

    stri = "("
    for edgeS in left_edge_minus_bottom:
        stri += "s = {} | ".format(edgeS)
    stri = stri[:-3]
    stri += ") & (orientation=9 | orientation=8) & turn=1 & stepL=3 -> s' = s + {}\n".format(2*gw.ncols-1)
    file.write(stri)





    ###45deg change###
    # stri = "((orientation=0 | orientation=1) & turn=4 & stepL=3) -> s' + {} = s\n".format(gw.ncols-1)
    # stri += "((orientation=3 | orientation=4) & turn=4 & stepL=3) -> s' = s + {}\n".format(gw.ncols+1)
    # stri += "((orientation=6 | orientation=7) & turn=4 & stepL=3) -> s' = s + {}\n".format(gw.ncols-1)
    # stri += "((orientation=9 | orientation=10) & turn=4 & stepL=3) -> s' + {} = s\n".format(gw.ncols+1)
    # stri += "\n"

    # stri += "((orientation=0 | orientation=11) & turn=0 & stepL=3) -> s' + {} = s\n".format(gw.ncols+1)
    # stri += "((orientation=3 | orientation=2) & turn=0 & stepL=3) -> s' + {} = s\n".format(gw.ncols-1)
    # stri += "((orientation=6 | orientation=5) & turn=0 & stepL=3) -> s' = s + {}\n".format(gw.ncols+1)
    # stri += "((orientation=9 | orientation=8) & turn=0 & stepL=3) -> s' = s + {}\n".format(gw.ncols-1)
    # stri += "\n"
    # file.write(stri)
    ###45deg change###

    stri = "!forward -> s' = s\n"
    ###45deg change###
    stri += "turn=2 -> orientation' = orientation"
    ###45deg change###
    stri += "\n"
    file.write(stri)

    
    # stri = "!forward -> st' != s\n"
    stri = "st' != s\n"
    stri += "\n"
    file.write(stri)

    # file.write("(orientation != 1 & directionrequest' != 2) /\ (orientation != 3 & directionrequest' != 4) -> !stair'\n")
    # file.write("(orientation' != 3 & directionrequest' != 2) & (orientation' != 9 & directionrequest' != 4) -> !stair'\n")
    file.write("(orientation' != 3 & orientation' != 9) \/ (directionrequest' != 4 & directionrequest' != 2) -> !stair'\n")

    # footstance based navigation:
    # file.write("(orientation=0 | orientation=3 |orientation=6 | orientation=9) /\\ turnLeft /\\ stanceFoot=0 -> pastTurnStanceMatchFoot' = 1\n")
    # file.write("(orientation=0 | orientation=3 |orientation=6 | orientation=9) /\\ turnLeft /\\ stanceFoot=1 -> pastTurnStanceMatchFoot' = 0\n")
    # file.write("(orientation=0 | orientation=3 |orientation=6 | orientation=9) /\\ turnRight /\\ stanceFoot=0 -> pastTurnStanceMatchFoot' = 0\n")
    # file.write("(orientation=0 | orientation=3 |orientation=6 | orientation=9) /\\ turnRight /\\ stanceFoot=1 -> pastTurnStanceMatchFoot' = 1\n")
    # file.write("forward /\\ ((orientation !=0 /\\ orientation!=3 /\\ orientation != 6 /\\ orientation != 9) \/ (!turnLeft /\\ !turnRight)) -> pastTurnStanceMatchFoot' = pastTurnStanceMatchFoot\n")
    # file.write("!forward -> pastTurnStanceMatchFoot' = 2\n")
    ##################### Jonas Action Based Specs ###################


    # Writing env_safety
    print 'Writing ENV_SAFETY'
    for obs in tqdm(gw.obstacles):
        if obs in allowed_states:
            file.write('!st = {}\n'.format(obs))

    ##### Navigation goal tracking
    # stri = "directionrequest = 1 -> ((s' = {} & directionrequest' = 0) \/ (s' != {} & directionrequest' = 1))\n".format(PUDO_targets[0],PUDO_targets[0])
    # stri += "directionrequest = 2 -> ((s' = {} & directionrequest' = 0) \/ (s' != {} & directionrequest' = 2))\n".format(PUDO_targets[1],PUDO_targets[1])
    # stri += "directionrequest = 3 -> ((s' = {} & directionrequest' = 0) \/ (s' != {} & directionrequest' = 3))\n".format(PUDO_targets[2],PUDO_targets[2])
    # stri += "directionrequest = 4 -> ((s' = {} & directionrequest' = 0) \/ (s' != {} & directionrequest' = 4))\n".format(PUDO_targets[3],PUDO_targets[3])
    # file.write(stri)
    
    # file.write("directionrequest = 0 -> directionrequest' !=0\n\n")

    ##### Attempt to elliminate stop when entering each new coarse grid #####:
    file.write("directionrequest = 0 & orientation = 0 & requestPending1 = 5 -> directionrequest' =1 \/ directionrequest' =0\n")
    file.write("directionrequest = 0 & orientation = 3 & requestPending1 = 5 -> directionrequest' =2 \/ directionrequest' =0\n")
    file.write("directionrequest = 0 & orientation = 6 & requestPending1 = 5 -> directionrequest' =3 \/ directionrequest' =0\n")
    file.write("directionrequest = 0 & orientation = 9 & requestPending1 = 5 -> directionrequest' =4 \/ directionrequest' =0\n")

    file.write("directionrequest = 1 -> directionrequest' !=3\n")
    file.write("directionrequest = 2 -> directionrequest' !=4\n")
    file.write("directionrequest = 3 -> directionrequest' !=1\n")
    file.write("directionrequest = 4 -> directionrequest' !=2\n")

    file.write("requestPending1 != 5 -> directionrequest' = directionrequest\n")
    # file.write("requestPending1 = 5 -> directionrequest' != 0\n\n")

    ###### Can't use specs below since the robot tries to brake env specs by turning 
    # file.write("requestPending1 != 5 & stair-> stair' \n")
    # file.write("requestPending1 != 5 & !stair-> !stair' \n")

    ##################### Some Suda Stuff ###################
    # if target_reachability:
    #     for t in targets:
    #         file.write('!st = {}\n'.format(t))
    ##################### Some Suda Stuff ###################

    # writing sys_trans
    file.write('\n[SYS_TRANS]\n')
    # all this code does is check what states there is a probability greater than 0 of getting to from the current state. Need to include orientation in that probability map
    # not sure how to deal with actions relying on previous actions. Should I just include actions in the spec file?
    #In general do not need to rely on previous actions/next actions other than to tell the system to stop ahead of time, how to deal with this?

    print 'Writing SYS_TRANS'
    

    ####################################### JONAS ############################
    # stri = "!forward' -> (!turnLeft' & !turnRight')\n\n"
    
    # stri += "!forward -> (!turnLeft' & !turnRight')\n\n"
    stri = "!forward' -> turn'=2\n\n"

    # stri += "turnLeft' -> !turnRight'\n"
    # stri += "turnRight' -> !turnLeft'\n\n"
    # stri += "turn' != 0\n"
    # stri += "turn' != 4\n"
    

    stri += "stop -> stepL=0\n"
    stri += "!forward -> (stepL=0 & turn=2)\n\n"
    stri += "stop <-> !forward'\n\n"
    stri += "(orientation'!=0 & orientation'!=3  & orientation'!=6 & orientation'!=9) -> stepL=3\n"
    stri += "(orientation'=0 | orientation'=3  | orientation'=6 | orientation'=9) -> stepL!=3\n\n"
    stri += "(turn=3 & (orientation'!=0 & orientation'!=3  & orientation'!=6 & orientation'!=9)) -> turn'=3\n"
    stri += "(turn=1 & (orientation'!=0 & orientation'!=3  & orientation'!=6 & orientation'!=9)) -> turn'=1\n"
    # stri += "(turn=4 & (orientation'!=0 & orientation'!=3  & orientation'!=6 & orientation'!=9)) -> turn'=4\n"
    # stri += "(turn=0 & (orientation'!=0 & orientation'!=3  & orientation'!=6 & orientation'!=9)) -> turn'=0\n"
    stri += "\n"
    file.write(stri)


    ##### navigation goal tracking specs #####
    # stri = "(s = {}) -> ! requestPending1'\n".format(PUDO_targets[0])
    # stri += "!(s = {}) ->(requestPending1' <-> (requestPending1 | directionrequest))\n\n".format(PUDO_targets[0])
    # stri += "(s = {}) -> !requestPending2'\n".format(PUDO_targets[1])
    # stri += "!(s = {}) -> (requestPending2' <-> ((s = {} & requestPending1) | requestPending2))\n\n".format(PUDO_targets[1],PUDO_targets[0])
    # file.write(stri)
    # stri = "directionrequest = 1 -> ((s = {} & directionrequest' = 0) \/ directionrequest' = 1)\n".format(PUDO_targets[0])
    # stri += "directionrequest = 2 -> ((s = {} & deliveryrrequest' = 0) \/ directionrequest' = 2)\n".format(PUDO_targets[1])
    # stri += "directionrequest = 3 -> ((s = {} & directionrequest' = 0) \/ directionrequest' = 3)\n".format(PUDO_targets[2])
    # stri += "directionrequest = 4 -> ((s = {} & directionrequest' = 0) \/ directionrequest' = 4)\n".format(PUDO_targets[3])
    # file.write(stri)





    # footstance based navigation:
    # file.write('\n')
    # file.write("forward & !stop & stanceFoot=0 -> stanceFoot'=1\n")
    # file.write("forward & !stop & stanceFoot=1 -> stanceFoot'=0\n")

    # file.write("!forward' -> stanceFoot' =2\n")
    # file.write("forward' -> stanceFoot' !=2\n")

    # # file.write("forward & stanceFoot=0 -> stanceFoot'=1\n")
    # # file.write("forward & stanceFoot=1 -> stanceFoot'=0\n")

    # file.write("(orientation=0 | orientation=3 |orientation=6 | orientation=9) /\\ pastTurnStanceMatchFoot=1 /\\ stanceFoot=0 -> !turnLeft\n")
    # file.write("(orientation=0 | orientation=3 |orientation=6 | orientation=9) /\\ pastTurnStanceMatchFoot=1 /\\ stanceFoot=1 -> !turnRight\n")
    # file.write("(orientation=0 | orientation=3 |orientation=6 | orientation=9) /\\ pastTurnStanceMatchFoot=0 /\\ stanceFoot=0 -> !turnRight\n")
    # file.write("(orientation=0 | orientation=3 |orientation=6 | orientation=9) /\\ pastTurnStanceMatchFoot=0 /\\ stanceFoot=1 -> !turnLeft\n")

    # # last updates for yignke's new velocity picking:
    # file.write("!forward /\\ forward' -> stepL' = 1\n")
    # file.write("(orientation=0 | orienstation=3 |orientation=6 | orientation=9) /\\ pastTurnStanceMatchFoot=2 /\\ stanceFoot=0 -> !turnLeft\n")
    # file.write("(orientation=0 | orientation=3 |orientation=6 | orientation=9) /\\ pastTurnStanceMatchFoot=2 /\\ stanceFoot=1 -> !turnRight\n")
    # # ^last updates for yignke's new velocity picking

    file.write('\n')
    file.write('turn !=2 -> stepL != 1 /\ stepL !=2\n')
    file.write('\n')

    ##### Fine Specific Specs #####
    # stri =""
    # for edgeS in gw.edges:
    #     stri += "s' = {} -> turn' = 2\n".format(edgeS)
    # stri += "\n"
    # file.write(stri)

    # stri =""
    # for edgeS in gw.edges:
    #     stri += "s' = {} & directionrequest' != 0-> !forward\n".format(edgeS)
    # stri += "\n"
    # file.write(stri)

    # file.write("requestPending1' = directionrequest\n")

    ##### Specs that govern how liveness specs can be met #####
    # stri = "requestPending1 = 1 -> ((s' = {} & requestPending1' = 5) \/ (s' != {} & requestPending1' = 1))\n".format(PUDO_targets[0],PUDO_targets[0])
    # stri += "requestPending1 = 2 -> ((s' = {} & requestPending1' = 5) \/ (s' != {} & requestPending1' = 2))\n".format(PUDO_targets[1],PUDO_targets[1])
    # stri += "requestPending1 = 3 -> ((s' = {} & requestPending1' = 5) \/ (s' != {} & requestPending1' = 3))\n".format(PUDO_targets[2],PUDO_targets[2])
    # stri += "requestPending1 = 4 -> ((s' = {} & requestPending1' = 5) \/ (s' != {} & requestPending1' = 4))\n".format(PUDO_targets[3],PUDO_targets[3])
    # stri += "requestPending1 = 0 -> ((s = {} & s' = {} & requestPending1' = 5) \/ ( requestPending1' = 0))\n".format(PUDO_targets[4],PUDO_targets[4],PUDO_targets[4])
    # file.write(stri)

    stri = "requestPending1 = 1 -> ((("
    for edgeS in gw.top_edge:
        stri += "s' = {} \/ ".format(edgeS)
    stri = stri[:-4]
    stri+= ") & requestPending1' = 5) \/ (("
    for edgeS in gw.top_edge:
        stri += "s' != {} & ".format(edgeS)
    stri = stri[:-3]
    stri+= ") & requestPending1' = 1))\n"
    file.write(stri)

    file.write("\n\n #goal tracking specs\n\n")

    stri = "requestPending1 = 1 -> ((("
    for edgeS in gw.top_edge:
        stri += "s' = {} \/ ".format(edgeS)
    stri = stri[:-4]
    stri+= ") & requestPending1' = 5) \/ (("
    for edgeS in gw.top_edge:
        stri += "s' != {} & ".format(edgeS)
    stri = stri[:-3]
    stri+= ") & requestPending1' = 1))\n"
    file.write(stri)

    stri = "requestPending1 = 2 -> ((("
    for edgeS in gw.right_edge:
        stri += "s' = {} \/ ".format(edgeS)
    stri = stri[:-4]
    stri+= ") & requestPending1' = 5) \/ (("
    for edgeS in gw.right_edge:
        stri += "s' != {} & ".format(edgeS)
    stri = stri[:-3]
    stri+= ") & requestPending1' = 2))\n"
    file.write(stri)

    stri = "requestPending1 = 3 -> ((("
    for edgeS in gw.bottom_edge:
        stri += "s' = {} \/ ".format(edgeS)
    stri = stri[:-4]
    stri+= ") & requestPending1' = 5) \/ (("
    for edgeS in gw.bottom_edge:
        stri += "s' != {} & ".format(edgeS)
    stri = stri[:-3]
    stri+= ") & requestPending1' = 3))\n"
    file.write(stri)

    stri = "requestPending1 = 4 -> ((("
    for edgeS in gw.left_edge:
        stri += "s' = {} \/ ".format(edgeS)
    stri = stri[:-4]
    stri+= ") & requestPending1' = 5) \/ (("
    for edgeS in gw.left_edge:
        stri += "s' != {} & ".format(edgeS)
    stri = stri[:-3]
    stri+= ") & requestPending1' = 4))\n"
    file.write(stri)

    stri = "requestPending1 = 0 -> ((s = {} & s' = {} & requestPending1' = 5) \/ ( requestPending1' = 0))\n".format(PUDO_targets[4],PUDO_targets[4],PUDO_targets[4])
    file.write(stri)

    file.write("requestPending1 = 5 -> requestPending1' = directionrequest'\n")

    corner_states = [0,gw.ncols-1,gw.nstates-1,gw.nstates-gw.ncols]

    stri =""
    for edgeS in corner_states:
        stri += "s' != {}\n".format(edgeS)
    stri += "\n"
    file.write(stri)

    ##### Test ####

    ##### Ensure the robot doesn't leave cell before completing nav goal #####

    file.write("\n\n #specs to stay in coarse cell until goal is completed\n\n")

    stri =""
    for edgeS in gw.edges:
        stri += "s' = {} & requestPending1' != 5 -> !forward'\n".format(edgeS)
    stri += "\n"
    file.write(stri)

    # stri =""
    # for edgeS in gw.top_edge:
    #     stri += "s' = {} & orientation' = 0 & requestPending1' != 5 -> !forward'\n".format(edgeS)
    # stri += "\n"
    # file.write(stri)
    # stri =""
    # for edgeS in gw.right_edge:
    #     stri += "s' = {} & orientation' = 3 & requestPending1' != 5 -> !forward'\n".format(edgeS)
    # stri += "\n"
    # file.write(stri)
    # stri =""
    # for edgeS in gw.bottom_edge:
    #     stri += "s' = {} & orientation' = 6 & requestPending1' != 5 -> !forward'\n".format(edgeS)
    # stri += "\n"
    # file.write(stri)
    # stri =""
    # for edgeS in gw.left_edge:
    #     stri += "s' = {} & orientation' = 9 & requestPending1' != 5 -> !forward'\n".format(edgeS)
    # stri += "\n"
    # file.write(stri)

    stri =""
    for edgeS in gw.top_edge2:
        stri += "s' = {} & orientation' = 0 & requestPending1' != 5 -> stepL' != 2 & stepL' != 1\n".format(edgeS)
    stri += "\n"
    file.write(stri)
    stri =""
    for edgeS in gw.right_edge2:
        stri += "s' = {} & orientation' = 3 & requestPending1' != 5 -> stepL' != 2 & stepL' != 1\n".format(edgeS)
    stri += "\n"
    file.write(stri)
    stri =""
    for edgeS in gw.bottom_edge2:
        stri += "s' = {} & orientation' = 6 & requestPending1' != 5 -> stepL' != 2 & stepL' != 1\n".format(edgeS)
    stri += "\n"
    file.write(stri)
    stri =""
    for edgeS in gw.left_edge2:
        stri += "s' = {} & orientation' = 9 & requestPending1' != 5 -> stepL' != 2 & stepL' != 1\n".format(edgeS)
    stri += "\n"
    file.write(stri)

    stri =""
    for edgeS in gw.top_edge3:
        stri += "s' = {} & orientation' = 0 & requestPending1' != 5 -> stepL' != 2\n".format(edgeS)
    stri += "\n"
    file.write(stri)
    stri =""
    for edgeS in gw.right_edge3:
        stri += "s' = {} & orientation' = 3 & requestPending1' != 5 -> stepL' != 2\n".format(edgeS)
    stri += "\n"
    file.write(stri)
    stri =""
    for edgeS in gw.bottom_edge3:
        stri += "s' = {} & orientation' = 6 & requestPending1' != 5 -> stepL' != 2\n".format(edgeS)
    stri += "\n"
    file.write(stri)
    stri =""
    for edgeS in gw.left_edge3:
        stri += "s' = {} & orientation' = 9 & requestPending1' != 5 -> stepL' != 2\n".format(edgeS)
    stri += "\n"
    file.write(stri)
    ##### Test #####



    # stri = ""
    # for row in range(gw.nrows-1):
    #     stri += "s = {} \\/ s = {} \\/ s = {} -> s' != {} & s' != {} & s' != {}\n".format(((row+1)*gw.ncols -3),((row+1)*gw.ncols -2),((row+1)*gw.ncols -1),((row+1)*gw.ncols),((row+1)*gw.ncols +1),((row+1)*gw.ncols +2))
    # # need opposit of this aswell

    # file.write(stri)

    # stri =""
    # for edgeS in gw.edges:
    #     stri += "s' != {}\n".format(edgeS)
    # stri += "\n"
    # file.write(stri)
    
    # stri =""
    # obsborderlist = list(gw.obsborder)
    # for state in obsborderlist:
    #     stri += "s' != {}\n".format(state)
    # stri += "\n"
    # file.write(stri)

    # stri = ""
    # for s in tqdm(allowed_states):
    #     for orientation in [0,3,6,9]:
    #         if orientation == 0:
    #             st = s-gw.ncols
    #             if st >0 and st<gw.nstates:
    #                 stri += "s = {} /\\ st' = {} /\\ orientation = {} -> stepL != 3 /\\ stepL != 2\n".format(s,st, orientation)
    #             st = s-2*gw.ncols
    #             if st >0 and st<gw.nstates:
    #                 stri += "s = {} /\\ st' = {} /\\ orientation = {} -> stepL != 3 /\\ stepL != 2\n".format(s,st, orientation)
    #         if orientation == 3:
    #             st = s+1
    #             if st >0 and st<gw.nstates:
    #                 stri += "s = {} /\\ st' = {} /\\ orientation = {} -> stepL != 3 /\\ stepL != 2\n".format(s,st, orientation)
    #             st = s+2
    #             if st >0 and st<gw.nstates:
    #                 stri += "s = {} /\\ st' = {} /\\ orientation = {} -> stepL != 3 /\\ stepL != 2\n".format(s,st, orientation)
    #         if orientation == 6:
    #             st = s+gw.ncols
    #             if st >0 and st<gw.nstates:
    #                 stri += "s = {} /\\ st' = {} /\\ orientation = {} -> stepL != 3 /\\ stepL != 2\n".format(s,st, orientation)
    #             st = s+2*gw.ncols
    #             if st >0 and st<gw.nstates:
    #                 stri += "s = {} /\\ st' = {} /\\ orientation = {} -> stepL != 3 /\\ stepL != 2\n".format(s,st, orientation)
    #         if orientation == 9:
    #             st = s-1
    #             if st >0 and st<gw.nstates:
    #                 stri += "s = {} /\\ st' = {} /\\ orientation = {} -> stepL != 3 /\\ stepL != 2\n".format(s,st, orientation)
    #             st = s-2
    #             if st >0 and st<gw.nstates:
    #                 stri += "s = {} /\\ st' = {} /\\ orientation = {} -> stepL != 3 /\\ stepL != 2\n".format(s,st, orientation)

    # stri +="\n"
    # file.write(stri)

    file.write("\nstair' & orientation' = 3 & directionrequest' = 2 -> (stepL' = 0 & stepH' = 4) \/ ((stepL' = 1 & stepH' = 5)) \/ ((stepL' = 2 & stepH' = 6))\n")
    file.write("stair' & orientation' = 9 & directionrequest' = 4 -> (stepL' = 0 & stepH' = 2) \/ ((stepL' = 1 & stepH' = 1)) \/ ((stepL' = 2 & stepH' = 0))\n\n")
    file.write("!stair' -> stepH' = 3\n\n")
    

    ####################################### JONAS ############################



    for obs in gw.obstacles:
        if obs in allowed_states:
            file.write('!s = {}\n'.format(obs))

    # for obs in gw.obstacles:
    #     file.write('!s = {}\n'.format(obs))

    # for s in set(allowed_states):
    #     # stri = 'st = {} -> !s = {}\n'.format(s,s)
    #     # file.write(stri)
    #     stri = 'st = {} -> !s\' = {}\n'.format(s,s)
    #     file.write(stri)
    # #     ####################################### JONAS ############################
    #     stri = 'st\' = {} -> !s\' = {}\n'.format(s,s)
    #     file.write(stri)



    #     stri = 'st\' = {} -> !s = {}\n'.format(s,s)
    #     file.write(stri)

    #     # stri = 'st\' = {} -> (s\' != {}) /\\ (s\' + 1 != {}) /\\ (s\' != {}) /\\ (s\' + {} != {})\n'.format(s,s+1,s,s+gw.ncols,gw.ncols,s)
    #     # file.write(stri)

    #     # stri = 'st\' = {} -> (!s\' = {} + 1) /\\ (s\' + 1 != {}) /\\ (!s\' = {} + {} /\\ (s\' + {} != {})\n'.format(s,s,s,s,gw.ncols,gw.ncols,s)
    #     # file.write(stri)
        ####################################### JONAS ############################


##################################################################################

    # Writing sys_liveness
    file.write('\n[SYS_LIVENESS]\n')
    file.write("requestPending1 = 5\n")





    file.write('\n[ENV_LIVENESS]\n')
   
    # stri = ""
    # for visstate in set(nonbeliefstates):
    #     stri += "st != {} /\\ ".format(visstate)
    # stri = stri[:-4]
    # file.write(stri)

    # stri = ""
    # for Bstate in (set(allstates) - set(nonbeliefstates)):
    #     stri += "st = {} \/ ".format(Bstate)
    # stri = stri[:-4]
    # file.write(stri)

    # file.write("st' = {}".format(allstates[-2]))

    # file.write("st' = {}".format(115))