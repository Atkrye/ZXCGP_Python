from CMatrix import *
import math
import cmath
def enum(**named_values):
    return type('Enum', (), named_values)


class ZXNode:
    Function_Set = enum(H = "H", R = "R", G = "G")

    #A is max inputs, r is max outputs
    def __init__(self, x, y, a, r):
        self.a = a;
        self.r = r;
        self.function = ZXNode.Function_Set.G
        self.phase = 0.0
        self.inputs = [None for i in range(a)]
        self.outputs = [None for i in range(r)]
        self.x = x
        self.y = y
        self.active = False
        self.controlled = False

    def get_inputs_size(self):
        return self.a

    def get_outputs_size(self):
        return self.r

    def count_active_inputs(self):
        count = 0
        for a in range(self.a):
            if self.inputs[a] is not None:
                count += 1
        return count

    def get_controlled(self):
        return self.controlled

    def set_controlled(self, c):
        self.controlled = c

    def __str__(self):
        rep = "(" + str(self.x) + "," + str(self.y) + "): " + self.function + " " + str(self.phase)
        if self.active:
            rep += " ACTIVE"
        if self.controlled:
                rep += " C-GATE"
        rep += "\nInputs: "

        for i in range(len(self.inputs)):
            if self.inputs[i] is None:
                rep += "None, "
            else:
                rep += "(" + str(self.inputs[i].get_x()) + "," + str(self.inputs[i].get_y()) + " - " + str(self.inputs[i].get_z()) + "),"
        rep += "\nOutputs: "
        for o in range(len(self.outputs)):
            if self.outputs[o] is None:
                rep += "None, "
            else:
                rep += "(" + str(self.outputs[o].get_x()) + "," + str(self.outputs[o].get_y()) + " - " + str(self.outputs[o].get_z())+ "),"
        return rep

    def get_y(self):
        return self.y

    def get_x(self):
        return self.x

    #Get the node's function
    def get_function(self):
        return self.function

    #Get the node's phase
    def get_phase(self):
        return self.phase

    #Gets an input at the specified index
    def get_input(self, index):
        return self.inputs[index]

    #Gets an output at the specified index
    def get_output(self, index):
        return self.outputs[index]

    def set_input(self, input_index, input_node):
        self.inputs[input_index] = input_node

    def set_output(self, output_index, output_node):
        self.outputs[output_index] = output_node

    def set_function_hadamard(self):
        self.function = ZXNode.Function_Set.H

    def set_function_green(self):
        self.function = ZXNode.Function_Set.G

    def set_function_red(self):
        self.function = ZXNode.Function_Set.R

    def set_function(self, new_function):
        self.function = new_function

    def set_phase(self, new_phase):
        self.phase = new_phase

    def get_active(self):
        return self.active

    def set_active(self, new_active):
        self.active = new_active

    #Calculates a Complex Matrix CMatrix (see CMatrix.py for usage) for a fixed number of inputs and outputs using the nodes current phase and function
    #See function specific methods calculate_green(i,o), calculate_red(i,o) and calculate_hadamard(i,o) for more details
    def calculate_operator(self, inputs, outputs):
        #Controlled only matters if the node is 'square' with more than 1 qubit
        if(self.controlled and inputs == outputs and inputs != 1):
            #Generate a 1x1 matrix and place it in a controlled matrix
            return ZXNode.generate_controlled(inputs - 1, self.calculate_operator(1, 1))
        if self.function is ZXNode.Function_Set.H:
            #Calculate Hadamard CMatrix
            return ZXNode.calculate_hadamard(inputs, outputs)
        elif self.function is ZXNode.Function_Set.R:
            #Calculate Red Node CMatrix
            return self.calculate_general_red(inputs, outputs, self.phase)
        else:
            #Default calculate Green Node CMatrix
            return ZXNode.calculate_general_green(inputs, outputs, self.phase)

    #Generates Complex Matrix representation of a Hadamard node for a fixed number of inputs and outputs
    #We interpret this as Green(1, outputs, 0 phase) * conventional Hadamard Matrix * Green(inputs, 1, 0 phase)
    #E.g. Green splitters on either side of a conventional Hadamard (1/root(2) [[1, 1],[1, -1]]) and 1-input 1-output scenarios then generating
    #A conventional hadamard operation as Green(1, 1, 0 phase) is effectively a wire
    @staticmethod
    def calculate_hadamard(inputs, outputs):
        inmatrix = ZXNode.calculate_general_green(inputs, 1, 0.0)
        outmatrix = ZXNode.calculate_general_green(1, outputs, 0.0)
        h = ZXNode.generate_hadamard_matrix()
        return outmatrix * h * inmatrix

    #Generates a conventional 1-input, 1-output Matrix of a Hadamard gate
    @staticmethod
    def generate_hadamard_matrix():
        return CMatrix([[(1 / math.sqrt(2)) + 0j, (1 / math.sqrt(2)) + 0j], [(1 / math.sqrt(2)) + 0j, (-1 / math.sqrt(2)) + 0j]])

    #Generates a CMatrix for a Green Node for a certain number of inputs, outputs and phase.
    #This is a 2^input width * 2^input high Complex Matrix with all elements set to 0 except the first (0, 0) = 1 + 0i
    #And the last (2^input, 2^output) = e ^ (i * phase)
    #All generator cases (0 inputs) are resolved in the green operator as both Hadamard & Red with 0 inputs
    #Are instantiated using a 0 input Green (in Hadamard, we have 0-in, 1-out Green followed by H, followed by 1-in, O-out Green)
    #(in Red, we have 0 x H = [[1.0 + 0j]] then 0-in, O-out Green, then O x H masking the output).
    #Behaviour in the generator case is resolved as generating a bell state |q ^ O> = cos(phase).|0 ^ O> + sin(phase).|1 ^ O> as this
    #Generates a valid distribution which has a square sum of 1
    #There is also a destructor case (0 outputs) that can occur when an input of a ZX_CGP individual has no outputs.
    #That qubit must be closed/destroyed so that the constructed QuantumSystem.py QSystem can act on an input of a
    #Prespecified size without producing an error when an input is unused (e.g. has 0 outputs).
    @staticmethod
    def calculate_general_green(inputs, outputs, phasein):
        inbits = int(math.pow(2,inputs))
        outbits = int(math.pow(2,outputs))

        #By the nature of ZX_CGP, there is never a 0-in, 0-out case as 0-out can only occur in input nodes which
        #Are inherently 1-in. If you are designing a system where these may occur please adjust this catchment accordingly
        if inputs == 0 and outputs == 0:
            print("Warning! 0-input, 0-output Green node attempted! Aborting matrix contstruction!")
            return None
        
        #Catch the generator case
        if inputs == 0:
            #Generator has cos(phase) |0 ^ O> + sin(phase) |1 ^ O> e.g. all other mixed states have p = 0
            matrix = [[0 + 0j for y in range(outbits)]]
            #|0 ^ O> state
            matrix[0][0] = math.cos(phasein) + 0j
            #|1 ^ O> state
            matrix[0][outbits - 1] = math.sin(phasein) + 0j
            return CMatrix(matrix)

        #Catch the destructor case
        if outputs == 0:
            #Destructors are inherently not trace preserving. In fact, a 0 phase destructor will only store states where the destroyed
            #Qubit has value |0>, so if all states are in the |1> case, then the resultant QState is literally empty
            matrix = [[0 + 0j] for x in range(inbits)]
            #|0 ^ I> state
            matrix[0][0] = math.cos(phasein) + 0j
            #|1 ^ I> state
            matrix[inbits - 1][0] = math.sin(phasein) + 0j
            #Since these square sum to 1 this cannot be trace increasing
            return CMatrix(matrix)

            
        #Matrices are stored column by column
        matrix = [[0 + 0j for y in range(outbits)] for x in range(inbits)]
        #Top left element is simply 1
        matrix[0][0] = 1 + 0j
        #Bottom right element is e ^ (i * phase)
        matrix[inbits - 1][outbits - 1] = cmath.exp(float(phasein) * 1j)
        return CMatrix(matrix)

    #Generates a CMatrix for a Red node for a certain number of inputs, outputs and phase
    #This is generally interpreted as a layer of Hadamards on either side of a green node performing the same in,out,phase function
    #For more information see ZX Calculus literature
    @staticmethod
    def calculate_general_red(inputs,outputs,phase):
        h = ZXNode.generate_hadamard_matrix()

        #Set up in and out matrices
        inmatrix = CMatrix([[1 + 0j]])
        outmatrix = CMatrix([[1 + 0j]])

        #Expand in and out matrices as a hadamard gate for each input and output
        for i in range(inputs):
            #Backslash operator indicates tensor product
            inmatrix = inmatrix / h
        for j in range(outputs):
            outmatrix = outmatrix / h

        green = ZXNode.calculate_general_green(inputs, outputs,phase)
        return outmatrix * green * inmatrix

    @staticmethod
    def generate_controlled(control_bits, controlled_matrix):
        size = int(math.pow(2, control_bits + 1))
        M = [[0 + 0j for x in range(size)] for y in range(size)]
        #Set all diagnol bits to 1
        for i in range(size - 2):
            M[i][i] = 1 + 0j
        M[size - 2][size - 2] = controlled_matrix.get_raw_data()[0][0]
        M[size - 2][size - 1] = controlled_matrix.get_raw_data()[0][1]
        M[size - 1][size - 2] = controlled_matrix.get_raw_data()[1][0]
        M[size - 1][size - 1] = controlled_matrix.get_raw_data()[1][1]
        return CMatrix(M)


inp = int(1)
out = int(2)
phase = 0.0
#print(ZXNode.calculate_hadamard(inp,out))
#print(ZXNode.calculate_general_green(0,2,math.pi / 4))
#print(ZXNode.calculate_general_green(2,0,math.pi / 4))()) * a.calculate_operator(2, 2) * (ZXNode.generate_hadamard_matrix() / ZXNode.calculate_general_green(1,1,0.0)))
