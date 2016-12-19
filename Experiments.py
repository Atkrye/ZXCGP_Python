class Experiment:

    @staticmethod
    def run_1_plus_lambda(popsize, init_pop_mutations, individual_builder, phase_reset_granularity, mean_mutations, variance_mutations, variance_phase, node_arity_in, node_arity_out, max_complexity, mutation_weights, max_runs, checks, check_builder, target_score):
        #Start with gen counter at zero
        gen = 0

        #Score counters are in a double array
        scores = [0.0 for i in range(popsize)]

        #Initialize and randomize population
        population = [individual_builder.initialize_individual() for x in range(popsize)]

        for ind in population:
            for sbgraph in ind:
                sbgraph.mutate_with_weights(init_pop_mutations, variance_phase, phase_reset_granularity, mutation_weights)

        #Initialize check arrays
        checks_inputs = []
        checks_outputs = []

        #Generate an IO pair for each intended check
        for check in range(checks):
            IO_pair = check_builder.initialize_io_pair()
            checks_inputs += [IO_Pair[0]]
            checks_outputs += [IO_Pair[1]]

        #Evaluation counter
        evals = 0

        #Flag for a perfect solution
        perfect = False

        #Begin evolutionary algorithm
        while gen < max_runs and not perfect:
            gen += 1
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

                if changed:
                    #Use builder to generate quantum system equivalent (QSystem from QuantumSystem.py)
                    q = individual_builder.build_qsystem(ind)

                    #Increment evaluation counter
                    evals += 1

                    #initialize error counter
                    error = 0.0

                    #Evaluate on each check
                    for check in range(checks):
                        #Get check IOPair 
                        inp = checks_inputs[check]
                        out = checks_outputs[check]

                        #Evaluate system on check
                        real = q.apply(inp)

                        #ZXGraphs may be trace reducing, so we normalize them to have a square sum of 1
                        real.normalize()

                        #Increment error if it is 'significant', > 0.000000001
                        real_error = (real - out).state_data.size()
                        if real_error > 0.000000001:
                            error += real_error

                    #Update score with mean of error, and penalize for inactive inputs
                    scores[i] = 1.0 / (1.0 + ind.counter_inactive_inputs() + (error / float(checks)))
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
                if scores[i] = best:
                    winners.append(i)
                    winner_counter += 1

            #Give preference to neutral drift when the winner survives a generation
            old_winner = winner
            while old_winner == winner and len(winners) > 1:
                winner = winners[random.randint(0, winner_count - 1)]
            if len(winners) == 1:
                winner = winners[0]

            #Repopulation
            for i in range(popsize):
                if i != winner:
                    #Completely copy the winner
                    for part in range(len(population[i])):
                        population[i][part] = population[winner][part].copy()

