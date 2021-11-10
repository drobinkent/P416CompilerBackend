from ortools.linear_solver import pywraplp



class RMTV1ModelHardware:


    def __init__(self, headerFieldSpecs): # headerFieldSpecs map will contain "header field width" : "count" data .
        self.pakcetHeaderVectorFieldSizeVsCountMap= headerFieldSpecs

    def getPakcetHeaderVectorFieldSizeVsCountMap(self, p4ProgramHeaderFieldSpecs):
        return self.pakcetHeaderVectorFieldSizeVsCountMap

    def createDataModelForHeadreMapping(self, p4ProgramHeaderFieldSpecs): # Here we are doing a reverse multile knapsack. we want to pack the
        data = {}
        weights = []
        values = []
        for k in self.pakcetHeaderVectorFieldSizeVsCountMap:
            headerWidth = k
            count = self.pakcetHeaderVectorFieldSizeVsCountMap.get(k)
            for i in range(0,count):
                weights.append(headerWidth)
                values.append(headerWidth)
        data['weights'] = weights
        data['values'] = values
        data['items'] = list(range(len(weights)))
        data['num_items'] = len(weights)

        bin_capacities = []  # these are filled with the programs header fields specs
        for k in p4ProgramHeaderFieldSpecs:
            headerWidth = k
            count = p4ProgramHeaderFieldSpecs.get(k)
            for i in range(0,count):
                bin_capacities.append(headerWidth)
        num_bins = len(bin_capacities)
        data['bins'] = list(range(num_bins))
        data['bin_capacities'] = bin_capacities
        print("Data model is "+str(data))
        return data

    def mapHeaderFields(self, p4ProgramHeaderFieldSpecs):
        data = self.createDataModelForHeadreMapping(p4ProgramHeaderFieldSpecs)
        # Create the mip solver with the SCIP backend.
        solver = pywraplp.Solver.CreateSolver('BOP_INTEGER_PROGRAMMING')
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
        totalHeaderWidthRequiredByP4Program = 0
        for k in p4ProgramHeaderFieldSpecs:
            headerWidth = k
            count = p4ProgramHeaderFieldSpecs.get(k)
            totalHeaderWidthRequiredByP4Program = totalHeaderWidthRequiredByP4Program + headerWidth*count

        mappedacketHeaderVector = {}
        if status == pywraplp.Solver.OPTIMAL:
            print('Total packed value:', objective.Value())
            total_weight = 0
            for j in data['bins']:
                bin_weight = 0
                bin_value = 0
                # print('Bin ', j, '\n')
                binFiller = {}
                for i in data['items']:
                    if x[i, j].solution_value() > 0:
                        # print('Item', i, '- weight:', data['weights'][i], ' value:',
                        #       data['values'][i])
                        bin_weight += data['weights'][i]
                        bin_value += data['values'][i]

                        if mappedacketHeaderVector.get(data['bin_capacities'][j]) == None:
                            mappedacketHeaderVector[data['bin_capacities'][j]] = [data['weights'][i]]
                        else:
                            mappedacketHeaderVector.get(data['bin_capacities'][j]).append(data['weights'][i])
                            # mappedacketHeaderVector[data['bin_capacities'][j]]  =
                # print('Packed bin weight:', bin_weight)
                # print('Packed bin value:', bin_value)
                # print()

                total_weight += bin_weight
            print('Total packed weight:', total_weight)
            if(total_weight != totalHeaderWidthRequiredByP4Program):
                print("The optimized header mapping find process is able to map only: "+str(total_weight)+" bits in the packet header vector of the hardware. whereas the program requires "+str(totalHeaderWidthRequiredByP4Program)+" bits. Hence it is failed. ")
                print("Stopping further execution and exiting")
                exit(1)
            else:
                print("The program's header fields can be mapped to the RMT hardware using following mappine")
                print("For each X-bit wide header field this output lists all the hardwared header fields used. So assume in a P4 program you need 2 32 bit field. If it shows 8 x8 bit wide header fields. that means to fill"
                      "the 2x 32 bit header fields of the program we can use 8x8 bit wide header fields available in the hardware")
                print(str(mappedacketHeaderVector))
        else:
            print('The problem does not have an optimal solution.')
            pass
