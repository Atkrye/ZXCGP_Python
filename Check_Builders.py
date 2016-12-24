from QuantumSystem import *
from CMatrix import *
import random

#Super class declaring key method
class Check_Builder:
    #Initialize method
    def initialize(self, checks):
        return None

    #Evaluation method
    def get_error(self, qsystem):
        return 0.0

    #Static method to generate qubit as a CMatrix (so that it can be tensored, unlike a QState)
    @staticmethod
    def gen_qubit():
        #Random rotation between 0 and 2pi
        qubit = random.random() * math.pi * 2
        #Ignore imaginary axis. sin^2 + cos^2 = 1, so this produces a valid quantum state
        z = math.cos(qubit) + 0j
        o = math.sin(qubit) + 0j
        return CMatrix([[z, o]])
        
#Check builder for an IO Problem
class IO_Check(Check_Builder):
    #Pass ideal QSystem to generate IO pairs
    def __init__(self, isystem):
        self.isystem = isystem
        self.in_checks = []
        self.out_checks = []
        self.checks = 0

    #Build IO Pairs for a given number of checks
    def initialize(self, checks):
        self.checks = checks
        self.in_checks = []
        self.out_checks = []
        for i in range(checks):
            IO_pair = self.initialize_io_pair()
            self.in_checks += [IO_pair[0]]
            self.out_checks += [IO_pair[1]]
        
    #Generate a IO pair
    def initialize_io_pair(self):
        #work out in qubits
        in_m = CMatrix([[1.0 + 0j]])
        qubits = int(round(math.log(len(self.isystem.compiled_system.get_layer(0).get_raw_data()[0]), 2)))
        for i in range(qubits):
            in_m = in_m / Check_Builder.gen_qubit()
            
        in_state = QState(in_m.get_raw_data()[0])

        #Calculate output
        out_state = self.isystem.apply(in_state)
        return [in_state, out_state]

    #Evaluate by calculating total error across checks and averaging
    def get_error(self, qsystem):
       #initialize error counter
       error = 0.0

       #Evaluate on each check
       for check in range(self.checks):
            #Get check IOPair 
            inp = self.in_checks[check]
            out = self.out_checks[check]

            #Evaluate system on check
            real = qsystem.apply(inp)

            #ZXGraphs may be trace reducing, so we normalize them to have a square sum of 1
            real.normalize()

            #Increment error if it is 'significant', > 0.000000001
            real_error = (real - out).state_data.size()
            if real_error > 0.000000001:
                error += real_error
       return error / float(self.checks)

