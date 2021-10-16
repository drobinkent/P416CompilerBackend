from ortools.linear_solver import pywraplp


def create_data_model():
    """Create the data for the example."""
    data = {}
    # weights = [48, 30, 42, 36, 36, 48, 42, 42, 36, 24, 30, 30, 42, 36, 36]
    weights = []
    #64, 96, and 64 words of 8, 16, and 32b
    for i in range(0,64):
        weights.append(8)
    for i in range(0,96):
        weights.append(16)
    for i in range(0,64):
        weights.append(32)
    # values = [10, 30, 25, 50, 35, 30, 15, 40, 30, 35, 45, 10, 20, 30, 25]
    values = []
    for i in range(0,64):
        values.append(8)
    for i in range(0,96):
        values.append(16)
    for i in range(0,64):
        values.append(32)
    data['weights'] = weights
    data['values'] = values
    data['items'] = list(range(len(weights)))
    data['num_items'] = len(weights)
    # num_bins = 5
    # data['bins'] = list(range(num_bins))
    # data['bin_capacities'] = [100, 100, 100, 100, 100]

    # 16: 13, 32: 14, 8: 10, 48: 4, 128: 4, 24: 1
    bin_capacities = []
    for i in range(0,13):
        bin_capacities.append(16)
    for i in range(0,14):
        bin_capacities.append(32)
    for i in range(0,10):
        bin_capacities.append(8)
    for i in range(0,4):
        bin_capacities.append(48)
    for i in range(0,4):
        bin_capacities.append(128)
    for i in range(0,1):
        bin_capacities.append(24)
    num_bins = len(bin_capacities)
    data['bins'] = list(range(num_bins))
    data['bin_capacities'] = bin_capacities
    return data



def main():
    data = create_data_model()

    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver('SAT_INTEGER_PROGRAMMING')

    # Variables
    # x[i, j] = 1 if item i is packed in bin j.
    x = {}
    for i in data['items']:
        for j in data['bins']:
            x[(i, j)] = solver.IntVar(0, 1, 'x_%i_%i' % (i, j))

    # Constraints
    # Each item can be in at most one bin.
    for i in data['items']:
        solver.Add(sum(x[i, j] for j in data['bins']) <= 1)
    # The amount packed in each bin cannot exceed its capacity.
    for j in data['bins']:
        solver.Add(
            sum(x[(i, j)] * data['weights'][i]
                for i in data['items']) <= data['bin_capacities'][j])

    # Objective
    objective = solver.Objective()

    for i in data['items']:
        for j in data['bins']:
            objective.SetCoefficient(x[(i, j)], data['values'][i])
    objective.SetMaximization()

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print('Total packed value:', objective.Value())
        total_weight = 0
        for j in data['bins']:
            bin_weight = 0
            bin_value = 0
            print('Bin ', j, '\n')
            for i in data['items']:
                if x[i, j].solution_value() > 0:
                    # print('Item', i, '- weight:', data['weights'][i], ' value:',
                    #       data['values'][i])
                    bin_weight += data['weights'][i]
                    bin_value += data['values'][i]
            print('Packed bin weight:', bin_weight)
            print('Packed bin value:', bin_value)
            print()
            total_weight += bin_weight
        print('Total packed weight:', total_weight)
    else:
        print('The problem does not have an optimal solution.')


if __name__ == '__main__':
    main()