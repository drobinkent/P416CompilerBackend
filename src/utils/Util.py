

def calculatePHVWaste(headerFieldSpecsInP4Program, mappedPacketHeaderVector,totalRawBitwidth):
    totalBitsRequiredForRawHeaderFields = 0
    for hSpec in headerFieldSpecsInP4Program.keys():
        bWidth = hSpec
        count = headerFieldSpecsInP4Program.get(bWidth)
        totalBitsRequiredForRawHeaderFields = totalBitsRequiredForRawHeaderFields + bWidth * count

    totalBitsRequiredInPhv = 0
    phvToCountMap = {}
    for bWidth in mappedPacketHeaderVector.keys():
        phvList = mappedPacketHeaderVector.get(bWidth)
        for phv in phvList:
            totalBitsRequiredInPhv = totalBitsRequiredInPhv + phv
            if phvToCountMap.get(phv) == None:
                phvToCountMap[phv] = 1
            else:
                phvToCountMap[phv] = phvToCountMap.get(phv) + 1

    print("Total Bitwidth of the raw header fields is: "+str(totalRawBitwidth)+" bits")
    print("Total Bitwidth required for accomodating the header fields using the smallest size PHV field is: "+str(totalBitsRequiredForRawHeaderFields)+" bits")
    print("Used PHV field wise cunt is "+str(phvToCountMap))
    print("Total Bitwidth required for accomodating the header fields using the PHV fields is: "+str(totalBitsRequiredInPhv)+" bits")
    waste = 0
    if (totalBitsRequiredInPhv <= totalRawBitwidth):
        waste = 0
    else:
        waste = totalBitsRequiredInPhv - totalRawBitwidth
    print('Total waste is : '+str(waste))
    print("Waste percentage is %.2f\%", ((waste/totalBitsRequiredInPhv)*100))
    return