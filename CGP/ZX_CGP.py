from CGP.ZXNode import *
from CGP.EdgePointer import *
import random
import math
from CGP.QuantumSystem import *
from random import gauss
#Defines a CGP grid that can be evolved by some evolutionary algorithm
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

        def __str__(self):
            ret = ""
            for i in range(len(self.grid)):
                for j in range(len(self.grid[i])):
                    ret = ret + str(self.grid[i][j]) + "\n"
            return ret

        #Mutate the grid a certain number of times
        def mutate(self, num_mutations, phase_variance, phase_reset_granularity):
            for mut in range(num_mutations):
                print(self)
                #Keep retrying until mutation is successful
                success = False
                while not success:
                    #Pick a node. Can be output or hidden, not input
                    y = 1 + random.randint(0, self.n)
                    x = random.randint(0, len(self.grid[y]) - 1)
                    success = self.mutate_node(self.grid[y][x], phase_variance, phase_reset_granularity)

        #Function mutates a specific node
        def mutate_node(self, mutation_node, phase_variance, phase_reset_granularity):
            #Uniformally, choose between function mutation, edge mutation and phase mutation
            prob = random.random()
            if prob < 1 / 3:
                #Mutate function
                self.mutate_function(mutation_node, phase_reset_granularity)
                #Function mutations cannot fail and do not change the active topology of the graph so cannot affect complexity.
                return True
            elif prob < 2 / 3:
                #Phase mutation
                self.mutate_phase(mutation_node, phase_variance)
                #Phase mutations cannot fail and do not change the active topology of the graph so cannot affect complexity.
                return False
            else:
                #Edge mutation. This may fail by creating a graph with too high complexity
                return self.mutate_edge(mutation_node)

        #Method mutates the function of a specified node
        def mutate_function(self, mutation_node, phase_reset_granularity):
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
                if __name__ == '__main__':
                    if bool(random.getrandbits(1)):
                       #Pick green
                       mutation_node.set_function_green()
                    else:
                       #Pick hadamard
                       mutation_node.set_function_hadamard()

            #Execute phase resets. If the granularity of this is -1, then phase remains unchanged
            #Otherwise, its set to rand(k) * 2pi / k e.g. 0 < phase < 2pi at some division of k
            if phase_reset_granularity is not -1:
                mutation_node.set_phase(random.randint(0, int(phase_reset_granularity)) * 2.0 * math.pi / float(phase_reset_granularity))

            #Check if we have updated the active graph
            if mutation_node.get_active():
                self.changed = True

        #Method mutates phase for a specific node
        def mutate_phase(self, mutation_node, phase_variance):
            #Phase mutation is phase + gaussian(0, variance)
            mutation_node.set_phase(mutation_node.get_phase() + gauss(0.0, phase_variance))

            #Check if we have updated the active graph. Hadamards do not use phase!
            if mutation_node.get_active() and mutation_node.get_function() is not ZXNode.Function_Set.H:
                self.changed = True

        #Get the node at a specific coordinate
        def get_node(self, x, y):
            return self.grid[x][y]

        #Method mutates an edge for a specific node
        def mutate_edge(self, mutation_node):
            #Pick an input to change
            input = random.randint(0, mutation_node.get_inputs_size() - 1)

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
            if old_edge_source is not None:
                #If there was an edge already connected to this slot delete it in its source
                self.get_node(old_edge_source.get_x(), old_edge_source.get_y()).set_input(old_edge_source.get_z(), None)
            if mutant_edge_target is not None:
                #If there was a node that the mutated edge was connected to, delete it in its target
                self.get_node(mutant_edge_target.get_x(), mutant_edge_target.get_y()).set_output(mutant_edge_target.get_z(), None)
            #Set new input into input slot
            mutation_node.set_input(input, EPointer(x, y, output))
            #Take over new input's relevant output slot
            new_input.set_output(output, EPointer(mutation_node.get_x(), mutation_node.get_y(), input))

            #Check if the new graph has unreasonable complexity
            if not self.check_complexity():
                print("Complexity fail!")
                #Complexity of the new circuit is too high. The executed mutation is undone
                #Replace the old connections
                if old_edge_source is not None:
                    self.get_node(old_edge_source.get_x(), old_edge_source.get_y()).set_input(old_edge_source.get_z(), EPointer(x, y, output))
                if mutant_edge_target is not None:
                    self.get_node(mutant_edge_target.get_x(), mutant_edge_target.get_y()).set_output(mutant_edge_target.get_z(), EPointer(mutation_node.get_x(), mutation_node.get_y(), input))
                new_input.set_output(output, old_edge_source)
                mutation_node.set_input(input, None)
                return False
            else:
                #Check if mutated node is active or if the old connection is active to check if the phenotype has changed
                if not mutation_node.get_active() or (old_edge_source is not None and not self.get_node(old_edge_source.get_x(), old_edge_source.get_y()).get_active()):
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
                l = l - 1
                active_nodes = []
                new_active = []
                #Check every currently considered node to see if it is in this layer
                for node in active:
                    #y coordinate check
                    if node.get_y() == l:
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
            return True

        #Builds a matrix equivalent of the zx graph expressed in the phenotype
        def generate_qsystem(self):
            #Ensure we have an up-to-date notion of which nodes are active
            self.active_pass()

            #See QuantumSystem.py for usage
            q = QSystem()
            grid = self.grid
            #Iterate front to back, building layers
            q.new_layer()
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
                qs.add_operator(node.calculate_matrix(inputs, outputs))

            #Iterate through each hidden layer
            for l in range(self.n + 1):
                #Reset the new unresolved inputs list
                new_unresolved_inputs = []

                #List to store which inputs have been matched to which vertical index in the quantum system
                resolved_inputs = []

                #Close the previous layer and start a new one
                qs.new_layer()

                #input layer is index 0 so shuffle index one to right
                layer_index = l + 1

                #Go through each hidden node in this layer
                for j in range(self.m):
                    #Get jth corresponding node
                    node = self.get_node(layer_index, j)

                    #A node is only relevant if its has already been tagged active
                    if node.get_active():
                        inputs = 0
                        outputs = 0
                        #Try to find some edge connecting to this node by searching over all unresolved edges. It is possible for a node to be active with no active inputs
                        #This would make the node a generator, but this behaviour is accommodated for and can be seen in ZXNode.py, in the ZXNode class, calculate_matrix() method
                        #We split the process into matching for individual inputs for the node. The purpose of doing this is to maintain a clear ordering on
                        #The inputs and outputs.
                        for e in range(node.get_inputs_size):
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
                        qs.add_operator(node.calculate_matrix(inputs, outputs))

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
                        if unresolved.get_y() < layer_index:
                            print("Warning! Unresolved connection points to node that should already be resolved!")
                        #Wire has form (1, 0), (0, 1) e.g. 2x2 identity Matrix
                        qs.add_operator(CMatrix([[1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j]]))
                        resolved_inputs.append(unresolved)
                        unresolved_inputs.append(unresolved)

                #Update unresolved_inputs
                unresolved_inputs = new_unresolved_inputs

            #Close the last layer
            qs.close_layer()

            #Compile the system
            qs.compile()
            return qs

        def active_pass(self):
            return None





zx = ZX_CGP(2,3,3,2,2,4,4)
zx.mutate(10000, 0.3, 16)
print(zx)