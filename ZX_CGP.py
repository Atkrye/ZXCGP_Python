from ZXNode import *
from EdgePointer import *
import random
import math
from QuantumSystem import *
from random import gauss
#Defines a CGP grid that can be evolved by some evolutionary algorithm
#Includes a method for converting said CGP grid into a QuantumSystem based on its active nodes
class ZX_CGP:
        #Params:
        #i, number of inputs
        #n, number of layers in grid
        #m, width of each layer in grid
        #o, number of outputs
        #a, max input arity of nodes
        #r, max output arity of nodes
        #c, max complexity of grid
        def __init__(self, i, n, m, o, a, r, c):
            self.i = i
            self.n = n
            self.m = m
            self.o = o
            self.a = a
            self.r = r
            self.c = c

            #Whether this individual phenotypically changed as a result of mutations applied. Initially false
            self.changed = False

            #Build grid

            #Layer 0 is inputs, Layer n + 1 is outputs
            self.grid = []

            #Build inputs
            inputs = []
            for input in range(i):
                inputs.append(ZXNode(0, input, 0, r))

            self.grid.append(inputs)

            #Build main grid
            for l in range(n):
                layer = []
                for node in range(m):
                    layer.append(ZXNode(l + 1, node, a, r))
                self.grid.append(layer)

            #Build outputs
            outputs = []
            for output in range(o):
                node = ZXNode(n + 1, output, 1, 0)
                #Outputs are inherently active
                node.set_active(True)
                outputs.append(node)

            self.grid.append(outputs)

        def copy(self):
            new = ZX_CGP(self.i,self.n,self.m,self.o,self.a,self.r,self.c)

            #Copy each input
            for input in range(self.i):
                source_node = self.get_node(0, input)
                target_node = new.get_node(0, input)

                #Copy
                self.copy_node(source_node, target_node)

            # Copy each node
            for x in range(self.n):
                for y in range(self.m):
                    source_node = self.get_node(x + 1, y)
                    target_node = new.get_node(x + 1, y)

                    #Copy
                    self.copy_node(source_node, target_node)

            # Copy each output
            for output in range(self.o):
                source_node = self.get_node(self.n + 1, output)
                target_node = new.get_node(self.n + 1, output)

                # Copy
                self.copy_node(source_node, target_node)

            new.active_pass()
            return new

        def copy_node(self, source, target):
            #Copy function
            target.set_function(source.get_function())
            #Copy phase
            target.set_phase(source.get_phase())
            #Copy control
            target.set_controlled(source.get_controlled())
            #Copy inputs
            for i in range(target.get_inputs_size()):
                target.set_input(i, self.copy_edge_pointer(source.get_input(i)))
            #Copy outputs
            for o in range(target.get_outputs_size()):
                target.set_output(o, self.copy_edge_pointer(source.get_output(o)))

        def copy_edge_pointer(self, e):
            if e == None:
                return None
            return EPointer(e.get_x(), e.get_y(), e.get_z())
        
        def __str__(self):
            ret = ""
            for i in range(len(self.grid)):
                for j in range(len(self.grid[i])):
                    ret = ret + str(self.grid[i][j]) + "\n"
            return ret

        #Method to count number of inactive inputs in the system. This is an important notion for training a system to be a function of
        #Its inputs
        def count_inactive_inputs(self):
            count = 0.0
            for inp in range(self.i):
                if not self.get_node(0, inp).get_active():
                    count += 1.0
            return count

        #Mutate the grid a certain number of times
        def mutate(self, num_mutations, phase_variance, phase_reset_granularity, disconnect_rate, phase_reset_rate):
            self.changed = False
            for mut in range(num_mutations):
                #Once mutated, do an active pass. This is expensive and could be optimized, but relative to
                #Quantum complexity this is arbitrary at higher numbers of qubits (max complexity)
                self.active_pass()
                #Keep retrying until mutation is successful
                success = False
                while not success:
                    #Pick a node. Can be hidden or output, not input (which is linear)
                    y = 1 + random.randint(0, self.n)
                    x = random.randint(0, len(self.grid[y]) - 1)
                    success = self.mutate_node(self.grid[y][x], phase_variance, phase_reset_granularity, disconnect_rate, phase_reset_rate)

        
        #Mutate the grid a certain number of times using a weighted mutation distribution across [edge_change, edge_disconnect, function_change, phase_change, phase_reset, control flip]
        def mutate_with_weights(self, num_mutations, phase_variance, phase_reset_granularity, mutation_weights):
            self.changed = False
            self.active_pass()
            mutation_counters = [0 for x in range(6)]
            for mut in range(num_mutations):
                #Once mutated, do an active pass. This is expensive and could be optimized, but relative to
                #Quantum complexity this is arbitrary at higher numbers of qubits (max complexity)
                self.active_pass()
                
                #Pick a node. Can be hidden or output, not input (which is linear)
                x = 1 + random.randint(0, self.n)
                y = random.randint(0, len(self.grid[x]) - 1)
                ret = self.mutate_node_with_weights(self.grid[x][y], phase_variance, phase_reset_granularity, mutation_weights)
                mutation_counters[ret[1]] += 1
            return mutation_counters

        #Function mutates a specific node
        def mutate_node(self, mutation_node, phase_variance, phase_reset_granularity, disconnect_rate, phase_reset_rate):
            #Uniformally, choose between function mutation, edge mutation and phase mutation
            prob = random.random()
            #Outputs can only have edge mutations, so will always act as wires (green with 0 phase)
            if mutation_node.get_x() == self.n + 1:
                return self.mutate_edge(mutation_node, disconnect_rate)
            if prob < 1 / 3:
                #Mutate function
                self.mutate_function(mutation_node, phase_reset_rate, phase_reset_granularity)
                #Function mutations cannot fail and do not change the active topology of the graph so cannot affect complexity.
                return True
            elif prob < 2 / 3:
                #Phase mutation
                self.mutate_phase(mutation_node, phase_variance, phase_reset_rate, phase_reset_granularity)
                #Phase mutations cannot fail and do not change the active topology of the graph so cannot affect complexity.
                return False
            else:
                #Edge mutation. This may fail by creating a graph with too high complexity
                return self.mutate_edge(mutation_node, disconnect_rate)
        
        #Function mutates a specific node
        def mutate_node_with_weights(self, mutation_node, phase_variance, phase_reset_granularity, mutation_weights):
            #Generate rng to sample weight distribution
            prob = random.random()
