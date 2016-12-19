#Raw experiment code, written to serve as a basis for parameterized experiment code. Aim is to learn simple 3 bit Quantum Fourier Transform
#Function as a ZX Graph

from ZX_CGP import *

#Define population size
popsize = 5
#Define search width
n = 8
#Define search height
m = 8
#CNOT is 2 inputs
i = 3
#CNOT is 2 outputs
o = 3
#Define phase reset granularity, the degree to which a node's phase can be reset between 0 and 2pi
k = 16
#Mean mutations
uM = 20
#Variance in mutations
vM = 20
#Phase variance; phase is changed on average by 0.5
p = 0.5
#Node arity (in)
a = 2
#Node arity (out)
r = 4
#Max complexity
c = 4
#Edge disconnect rate
d = 0.1
#Phase reset rate
pr = 0.3
#UI update rate (number of generations between updates
ui_rate = 1000

#Max runs
max_runs = 200000
#Number of checks on fitness function
checks = 50
#Target score
target = 0.999

#Initialize population
population = [ZX_CGP(i,n,m,o,a,r,c)for x in range(popsize)]

print("Building population...")
#Randomize over 10000 mutations. Since each mutation has a reverse this is effectively shuffling
for ind in population:
    ind.mutate(1000, p, k, d, pr)

print("Population built.")

#Gen counter
gen = 0
#Score counter
scores = [0.0 for i in range(popsize)]
#Perfect gate
perfect = False
#Winning index
winner = -1
best = 0.0

print("Building IO pairings...")

#Generate IO pairs
checks_inputs = []
checks_outputs = []
bp = QSystem()
bp.new_layer()
bp.add_operator(QSystem.generate_qft(3))
bp.close_layer()
bp.compile()
for check in range(checks):
    # Get 2 random phases
    qubitA = random.random() * math.pi * 2
    qubitB = random.random() * math.pi * 2
    qubitC = random.random() * math.pi * 2
    aZ = math.cos(qubitA) + 0j
    aO = math.sin(qubitA) + 0j
    bZ = math.cos(qubitB) + 0j
    bO = math.sin(qubitB) + 0j
    cZ = math.cos(qubitC) + 0j
    cO = math.sin(qubitC) + 0j
    zzz = aZ * bZ * cZ
    zzo = aZ * bZ * cO
    zoz = aZ * bO * cZ
    zoo = aZ * bO * cO
    ozz = aO * bZ * cZ
    ozo = aO * bZ * cO
    ooz = aO * bO * cZ
    ooo = aO * bO * cO
    # Build superstate of qubits
    input = QState([zzz, zzo, zoz, zoo, ozz, ozo, ooz, ooo])
    output = bp.apply(input)
    checks_inputs.append(input)
    checks_outputs.append(output)

print("IO Pairings built.")

print("Evaluating IO Parents on ideal solution...")

#Evaluate test set on human solution
bp_zx = QSystem()
bp_zx.new_layer()
bp.add_operator(QSystem.generate_qft(3))
#TODO Implement 3-bit ZX Graph as human solution
##bp_zx.add_operator(ZXNode.generate_hadamard_matrix())
##bp_zx.add_operator(ZXNode.calculate_general_green(1,1,0.0))
##bp_zx.close_layer()
##bp_zx.new_layer()
##bp_zx.add_operator((ZXNode.generate_controlled(1,ZXNode.calculate_general_green(1,1,0.5 * math.pi))))
##bp_zx.close_layer()
##bp_zx.add_operator(ZXNode.calculate_general_green(1,1,0.0))
##bp_zx.add_operator(ZXNode.generate_hadamard_matrix())
bp_zx.close_layer()
bp_zx.compile()
error = 0.0
for check in range(checks):
    input = checks_inputs[check]
    output = checks_outputs[check]
    # Apply the individual to the input
    real_output = bp.apply(input)
    real_output.normalize()
    print("Input: \n" + str(input))
    print("Expects output: \n" + str(output))
    print("Generated: " + str(real_output))
    print("Error: " + str((real_output - output).state_data.size()))

    # Work out the error
    error += (real_output - output).state_data.size()

# Adjust the error
error = error / float(checks)
print("Human competitive system score: " + str(1.0 / (1.0 + error)))

print("Evaluation complete.")


#evaluation counter
evals = 0

#ui update couner
ui_counter = 0

print("Performing evolutionary algorithm...")


#1 + Lambda algorithm
while gen < max_runs and not perfect:
    ui_counter += 1
    if ui_counter >= ui_rate:
        ui_counter = 0
        print("Generation " + str(gen + 1) + ", best score: " + str(best) + ", evaluations: " + str(evals))
    #Increment gen counter
    gen += 1
    best = 0.0

    #Evaluation
    for i in range(popsize):
        ind = population[i]

        #Check if mutations have changed this individual
        if ind.changed:
            evals += 1
            #Evaluate the individual
            error = 0.0
            #Build system
            q = ind.generate_qsystem()

            for check in range(checks):
                input = checks_inputs[check]
                output = checks_outputs[check]
                #Apply the individual to the input
                real_output = q.apply(input)
                real_output.normalize()

                #Work out the error
                error += (real_output - output).state_data.size()

            #Adjust the error
            error = error / float(checks)
            scores[i] = 1.0 / (1.0 + ind.count_inactive_inputs() +  error)

            #Check if newly evaluated score is perfect
            if scores[i] > target:
                perfect = True

        if scores[i] > best:
            best = scores[i]

    #Work out the winner
    winners = []
    winner_count = 0
    for i in range(popsize):
        #Scores within 0.001 are allowed for neutral drift
        if ((best - scores[i] < 0.002) and not perfect) or scores[i] > target:
            winners.append(i)
            winner_count += 1

    #Give preference to neutral drift
    old_winner = winner
    while old_winner == winner and len(winners) > 1:
        winner = winners[random.randint(0, winner_count - 1)]
        #Might have a large jump meaning old winner is lost
    if len(winners) == 1:
        winner = winners[0]
    if best > target:
        perfect = True

    #Repopulation
    for i in range(popsize):
        if i != winner:
            population[i] = population[winner].copy()

            #Round gaussian to get number of mutations
            mutations = int(round(gauss(uM, vM)))

            #Ensure mutations is positive
            if mutations < 0:
                mutations

            #Catch no mutations, these are useless
            elif mutations == 0:
                mutations = 1

            #Perform mutations
            population[i].mutate(mutations, p, k, d, pr)
            scores[i] = scores[winner]
        else:
            population[i].changed = False


print("Finished")
print("Executed in " + str(gen) + " executions")
print("Perfect score found? " + str(perfect))
print("Winning individual, score " + str(scores[winner]) + " : ")
print(population[winner])
print(population[winner].generate_qsystem().compiled_system.get_layer(0))
error = 0.0
q = population[winner].generate_qsystem().compiled_system
for check in range(checks):
    input = checks_inputs[check]
    output = checks_outputs[check]
    # Apply the individual to the input
    real_output = q.apply(input)
    real_output.normalize()

    # Work out the error
    error += (real_output - output).state_data.size()

# Adjust the error
error = error / float(checks)
print("Final score: " + str(1.0 / (1.0 + error)))






