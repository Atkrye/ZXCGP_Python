from Individual_Builders import *
from Check_Builders import *
class Experiment:

    @staticmethod
    def run_1_plus_lambda(popsize, check_reset, init_pop_mutations, individual_builder, phase_reset_granularity, mean_mutations, variance_mutations, variance_phase, mutation_weights, max_runs, checks, check_builder, target_score):
        #Start with gen counter at zero
        gen = 0
        ui_count = 0
        ui_reset = 100
        check_count = 1

        #Score counters are in a double array
        scores = [0.0 for i in range(popsize)]

        #Initialize and randomize population
        population = [individual_builder.initialize_individual() for x in range(popsize)]

        for ind in population:
            for sbgraph in range(len(ind)):
                for i in range(init_pop_mutations):
                    sbgraph_copy = ind[sbgraph].copy()
                    sbgraph_copy.mutate_with_weights(1, variance_phase, phase_reset_granularity, mutation_weights)
                    while not sbgraph_copy.check_complexity():
                        sbgraph_copy = ind[sbgraph].copy()
                        sbgraph_copy.mutate_with_weights(1, variance_phase, phase_reset_granularity, mutation_weights)
                    ind[sbgraph] = sbgraph_copy
                    
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

        neutral = 0
        same_winner = 0
        unchanged = 0

        mutation_counters = [0 for x in range(6)]

        #Begin evolutionary algorithm
        while gen < max_runs and not perfect:
            gen += 1
            ui_count += 1
            check_count += 1
            if ui_count >= ui_reset:
                ui_count = 0
                print("Generation " + str(gen) + ": " + str(best))
                print(str(neutral) + " neutral genetic drifts")
                print(str(unchanged) + " unchanged individuals")
                print(str(same_winner) + " stagnant generations")
                print("Mutation distribution: " + str(mutation_counters))
                unchanged = 0
                neutral = 0
                same_winner = 0
                mutation_counters = [0 for x in range(6)]
            if check_count >= check_reset:
                check_count = 1
                check_builder.initialize(checks)
                #Re-evaluate all
                for ind in population:
                    for part in ind:
                        part.changed = True
            best = 0.0

            #Evaluation each individual
            for i in range(popsize):
                #Get each individual
                ind = population[i]

                #Check whether any part of the individual has changed
                changed = False
                for part in ind:
                    if part.changed:
                        changed = True
                if not changed:
                    unchanged += 1
                    scores[i] = scores[winner]
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
                if best - scores[i] < 0.0001:
                    winners.append(i)
                    winner_count += 1


            old_winner = winner
            #Give preference to neutral drift when the winner survives a generation
            if len(winners) == 1:
                winner = winners[0]
            else:
                if old_winner in winners:
                    neutral += 1
                while old_winner == winner and len(winners) > 1:
                    winner = winners[random.randint(0, winner_count - 1)]
            if old_winner == winner:
                same_winner += 1
            
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
                            population[i][part].changed = False

                            #Mutate the copied part a precalculated number of times

                            #Round gaussian to get number of mutations
                            mutations = int(round(gauss(uM, vM)))

                            #Ensure mutations is positive
                            if mutations <= 0:
                                mutations = 1
                                
                            counters = population[i][part].mutate_with_weights(mutations, variance_phase, phase_reset_granularity, mutation_weights)

                            #Keep retrying until run valid complexity
                            while not population[i][part].check_complexity():
                                population[i][part] = population[winner][part].copy()
                                population[i][part].changed = False
                                counters = population[i][part].mutate_with_weights(mutations, variance_phase, phase_reset_granularity, mutation_weights)
                                
                            for j in range(6):
                                mutation_counters[j] += counters[j]
                    else:
                        for part in population[i]:
                            part.changed = False
        #Return is [final_result, score, generations, evaluations]
        print("Final winner index... " + str(winner))
        return [population[winner], scores[winner], gen, evals]
#Popsize
popsize = 10
#Initial randomization
init_rand = 500
#Individual Builder
in_builder = Simple_Circuit_Builder(3, 3, 7, 7, 2, 4, 4)
tp_builder = TP_Builder(4, 4, 4, 4, 5, 5, 2, 4, 1)
layered_builder = Layered_Builder(2, 2, 2, 3, 3, 2, 4, 3)
#Phase reset granularity
k = 4
#Mean mutations
uM = 5
#Variance mutations
vM = 5
#Variance in phase
vP = 0.5
#Mutation distribution is [edge_change, edge_disconnect, function_change, phase_change, phase_reset, control flip rate]
mutation_weights = [1,0.2,1,1,1,1]
#Max runs
max_runs = 2000000
#Number of checks
checks = 10
#Check reset rate
check_reset = 150000
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
target = 0.99
#result = Experiment.run_1_plus_lambda(popsize, check_reset, init_rand, in_builder, k, uM, vM, vP, mutation_weights, max_runs, checks, ch_builder, target)
#print(result[0][0])
#print(result[1])
##
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
#print(tp_check.get_error_debug(qs))

result = Experiment.run_1_plus_lambda(popsize, check_reset, init_rand, tp_builder, k, uM, vM, vP, mutation_weights, max_runs, checks, tp_check, target)

print(str(result[0][0]))
print(str(result[0][1]))
print(str(result[0][2]))
print(str(result[0][0].generate_qsystem().compiled_system.get_layer(0)))
print(str(result[0][1].generate_qsystem().compiled_system.get_layer(0)))
print(str(result[0][2].generate_qsystem().compiled_system.get_layer(0)))
print(result[1])
print(result[2])
print(result[3])

    
tp_check.initialize(3)
print(tp_check.get_error_debug(tp_builder.build_qsystem(result[0])))