##            #Outputs can only have edge mutations, so will always act as wires (green with 0 phase). Therefore we only choose between edge mutation and edge disconnection for outputs
##            if mutation_node.get_x() == self.n + 1:
##                sum_weights = mutation_weights[0] + mutation_weights[1]
##                if prob <= (float(mutation_weights[0]) / float(sum_weights)):
##                        #Edge mutation, disconnect rate = 0.0
##                        return [self.mutate_edge(mutation_node, 0.0), 0]
##                else:
##                        #Edge deletion, disconnect rate = 1.0
##                        return [self.mutate_edge(mutation_node, 1.0), 1]

            #Calculate sum of weights
            sum_weights = 0.0
            for j in range(len(mutation_weights)):
                    sum_weights += float(mutation_weights[j])
            s = mutation_weights[0]
            #First is edge change
            if prob <= float(s) / sum_weights:
                    #Mutate edge
                    return [self.mutate_edge(mutation_node, 0.0), 0]
            #Second is edge disconnect
            s += mutation_weights[1]
            if prob <= float(s) / sum_weights:
                    #Disconnect edge
                    return [self.mutate_edge(mutation_node, 1.0), 1]
            #Third is function change
            s += mutation_weights[2]
            if prob <= float(s) / sum_weights:
                    #Mutate function
                    self.mutate_function(mutation_node, 0.0, phase_reset_granularity)
                    #Function mutations cannot fail and do not change the active topology of the graph so cannot affect complexity.
                    return [True, 2]
            #Fourth is phase change
            s += mutation_weights[3]
            if prob <= float(s) / sum_weights:
                #Mutate phase
                self.mutate_phase(mutation_node, phase_variance, 0.0, phase_reset_granularity)
                #Phase mutations cannot fail and do not change the active topology of the graph so cannot affect complexity.
                return [True, 3]
            #Fifth is phase reset
            s += mutation_weights[4]
            if prob <= float(s) / sum_weights:
                #Phase reset
                self.mutate_phase(mutation_node, phase_variance, 1.0, phase_reset_granularity)
                #Phase reset cant fail
                return [True, 4]
            #Sixth is control flip
            else:
                self.mutate_control(mutation_node)
                return [True, 5]

        def mutate_control(self, mutation_node):
                mutation_node.set_controlled(not mutation_node.get_controlled())

        #Method mutates the function of a specified node
        #Params are mutation_node, the node to mutate, and phase_reset_granularity; the degree to which phase
        #Should be reset. If the granularity is -1, we do not change the phase
        def mutate_function(self, mutation_node, phase_reset_rate, phase_reset_granularity):
            #Function mutation. Function can have 3 values but we already have 1 so we choose between the other 2

            if mutation_node.get_function() is ZXNode.Function_Set.H:
                #Is already hadamard
                if bool(random.getrandbits(1)):
                   #Pick green
                   mutation_node.set_function_green()
                else:
                   #Pick red
                   mutation_node.set_function_red()

            elif mutation_node.get_function() is ZXNode.Function_Set.G:
                #Is already Green
                if bool(random.getrandbits(1)):
                   #Pick green
                   mutation_node.set_function_hadamard()
                else:
                   #Pick red
                   mutation_node.set_function_red()

            else:
                #Is already Red
                if bool(random.getrandbits(1)):
                        #Pick green
                        mutation_node.set_function_green()
                else:
                        #Pick hadamard
                        mutation_node.set_function_hadamard()

            #Execute phase resets. If the granularity of this is -1, then phase remains unchanged
            #Otherwise, its set to rand(k) * 2pi / k e.g. 0 < phase < 2pi at some division of k
            if random.random() < phase_reset_rate and phase_reset_granularity is not -1:
                mutation_node.set_phase(random.randint(0, int(phase_reset_granularity)) * 2.0 * math.pi / float(phase_reset_granularity))

            #Check if we have updated the active graph
            if mutation_node.get_active():
                self.changed = True


        #Method mutates phase for a specific node
        def mutate_phase(self, mutation_node, phase_variance, phase_reset_rate, phase_reset_granularity):
            if random.random() < phase_reset_rate:
                    #Reset the phase according to the given granularity
                    factor = float(random.randint(0, int(phase_reset_granularity))) / phase_reset_granularity
                    mutation_node.set_phase(math.pi * 2 * factor)
            else:
                    #Phase mutation is phase + gaussian(0, variance)
                    new_phase = mutation_node.get_phase() + gauss(0.0, phase_variance)
                    while new_phase < 0:
                        new_phase += (math.pi * 2.0)
                    while new_phase > math.pi * 2.0:
                        new_phase += -(math.pi * 2.0)
                    mutation_node.set_phase(new_phase)

            #Check if we have updated the active graph. Hadamards do not use phase!
            if mutation_node.get_active() and mutation_node.get_function() is not ZXNode.Function_Set.H:
                self.changed = True

        #Get the node at a specific coordinate
        def get_node(self, x, y):
            return self.grid[x][y]

        #Method mutates an edge for a specific node
        def mutate_edge(self, mutation_node, disconnect_rate):
            #Pick an input to change
            input = random.randint(0, mutation_node.get_inputs_size() - 1)

            #Disconnect case - disconnect the input according to disconnect)rate
            if random.random() < disconnect_rate:
                        inp = mutation_node.get_input(input)
                        if inp is not None:
                            mutation_node.set_input(input, None)
                            self.get_node(inp.get_x(), inp.get_y()).set_output(inp.get_z(), None)
                        if mutation_node.get_active() and inp is not None:
                            self.changed = True
                        #Disconnects cannot complexify circuits so a complexity check is unnecessary
                        return True

            # Pick a node to use as input. Can be input or hidden with y < target mutant's y, not output
            if mutation_node.get_x() == 1:
                x = 0
            else:
                x = random.randint(0, mutation_node.get_x() - 1)
            y = random.randint(0, len(self.grid[x]) - 1)
            new_input = self.get_node(x, y)

            #Pick an output slot in the input node
            output = random.randint(0, new_input.get_outputs_size() - 1)

            #Aggressively take over that output. Clear old output if any
            #Store the old edges in case we have to undo the mutation
            old_edge_source = new_input.get_output(output)
            mutant_edge_target = mutation_node.get_input(input)
            #If there was an edge already connected to this slot delete it in its source
            if old_edge_source is not None:
                self.get_node(old_edge_source.get_x(), old_edge_source.get_y()).set_input(old_edge_source.get_z(), None)
            #If there was a node that the mutated edge was connected to, delete it in its target
            if mutant_edge_target is not None:
                self.get_node(mutant_edge_target.get_x(), mutant_edge_target.get_y()).set_output(mutant_edge_target.get_z(), None)
            #Set new input into input slot
            mutation_node.set_input(input, EPointer(x, y, output))
            #Take over new input's relevant output slot
            new_input.set_output(output, EPointer(mutation_node.get_x(), mutation_node.get_y(), input))