#Check builder specific for Teleportation Problem
class TP_Check(Check_Builder):
    #Init code
    def __init__(self):
        self.in_checks = []
        self.checks = 0

    #Build IO Pairs for a given number of checks
    def initialize(self, checks):
        self.checks = checks
        self.in_checks = []
        #Simply generate single qubits as input
        for i in range(checks):
            self.in_checks += [Check_Builder.gen_qubit()]
    
    #Evaluate by calculating total error across checks and averaging
    def get_error(self, qsystem):
       #initialize error counter
       error = 0.0

       #Initialize zero qubit
       z = CMatrix([[1 + 0j, 0j]])
       o = CMatrix([[0j, 1 + 0j]])
       #Initialize one qubit

       #Evaluate on each check
       for check in range(self.checks):
            #Get check input
            inp = self.in_checks[check]

            #Build input with 2 extra qubits in zero state
            input_state = QState((inp / z / z).get_raw_data()[0])
            
            #Evaluate system on check to generate *PRE-MEASUREMENT STATE*
            inter = input_state.apply_operator(qsystem.compiled_system.get_layer(0))
            inter.normalize()
            
            #Initialize arbitrarily large
            first = None
            second = None
            #Calculate expected error
            expected_error = 0.0
            #Try each pairing of the first 2 qubits (e.g. the control bits that are measured and passed)
            pairings = []
            for one1 in [False, True]:
                for one2 in [False, True]:
                    copy = inter.copy()
                    res = None
                    if one1:
                        res = inter.measure_qubit_to_value(0, False)
                    else:
                        res = inter.measure_qubit_to_value(0, True)
                    inter2 = res[0]
                    res2 = None
                    if one2:
                        res2 = inter2.measure_qubit_to_value(1, False)
                    else:
                        res2 = inter2.measure_qubit_to_value(1, True)
                    p = res[1] * res2[1]
                    real = res2[0]
                    real = real.apply_operator(qsystem.compiled_system.get_layer(2))
                    real.normalize()
                    
                    #Find best case error
                    min_error = 10000.0
                    for one3 in [False, True]:
                        for one4 in [False, True]:
                            if one3:
                                first = o
                            else:
                                first = z
                            if one4:
                                second = o
                            else:
                                second = z
                            output_state = QState((first / second / inp).get_raw_data()[0])
                            potential_error = (real - output_state).state_data.size()
                            if potential_error < min_error:
                                min_error = potential_error
                    pairings.append([min_error, p])
            totalp = 0.0
            for pair in pairings:
                totalp += pair[1]
                expected_error += (pair[1] * pair[0])
            if totalp <= 0.0001:
                expected_error = 1.0
            #Ignore insignificant error e.g. caused by python math
            if expected_error > 0.000000001:
                error += expected_error
       return error / float(self.checks)


    #Evaluate by calculating total error across checks and averaging
    def get_error_debug(self, qsystem):
       #initialize error counter
       error = 0.0

       #Initialize zero qubit
       z = CMatrix([[1 + 0j, 0j]])
       o = CMatrix([[0j, 1 + 0j]])
       #Initialize one qubit

       #Evaluate on each check
       for check in range(self.checks):
            #Get check input
            inp = self.in_checks[check]

            #Build input with 2 extra qubits in zero state
            input_state = QState((inp / z / z).get_raw_data()[0])
            print("Input state: \n" + str(input_state))
            #Evaluate system on check to generate *PRE-MEASUREMENT STATE*
            inter = input_state.apply_operator(qsystem.compiled_system.get_layer(0))
            inter.normalize()
            print("Has pre-measurement state: \n" + str(inter))
            #Increment error if it is 'significant', > 0.000000001.
            #Initialize arbitrarily large
            first = None
            second = None
            #Calculate expected error
            expected_error = 0.0
            #Try each pairing of the first 2 qubits (e.g. the control bits that are measured and passed)
            pairings = []
            for one1 in [False, True]:
                for one2 in [False, True]:
                    copy = inter.copy()
                    res = None
                    if one1:
                        res = inter.measure_qubit_to_value(0, False)
                    else:
                        res = inter.measure_qubit_to_value(0, True)
                    inter2 = res[0]
                    res2 = None
                    if one2:
                        res2 = inter2.measure_qubit_to_value(1, False)
                    else:
                        res2 = inter2.measure_qubit_to_value(1, True)
                    p = res[1] * res2[1]
                    real = res2[0]
                    real = real.apply_operator(qsystem.compiled_system.get_layer(2))
                    real.normalize()

                    print("Possible result from " + str(one1) + "," + str(one2) + ", p = " + str(p) + ":\n" + str(real))

                    #Find best case error
                    min_error = 10000.0
                    for one3 in [False, True]:
                        for one4 in [False, True]:
                            if one3:
                                first = o
                            else:
                                first = z
                            if one4:
                                second = o
                            else:
                                second = z
                            output_state = QState((first / second / inp).get_raw_data()[0])
                            print("Error matrix: \n" + str(real - output_state))
                            potential_error = (real - output_state).state_data.size()
                            print("Error: " + str(potential_error))
                            if potential_error < min_error:
                                min_error = potential_error
                    print("Min error: " + str(min_error))
                    print("With probability: " + str(p))
                    pairings.append([min_error, p])
            totalp = 0.0
            for pair in pairings:
                print(pair)
                totalp += pair[1]
                expected_error += (pair[1] * pair[0])
            print("Total probability: " + str(totalp))
            if totalp <= 0.0001:
                expected_error = 1.0
            print("Expected error: " + str(expected_error))
            #Ignore insignificant error e.g. caused by python math
            if expected_error > 0.000000001:
                error += expected_error
       return error / float(self.checks)
