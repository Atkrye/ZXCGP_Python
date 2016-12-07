from CGP.CMatrix import CMatrix
from CGP.QuantumState import QState
import math
#Class for building and using a Quantum System made of CMatrix operators and basis measurement layers
class QSystem:

    #Param not required. Flags set to false used to indicate whether the system is currently building or compiled
    def __init__(self):
        self.layer_unfinished = False
        self.compiled = False
        self.is_compiled_system = False
        self.layers = []
        self.measure_flags = []
        self.current_layer = []
        self.compiled_system = None

    #Can be used to set a flag indicating that this is the compiled form of another system. This means that it should not be compiled and should be executed as is.
    def compiled_flag(self):
        self.is_compiled_system = True

    #Clears the system so that it can be rebuilt
    def clear(self):
        self.layer_unfinished = False
        self.compiled = False
        self.is_compiled_system = False
        self.layers = []
        self.measure_flags = []
        self.current_layer = []
        self.compiled_system = None

    #Adds a new layer. If an old layer still existed then it is tensored together and stored in the layers array
    def new_layer(self):
        #If there is an unfinished layer then we close that layer
        if(self.layer_unfinished):
            self.close_layer()
        self.layer_unfinished = True

    def close_layer(self):
        m = CMatrix([[1 + 0j]])
        for i in range(len(self.current_layer)):
           m = m / self.current_layer[i]
        self.layers.append(m)
        self.measure_flags.append(False)
        self.layer_unfinished = False
        self.current_layer = []

    #Adds a matrix operator to the current layer
    def add_operator(self, operator):
        self.current_layer.append(operator)

    #Adds a measurement layer, flagging it. Input is an array of integers that indicate which qubits should be measured
    def add_measurement_layer(self, measure_qubits):
        self.layers.append(measure_qubits)
        self.measure_flags.append(True)

    # Compiles the system into a simpler form by collapsing multiplications
    def compile(self):
        self.compiled = True
        self.compiled_system = QSystem()
        self.compiled_system.new_layer()
        self.compiled_system.compiled_flag()
        m = None
        for i in range(len(self.layers)):
            if self.measure_flags[i]:
                if m is not None:
                    self.compiled_system.add_operator(m)
                    self.compiled_system.new_layer()
                    m = None
                self.compiled_system.add_measurement_layer(self.layers[i])
            else:
                if m is None:
                    m = self.layers[i]
                else:
                    m = self.layers[i] * m
        if m is not None:
            self.compiled_system.add_operator(m)
            self.compiled_system.close_layer()
            m = None

    #Applies the system to some input quantum state
    def apply(self, input_state):
        if(self.compiled):
            return self.compiled_system.apply(input_state)
        else:
            if not self.is_compiled_system:
                print("Warning: The system executed has not been compiled!")
            current_state = input_state
            for i in range(len(self.layers)):
                #Get current layer
                current_layer = self.layers[i]
                #Check if this is a measurement layer
                if(self.measure_flags[i]):
                    #Perform necessary measurements
                    for j in current_layer:
                        current_state = current_state.measure_qubit(j)
                else:
                    current_state = current_state.apply_operator(current_layer)
            return current_state

CNOT = CMatrix([[1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 1 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 0 + 0j, 0 + 0j, 1 + 0j],[0 + 0j, 0 + 0j, 1 + 0j, 0 + 0j]])
CZ = CMatrix([[1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 1 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 0 + 0j, 1 + 0j, 0 + 0j],[0 + 0j, 0 + 0j, 0 + 0j, -1 + 0j]])
SWAP = CMatrix([[1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 0 + 0j, 1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 0 + 0j, 0 + 0j, 1 + 0j]])
#Teleportation Example
qs = QSystem()
qs.new_layer()
#Wire, Hadamard, Wire
qs.add_operator(CMatrix([[1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j]]))
qs.add_operator(CMatrix([[math.sqrt(1 / 2) + 0j,math.sqrt(1 / 2) + 0j],[math.sqrt(1 / 2) + 0j, -(math.sqrt(1 / 2)) + 0j]]))
qs.add_operator(CMatrix([[1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j]]))
qs.new_layer()
#Wire, CNOT
qs.add_operator(CMatrix([[1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j]]))
qs.add_operator(CMatrix([[1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 1 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 0 + 0j, 0 + 0j, 1 + 0j],[0 + 0j, 0 + 0j, 1 + 0j, 0 + 0j]]))
qs.new_layer()
#CNOT, Wire
qs.add_operator(CMatrix([[1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 1 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 0 + 0j, 0 + 0j, 1 + 0j],[0 + 0j, 0 + 0j, 1 + 0j, 0 + 0j]]))
qs.add_operator(CMatrix([[1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j]]))
qs.new_layer()
#Hadamard, Wire, Wire
qs.add_operator(CMatrix([[math.sqrt(1 / 2) + 0j,math.sqrt(1 / 2) + 0j],[math.sqrt(1 / 2) + 0j, -(math.sqrt(1 / 2)) + 0j]]))
qs.add_operator(CMatrix([[1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j]]))
qs.add_operator(CMatrix([[1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j]]))
qs.close_layer()
#Measurement
qs.add_measurement_layer([0,1])
#Corrections
#Wire, CNOT
qs.new_layer()
qs.add_operator(CMatrix([[1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j]]))
qs.add_operator(CNOT)
#SWAP, Wire
qs.new_layer()
qs.add_operator(SWAP)
qs.add_operator(CMatrix([[1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j]]))
#Wire, CNOT
qs.new_layer()
qs.add_operator(CMatrix([[1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j]]))
qs.add_operator(CZ)
#SWAP, Wire
qs.new_layer()
qs.add_operator(SWAP)
qs.add_operator(CMatrix([[1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j]]))
qs.close_layer()
qs.compile()

#Test on (A|0| + B|1|)|00| with A = 1/2 and B = root(3)/4
state = QState([math.sqrt(1/4) + 0j, 0 + 0j, 0 + 0j, 0 + 0j, math.sqrt(3/4) + 0j, 0 + 0j,0 + 0j, 0 + 0j])
#Results are expected to be |00|(A|0| + B|1|) or requiring corrections as defined by TP circuits
#print("Attempt 1")
#print(qs.apply(state))
#print("Attempt 2")
#print(qs.apply(state))
#print("Attempt 3")
#print(qs.apply(state))