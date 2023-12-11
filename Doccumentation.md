# The source code starts from the Main.py file. 

This Python code is designed for analyzing and processing a P4 (Programming Protocol-Independent Packet Processors) program and mapping it to a V1Model switch. It involves parsing the P4 program, building a header vector, mapping header fields to hardware, and performing various analyses related to TCAM entry generation, header vector mapping, and TDG (Ternary Directed Graph) mapping on a reconfigurable hardware model.



## Parsing P4 program and hardware description

- `p4ProgramParserFactory`: Instance of `P4ProgramParserFactory` for P4 program parsing. Parsing logic for additional P4 language constructs can be added here. Or new parser can be used also. P4 program is parsed using `P4ProgramParserFactory` to obtain a parsed representation and stored in `p4program`.
- `hw`: Instance of RMT hardware created using `RMTHardwareFactory`. This instance of hardware takes two inputs a) a JSON file describing the hardware resources of a V1Model and b) the additionally, if you want to implement new externs you can also provide that as description in the second JSON file. 
- Hardware configuration files are specified for instruction set and hardware specification.



## Physical Header Vector Construction

- The parsed hardware description is used to build a physical header vector of the RMT hardware using the call `p4program.buildHeaderVector(hw)`.

## P4 Program Graph Creation

- Here, a table dependency graph is generated from the intermediate representation of the P4 program graph (`p4ProgramGraph`). It is created based on the parsed P4 program. The relevant call is `p4ProgramGraph = P4ProgramGraph(p4program)`.

# From here the actual mapping process starts. 

## PHV (Parser Header Vector) Analysis and mapping

- At the beginning we analyze the header lists of the given P4 program to find a mapping of these fields on the RMT hardware's PHV fields. The relevant call is `headerFieldSpecsInP4ProgramToBeUsedForParserMapper, totalRawBitwidth = p4ProgramGraph.headeranalyzer(hw)`.
- Then at last we calculate the Waste in PHV  based on header field specifications and the mapped packet header vector. The relevant call is `Util.calculatePHVWaste(headerFieldSpecsInP4Program, mappedPacketHeaderVector,totalRawBitwidth)`.

## Parser Mapping

- Header fields in the P4 program are analyzed, and a parse graph is loaded. The relevant call is `parseGraphHeaderList, parsedGraphHeaders, initHeader = HeaderLib.loadParseGraph(parserObject = p4program.parsers[0], p4ProgramGraph = p4ProgramGraph)`
-  Then `buildParserMapper` function is called to generate TCAM entries for the parser. The relevant function call is `buildParserMapper(parseGraphHeaderList, parsedGraphHeaders, hw, initHeader)`
- Time taken for this operation is measured and printed.



## TDG or Pipeline Embedding

- Pipelines are embedded into the RMT hardware based on the P4 program graph. The relevant call is `p4ProgramGraph.loadPipelines(hw)`.
- Time taken for this operation is measured and printed.

## Performance Metrics

- Total time for TDG mapping is printed.
- Total nodes and edges in the TDG are printed.
- Total latency of the RMT hardware is calculated and printed.

**Note:** This documentation assumes proper indentation and code structure in the original code.
