from CMatrix import *
import math
import random

#Class for instantiating, storing and manipulating a quantum state
class QState:

    #Parameter is raw 1D array of Complex values.
    def __init__(self, init_data):
        self.state_data = CMatrix([init_data]*1)

    def __str__(self):
        return str(self.state_data)

    #Gets raw representation of the instance
    def get_raw_data(self):
        return self.state_data.get_raw_data()

    #Performs a basis measurement on a specified qubit
    def measure_qubit(self, qubit):
        state_data = self.get_raw_data()
        self_qubits = int(math.log(len(state_data[0]), 2))
        qubit_flip = int(math.pow(2, self_qubits - (qubit + 1)))
        qubit_iterations = int(math.pow(2, qubit + 1))
        state_zero = True
        zero_total = 0.0
        one_total = 0.0
        for i in range(qubit_iterations):
            for j in range(qubit_flip):
                val = state_data[0][(i * qubit_flip) + j]
                new_val = (val.real * val.real) + (val.imag * val.imag)
                if state_zero:
                    zero_total += new_val
                else:
                    one_total += new_val
            state_zero = not state_zero
        prob_total = zero_total + one_total
        prob = random.random() * prob_total
        mod = 0
        if prob < zero_total:
            #Qubit is measured as being in state 0
            state_zero = True
            mod = math.sqrt(zero_total)
        else:
            #Qubit is measured as being in state 1
            state_zero = False
            mod = math.sqrt(one_total)
        new_data = [0 + 0j for x in range(len(state_data[0]))]
        for i in range(qubit_iterations):
            for j in range(qubit_flip):
                if state_zero:
                    new_data[(i * qubit_flip) + j] = state_data[0][(i * qubit_flip) + j] / mod
            state_zero = not state_zero
        return QState(new_data)

    def apply_operator(self, op_matrix):
        return QState((op_matrix * self.state_data).get_raw_data()[0])


state = QState([math.sqrt(1/4) + 0j, 0 + 0j, 0 + 0j, 0 + 0j,math.sqrt(3/4) + 0j, 0 + 0j,0 + 0j, 0 + 0j])

w = CMatrix([[1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j]])
h = CMatrix([[math.sqrt(1 / 2) + 0j,math.sqrt(1 / 2) + 0j],[math.sqrt(1 / 2) + 0j, -(math.sqrt(1 / 2)) + 0j]])
CNOT = CMatrix([[1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 1 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 0 + 0j, 0 + 0j, 1 + 0j],[0 + 0j, 0 + 0j, 1 + 0j, 0 + 0j]])
CNOTU = CMatrix([[1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 0 + 0j, 0 + 0j, 1 + 0j],[0 + 0j, 0 + 0j, 1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j, 0 + 0j, 0 + 0j]])

#print("Matrix:")
#print((h/w/w) * (CNOT/w) * (w/CNOT) * (w/h/w))
#print("Result:")
#print(state.apply_operator(((w/CNOT) * (w/h/w))))
