from Individual_Builders import *
from Check_Builders import *
class Experiment:

    @staticmethod
    def run_1_plus_lambda(popsize, init_pop_mutations, individual_builder, phase_reset_granularity, mean_mutations, variance_mutations, variance_phase, mutation_weights, max_runs, checks, check_builder, target_score):
        #Start with gen counter at zero
        gen = 0

        #Score counters are in a double array
        scores = [0.0 for i in range(popsize)]

        #Initialize and randomize population
        population = [individual_builder.initialize_individual() for x in range(popsize)]

        for ind in population:
            for sbgraph in ind:
                sbgraph.mutate_with_weights(init_pop_mutations, variance_phase, phase_reset_granularity, mutation_weights)

        #Initialize check builder with given number of checks
        check_builder.initialize(checks)

        #Evaluation counter
        evals = 0

        #Flag for a perfect solution
        perfect = False

        #Variable for tracking winner
        winner = -1

        #Variable for tracking best score in each generation
        best = 0.0

        #Begin evolutionary algorithm
        while gen < max_runs and not perfect:
            print("Generation " + str(gen) + ": " + str(best))
            gen += 1
            best = 0.0

            #Evaluation each individual
            for i in range(popsize):
                #Get each individual
                ind = population[i]

                #Check whether any part of the individual has changed
                changed = True

                if changed:
                    #Use builder to generate quantum system equivalent (QSystem from QuantumSystem.py)
                    q = individual_builder.build_qsystem(ind)

                    #Increment evaluation counter
                    evals += 1

                    #calculate error
                    error = check_builder.get_error(q)

                    inactive = 0.0
                    #Count inactive inputs
                    for part in range(len(ind)):
                        inactive += float(ind[part].count_inactive_inputs())

                    #Update score with mean of error, and penalize for inactive inputs
                    scores[i] = 1.0 / (1.0 + inactive + error)
                    if scores[i] > target:
                        perfect = True

                #Catch generations with no positive improvement (neutral mutations win)
                if scores[i] > best:
                    best = scores[i]
                    
            #Choose the winner
            winners = []
            winner_count = 0
            for i in range(popsize):
                #Catch winners. Winners may be equivalent in neutral drift
                if best - scores[i] < 0.001:
                    winners.append(i)
                    winner_count += 1

            #Give preference to neutral drift when the winner survives a generation
            old_winner = winner
            while old_winner == winner and len(winners) > 1:
                winner = winners[random.randint(0, winner_count - 1)]
            if len(winners) == 1:
                winner = winners[0]
            
            #Winner starts unchanged
            for part in range(len(population[i])):
                    population[winner][part].changed = False

            #Repopulation
            if not perfect:
                for i in range(popsize):
                    if i != winner:
                        #Completely copy the winner by copying and mutating each part
                        for part in range(len(population[i])):
                            #Perform actual copy operation
                            population[i][part] = population[winner][part].copy()
                            
                            #Mutate the copied part a precalculated number of times

                            #Round gaussian to get number of mutations
                            mutations = int(round(gauss(uM, vM)))

                            #Ensure mutations is positive
                            if mutations < 0:
                                mutations

                            #Catch no mutations, these are useless
                            elif mutations == 0:
                                mutations = 1

                            population[i][part].mutate_with_weights(mutations, variance_phase, phase_reset_granularity, mutation_weights)
        #Return is [final_result, score, generations, evaluations]
        print("Final winner index... " + str(winner))
        return [population[winner], scores[winner], gen, evals]
#Popsize
popsize = 5
#Initial randomization
init_rand = 1000
#Individual Builder
in_builder = Simple_Circuit_Builder(3, 3, 7, 7, 2, 4, 4)
tp_builder = TP_Builder(4, 4, 4, 4, 5, 5, 2, 4, 1)
#Phase reset granularity
k = 4
#Mean mutations
uM = 5
#Variance mutations
vM = 5
#Variance in phase
vP = 1.0
#Mutation distribution is [edge_change, edge_disconnect, function_change, phase_change, phase_reset]
mutation_weights = [2.5, 0.5, 3.0, 2.0, 1.0]
#Max runs
max_runs = 50000
#Number of checks
checks = 5
#Check builder
CNOT = CMatrix([[1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 1 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 0 + 0j, 0 + 0j, 1 + 0j],[0 + 0j, 0 + 0j, 1 + 0j, 0 + 0j]])
qft2 = QSystem.generate_qft(2)
qft3 = QSystem.generate_qft(3)
q = QSystem()
q.new_layer()
q.add_operator(qft3)
q.close_layer()
q.compile()
ch_builder = IO_Check(q)
tp_check = TP_Check()
#Target score
target = 0.999

#result = Experiment.run_1_plus_lambda(popsize, init_rand, in_builder, k, uM, vM, vP, mutation_weights, max_runs, checks, ch_builder, target)

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

tp_check.initialize(10)
print(tp_check.get_error_debug(qs))

result = Experiment.run_1_plus_lambda(popsize, init_rand, tp_builder, k, uM, vM, vP, mutation_weights, max_runs, checks, tp_check, target)

print(str(result[0][0]))
print(str(result[0][1]))
print(str(result[0][2]))
print(str(result[0][0].generate_qsystem().compiled_system.get_layer(0)))
print(str(result[0][1].generate_qsystem().compiled_system.get_layer(0)))
print(str(result[0][2].generate_qsystem().compiled_system.get_layer(0)))
print(result[1])
print(result[2])
print(result[3])

print(tp_check.get_error_debug(tp_builder.build_qsystem(result[0])))
    
