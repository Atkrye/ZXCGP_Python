#Raw experiment code, written to serve as a basis for parameterized experiment code. Aim is to learn simple CNOT
#Function as a ZX Graph

from ZX_CGP import *

#Define population size
popsize = 5
#Define search width
n = 5
#Define search height
m = 10
#CNOT is 2 inputs
i = 2
#CNOT is 2 outputs
o = 2
#Define phase reset granularity, the degree to which a node's phase can be reset between 0 and 2pi
k = 16
#Mean mutations
uM = 3
#Variance in mutations
vM = 2
#Phase variance; phase is changed on average by 0.5
p = 1.0
#Node arity (in)
a = 3
#Node arity (out)
r = 3
#Max complexity
c = 3
#Edge disconnect rate
d = 0.1
#Phase reset rate

#Max runs
max_runs = 2000
#Number of checks on fitness function
checks = 50
#Target score
target = 0.999

#Initialize population
population = [ZX_CGP(i,n,m,o,a,r,c)for x in range(popsize)]

print("Building population...")
#Randomize over 10000 mutations. Since each mutation has a reverse this is effectively shuffling
for ind in population:
    ind.mutate(10000, p, k, d)

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
cnot = QSystem()
cnot.new_layer()
cnot.add_operator(CMatrix([[1 + 0j, 0j, 0j, 0j],[0j, 1 + 0j, 0j, 0j],[0j,0j,0j,1 + 0j],[0j,0j,1 + 0j, 0j]]))
cnot.close_layer()
cnot.compile()
for check in range(checks):
    # Get 2 random phases
    qubitA = random.random() * math.pi * 2
    qubitB = random.random() * math.pi * 2
    aZ = math.cos(qubitA) + 0j
    aO = math.sin(qubitA) + 0j
    bZ = math.cos(qubitB) + 0j
    bO = math.sin(qubitB) + 0j
    zz = aZ * bZ
    zo = aZ * bO
    oz = aO * bZ
    oo = aO * bO
    # Build superstate of qubits
    input = QState([zz, zo, oz, oo])
    output = cnot.apply(input)
    print("Input :\n" + str(input))
    print("Expects output :\n" + str(output))
    checks_inputs.append(input)
    checks_outputs.append(output)

print("IO Pairings built.")

print("Evaluating IO Parents on ideal solution...")

#Evaluate test set on human solution
cnot_zx = QSystem()
cnot_zx.new_layer()
cnot_zx.add_operator(ZXNode.calculate_general_green(1, 2, 0.0))
cnot_zx.add_operator(ZXNode.calculate_general_green(1, 1, 0.0))
cnot_zx.new_layer()
cnot_zx.add_operator(ZXNode.calculate_general_green(1, 1, 0.0))
cnot_zx.add_operator(ZXNode.calculate_general_red(2, 1, 0.0))
cnot_zx.close_layer()
cnot_zx.compile()
error = 0.0
for check in range(checks):
    input = checks_inputs[check]
    output = checks_outputs[check]
    # Apply the individual to the input
    real_output = cnot_zx.apply(input)
    real_output.normalize()

    # Work out the error
    error += (real_output - output).state_data.size()

# Adjust the error
error = error / float(checks)
print("Human competitive system score: " + str(1.0 / (1.0 + error)))

print("Evaluation complete.")


#evaluation counter
evals = 0

print("Performing evolutionary algorithm...")


#1 + Lambda algorithm
while gen < max_runs and not perfect:
    print("Generation " + str(gen) + ", best score: " + str(best) + ", evaluations: " + str(evals))
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
        #Scores within 0.0001 are allowed for neutral drift
        if best - scores[i] < 0.0001:
            winners.append(i)
            winner_count += 1
    winner = winners[random.randint(0, winner_count - 1)]

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
            population[i].mutate(mutations, p, k, d)
            scores[i] = scores[winner]
        else:
            population[winner].changed = False

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