##            #Check if the new graph has unreasonable complexity
##            if not self.check_complexity():
##                #Complexity of the new circuit is too high. The executed mutation is undone
##                #Replace the old connections
##                if old_edge_source is not None:
##                    self.get_node(old_edge_source.get_x(), old_edge_source.get_y()).set_input(old_edge_source.get_z(), EPointer(x, y, output))
##                if mutant_edge_target is not None:
##                    self.get_node(mutant_edge_target.get_x(), mutant_edge_target.get_y()).set_output(mutant_edge_target.get_z(), EPointer(mutation_node.get_x(), mutation_node.get_y(), input))
##                new_input.set_output(output, old_edge_source)
##                mutation_node.set_input(input, mutant_edge_target)
##                return False
##            else:
            #Check if mutated node is active or if the old connection is active to check if the phenotype has changed
            is_node_active = mutation_node.get_active()
            if old_edge_source is not None:
                    is_old_source_active = self.get_node(old_edge_source.get_x(), old_edge_source.get_y()).get_active()
            else:
                    is_old_source_active = False
            if is_node_active or is_old_source_active:
                    self.changed = True
            return True

        #Method checks is a graph exceeds the required complexity by considering the number of active edges at any point in the graph
        def check_complexity(self):
            active = []
            #Get our initial output connections from the outputs
            for o in self.grid[self.n + 1]:
                for input in range(o.get_inputs_size()):
                    inp = o.get_input(input)
                    if inp is not None:
                        active.append(inp)

            #If active is bigger than the max complexity, then the check fails
            if len(active) > self.c:
                return False

            l = self.n + 1
            #Iterate from back to front, layer by layer, removing nodes that are present from the active list and adding their inputs
            while l > 0:
                active_nodes = []
                new_active = []
                #Check every currently considered node to see if it is in this layer
                for node in active:
                    #x coordinate check - is the node we're looking for in this layer?
                    if node.get_x() == l:
                        #Node is found in this layer. Add it to active nodes
                        active_nodes.append(node)
                    else:
                        #Node is not found in this layer. Add it to new_active so that it is checked next layer
                        new_active.append(node)

                #Iterate through every active node in this layer, removing duplicates and adding children to new active so that they are checked next layer

                #To remove duplicates create a string list to abuse python's set function with
                string_active = []
                for a in active_nodes:
                    string_active.append(str(a.get_x()) + ":" + str(a.get_y()))
                reduced = list(set(string_active))

                #Use this set to induce active elements created by active nodes in this layer
                for a in reduced:
                    sp = a.split(":")
                    x = sp[0]
                    y = sp[1]
                    anode = self.get_node(int(x), int(y))
                    for i in range(anode.get_inputs_size()):
                        if anode.get_input(i) is not None:
                            new_active.append(anode.get_input(i))

                #Copy new active list over
                active = new_active

                #Check complexity of the next active list
                if len(new_active) > self.c:
                    return False
                l = l - 1
            return True

        #Builds a matrix equivalent of the zx graph expressed in the phenotype
        #This (bloated) method treats the individual as a ZX Graph by simply ignoring inactive nodes as it iterates
        #Through the graph, replacing each node with its matrix equivalent and resolving connections using the construct_connection_matrix method
        def generate_qsystem(self):
            #Ensure we have an up-to-date notion of which nodes are active
            self.active_pass()

            #See QuantumSystem.py for usage
            qs = QSystem()
            grid = self.grid
            #Iterate front to back, building layers
            qs.new_layer()
            input_layer = self.grid[0]
            unresolved_inputs = []
            new_unresolved_inputs = []

            #Iterate over each input, generating a matrix for it
            for input in range(self.i):
                node = input_layer[input]

                #All inputs use 1 input
                inputs = 1

                #Find active outputs, add them to unresolved_inputs and increase the count of outputs for this node
                outputs = 0
                for output in range(node.get_outputs_size()):
                    if node.get_output(output) is not None:
                        #An output using a connection has been found. It is now checked to see if its source is active
                        potential_output = node.get_output(output)
                        if self.get_node(potential_output.get_x(), potential_output.get_y()).get_active():
                            unresolved_inputs.append(potential_output)
                            outputs += 1

                #Calculate Matrix for input. Input is always green with phase 0.0 e.g. a wire for 1 output
                qs.add_operator(node.calculate_operator(inputs, outputs))
                
            #Close the input layer
            qs.close_layer()

            #Iterate through each hidden layer
            for l in range(self.n):
                #Reset the new unresolved inputs list
                new_unresolved_inputs = []

                #List to store which inputs have been matched to which vertical index in the quantum system
                resolved_inputs = []

                #Start a new layer
                qs.new_layer()

                #input layer is index 0 so shuffle index one to right
                layer_index = l + 1
                found_node = False

                #Go through each hidden node in this layer
                for j in range(self.m):
                    #Get jth corresponding node
                    node = self.get_node(layer_index, j)

                    found_node = True
                    #A node is only relevant if its has already been tagged active
                    if node.get_active():
                        inputs = 0
                        outputs = 0
                        #Try to find some edge connecting to this node by searching over all unresolved edges. It is possible for a node to be active with no active inputs
                        #This would make the node a generator, but this behaviour is accommodated for and can be seen in ZXNode.py, in the ZXNode class, calculate_matrix() method
                        #We split the process into matching for individual inputs for the node. The purpose of doing this is to maintain a clear ordering on
                        #The inputs and outputs.
                        for e in range(node.get_inputs_size()):
                            for k in range(len(unresolved_inputs)):
                                #Get kth edge
                                input = unresolved_inputs[k]

                                #Check if kth edge has coordinates matching this node
                                if input.get_x() == node.get_x() and input.get_y() == node.get_y() and e == input.get_z():
                                    #Matching edge. Store the match as a resolved input and increase inputs counter
                                    resolved_inputs.append(input)
                                    inputs += 1

                        #Try to find active outputs. Note, since the node is active there should always be at least 1 active output
                        for k in range(node.get_outputs_size()):
                            #Get kth output
                            output = node.get_output(k)

                            #Check if the output is an active connection
                            if output is not None and self.get_node(output.get_x(), output.get_y()).get_active():
                                #New output. Store the new output as an unresolved input and increase outputs counter
                                new_unresolved_inputs.append(output)
                                outputs += 1

                        #Spit out a warning if there is a node with no active outputs
                        if outputs == 0:
                            print("Warning! CGP execution with active node with no active outputs!")

                        #We know now the complexity of the node, so can build a matrix representation and add it to the system
                        qs.add_operator(node.calculate_operator(inputs, outputs))

                #Only build the layer if an operator has been added

                if found_node:
                    #There may be edges that were not matched to a node in this layer. If the CGP representation is correctly coded these will all be
                    #Edges anticipated in future layers
                    for i in range(len(unresolved_inputs)):
                        #Get ith unresolved input
                        unresolved = unresolved_inputs[i]

                        #Have we matched this input?
                        already_matched = False
                        for j in range(len(resolved_inputs)):
                            #Get jth resolved input
                            resolved = resolved_inputs[j]
                            if unresolved.get_x() == resolved.get_x() and unresolved.get_y() == resolved.get_y() and unresolved.get_z() == resolved.get_z():
                                already_matched = True

                        #When we know that the ith input has not been resolved, we push that input to the bottom of the system, transition it with
                        #a wire operator and insert it into the new unresolved inputs list on the other side of the layer, e.g. resolve this later
                        if not already_matched:
                            #If the unresolved input has an x coordinate that indicates it should have been resolved by now e.g.
                            #Existed in an earlier layer than this, spit out a warning
                            if unresolved.get_x() < layer_index:
                                print("Warning! Unresolved connection points to node that should already be resolved!")
                            #Wire has form (1, 0), (0, 1) e.g. 2x2 identity Matrix
                            qs.add_operator(CMatrix([[1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j]]))
                            resolved_inputs.append(unresolved)
                            new_unresolved_inputs.append(unresolved)

                    #A new qubit may have been generated. A connection matrix is only necessary when qubits previously existed.

                    if len(unresolved_inputs) > 0:
                        #Close, adding a newly generated connection matrix (that reorders qubits so that they are passed from correct output to correct input
                        qs.close_layer_with_connection_matrix(self.calculate_connection_matrix(unresolved_inputs, resolved_inputs))
                    else:
                        qs.close_layer()

                #Update unresolved_inputs
                unresolved_inputs = new_unresolved_inputs

            #Build output layer
            # Go through each output node in this layer

            #List to store which inputs have been matched to which vertical index in the quantum system
            resolved_inputs = []

            #Start a new layer
            qs.new_layer()

            for j in range(self.o):
                # Get jth corresponding node
                node = self.get_node(self.n + 1, j)

                found_node = True
                inputs = 0

                #All output nodes have 1 output
                outputs = 1

                # Try to find some edge connecting to this node by searching over all unresolved edges. It is possible for a node to be active with no active inputs
                # This would make the node a generator, but this behaviour is accommodated for and can be seen in ZXNode.py, in the ZXNode class, calculate_matrix() method
                # We split the process into matching for individual inputs for the node. The purpose of doing this is to maintain a clear ordering on
                # The inputs and outputs.
                for e in range(node.get_inputs_size()):
                    for k in range(len(unresolved_inputs)):
                        # Get kth edge
                        input = unresolved_inputs[k]

                        # Check if kth edge has coordinates matching this node
                        if input.get_x() == node.get_x() and input.get_y() == node.get_y() and e == input.get_z():
                            # Matching edge. Store the match as a resolved input and increase inputs counter
                            resolved_inputs.append(input)
                            inputs += 1

                # We know now the complexity of the node, so can build a matrix representation and add it to the system
                qs.add_operator(node.calculate_operator(inputs, outputs))
            if len(unresolved_inputs) != 0:
                qs.close_layer_with_connection_matrix(self.calculate_connection_matrix(unresolved_inputs, resolved_inputs))
            else:
                qs.close_layer()


            #Compile the system
            qs.compile()
            return qs

        #Recalculates which nodes in the individual are active by sweeping backwards from the outputs.
        #Code largely based on check_complexity method in this module
        def active_pass(self):
            #Initially, set all nodes (except outputs) to inactive. This is to ensure no nodes which are not active are
            #Left active from the previous evaluation
            for x in range(self.n):
                    for y in range(self.m):
                            self.grid[x + 1][y].set_active(False)

            #Inputs are initially inactive too
            for i in range(self.i):
                    self.grid[0][i].set_active(False)
            
            active = []
            #Get our initial output connections from the outputs
            for o in self.grid[self.n + 1]:
                #Outputs are always active
                o.set_active(True)
                for input in range(o.get_inputs_size()):
                    inp = o.get_input(input)
                    if inp is not None:
                        active.append(inp)

            #If active is bigger than the max complexity, then the check fails
            if len(active) > self.c:
                return False

            l = self.n + 1
            #Iterate from back to front, layer by layer, removing nodes that are present from the active list and adding their inputs
            while l > 0:
                l = l - 1
                active_nodes = []
                new_active = []
                #Check every currently considered node to see if it is in this layer
                for node in active:
                    #y coordinate check
                    if node.get_x() == l:
                        #Node is found in this layer. Add it to active nodes
                        active_nodes.append(node)
                    else:
                        #Node is not found in this layer. Add it to new_active so that it is checked next layer
                        new_active.append(node)

                #Iterate through every active node in this layer, removing duplicates and adding children to new active so that they are checked next layer

                #To remove duplicates create a string list to abuse python's set function with
                string_active = []
                for a in active_nodes:
                    string_active.append(str(a.get_x()) + ":" + str(a.get_y()))
                reduced = list(set(string_active))
                #Use this set to induce active elements created by active nodes in this layer
                for a in reduced:
                    sp = a.split(":")
                    x = sp[0]
                    y = sp[1]
                    anode = self.get_node(int(x), int(y))
                    
                    for i in range(anode.get_inputs_size()):
                        if anode.get_input(i) is not None:
                            new_active.append(anode.get_input(i))
                    #Mark the active node
                    anode.set_active(True)
                #Copy new active list over
                active = new_active

        #Takes two lists, in and out, which are assumed to be two orderings on the same set of EdgePointers
        #Returns a connection matrix that maps each qubit state to its transformed state to provide the implied set of swaps
        def calculate_connection_matrix(self, inE, outE):
            if len(inE) != len(outE):
                #Lists should be equal size, else the connection matrix is incorrect
                print("Warning! generating connection matrix of mismatched size:" + str(inE) + " vs. " + str(outE))
                print(self)
            size = int(math.pow(2, len(inE)))

            #Initiate connection matrix as zeros
            cm = [[0 + 0j for i in range(size)] for j in range(size)]

            #Build bit transformation. This provides the index mapping for each qubit in the system
            bittrans = [0 for i in range(len(inE))]

            #Cycle in each edge pointer, trying to find its match in the out. The found match is the index mapping for that qubit
            for i in range(len(inE)):
                un = inE[i]
                #print("Check " + str(i) + ": " + str(un))
                found = False
                for j in range(len(outE)):
                    re = outE[j]
                    #print("Against " + str(j) + ": " + str(re))
                    #Check if this is a match
                    if un.get_x() == re.get_x() and un.get_y() == re.get_y() and un.get_z() == re.get_z():
                        #We have found a match
                        if found:
                            #Second match! Provided inputs are flawed
                            print("Warning! the provided input, " + str(un) + ", was found twice or more in the output.")
                            print(self)
                        else:
                            bittrans[i] = j
                            found = True
                    #else:
                    #    print("Fail")
                if not found:
                    #This qubit has no out match, Provided inputs are flawed
                    print("Warning! the provided input, " + str(un) + ", was not found in the output.")
            #Bit transformation contructed. Now iterate through bit form of each index
            #print(bittrans)

            #Now each state maps to the state generated by applying the bit transformation to it
            #Cycle through each state
            for state in range(size):

                #Converts state to bit state, a bitstring array
                bstate = list("{0:b}".format(state))

                #Ensures the bstate is the expected length (for smaller values)
                while len(bstate) < len(inE):
                    bstate = ["0"] + bstate

                #Transform the bit state using the transformation
                newstate = ["0"] * len(inE)

                #Map each bit
                for bit in range(len(inE)):
                    newstate[bittrans[bit]] = bstate[bit]

                #Convert the bitstring array, newstate, into an integer using base 2 formatting
                nstate = int(''.join(map(str, newstate)), 2)
                #Store this change in the connection matrix
                cm[state][nstate] = 1 + 0j
            return CMatrix(cm)





zx = ZX_CGP(2,3,3,2,6,6,3)
zx.mutate(100, 0.3, 16, 0.1, 0.1)
#print(zx)
zx.mutate(1, 0.3, 16, 0.1, 0.1)
#print(zx)
zx.mutate(1, 0.3, 16, 0.1, 0.1)
#print(zx)
zx.mutate(1, 0.3, 16, 0.1, 0.1)
#print(zx)
zx.mutate(1, 0.3, 16, 0.1, 0.1)
#print(zx)

#Linear transformation expected
inE = [EPointer(0,0,0),EPointer(0,0,1)]
outE = [EPointer(0,0,0),EPointer(0,0,1)]
#print(ZX_CGP.calculate_connection_matrix(inE, outE))

#Swap transformation expected
inE = [EPointer(0,0,0),EPointer(0,1,1)]
outE = [EPointer(0,1,1),EPointer(0,0,0)]
#print(ZX_CGP.calculate_connection_matrix(inE, outE))

#Linear transformation expected
inE = [EPointer(0,0,0),EPointer(0,0,1),EPointer(0,0,3)]
outE = [EPointer(0,0,0),EPointer(0,0,1),EPointer(0,0,3)]
#print(ZX_CGP.calculate_connection_matrix(inE, outE))

#Wire tensor Swap transformation expected
inE = [EPointer(0,0,0),EPointer(0,0,3),EPointer(0,0,1)]
outE = [EPointer(0,0,0),EPointer(0,0,1),EPointer(0,0,3)]
#print(ZX_CGP.calculate_connection_matrix(inE, outE))

#Swap tensor Wire transformation expected
inE = [EPointer(0,0,1),EPointer(0,0,0),EPointer(0,0,3)]
outE = [EPointer(0,0,0),EPointer(0,0,1),EPointer(0,0,3)]
#print(ZX_CGP.calculate_connection_matrix(inE, outE))

#Swap tensor Wire * Wire tensor Swap transformation expected
inE = [EPointer(0,0,1),EPointer(0,0,0),EPointer(0,0,3)]
outE = [EPointer(0,0,3),EPointer(0,0,0),EPointer(0,0,1)]
#print(ZX_CGP.calculate_connection_matrix(inE, outE))

#q = zx.generate_qsystem()
#print("Matrix")
#print(zx.generate_qsystem().get_compiled_version().get_layer(0))
