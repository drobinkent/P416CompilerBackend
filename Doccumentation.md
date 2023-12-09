# The source code starts from the Main.py file. 

This Python code is designed for analyzing and processing a P4 (Programming Protocol-Independent Packet Processors) program and mapping it to a V1Model switch. It involves parsing the P4 program, building a header vector, mapping header fields to hardware, and performing various analyses related to TCAM entry generation, header vector mapping, and TDG (Ternary Directed Graph) mapping on a reconfigurable hardware model.



## Configuration

- `p4ProgramParserFactory`: Instance of `P4ProgramParserFactory` for P4 program parsing. Parsing logic for additional P4 language constructs can be added here. Or new parser can be used also. 
- `hw`: Instance of RMT hardware created using `RMTHardwareFactory`. This instance of hardware takes two inputs a) a JSON file describing the hardware resources of a V1Model and b) the additionally, if you want to implement new externs you can also provide that as description in the second JSON file. 
- Hardware configuration files are specified for instruction set and hardware specification.

## P4 Program Parsing

- P4 program is parsed using `P4ProgramParserFactory` to obtain a parsed representation (`p4program`).
- P4 program file, version, and architecture are specified.

## Header Vector Construction

- The parsed P4 program is used to build a header vector for the RMT hardware.

## P4 Program Graph Creation

- A P4 program graph (`p4ProgramGraph`) is created based on the parsed P4 program.

## Parser Mapping

- Header fields in the P4 program are analyzed, and a parse graph is loaded.
- `buildParserMapper` function is called to generate TCAM entries for the parser.
- Time taken for this operation is measured and printed.

## Header Field Mapping

- Pipelines are loaded into the RMT hardware based on the P4 program graph.
- Header field specs in the P4 program are analyzed.
- Time taken for mapping header fields to the hardware is measured and printed.

## PHV (Parser Header Vector) Analysis

- Waste in PHV is calculated based on header field specifications and the mapped packet header vector.

## Pipeline Embedding

- Pipelines are embedded into the RMT hardware based on the P4 program graph.
- Time taken for this operation is measured and printed.

## Performance Metrics

- Total time for TDG mapping is printed.
- Total nodes and edges in the TDG are printed.
- Total latency of the RMT hardware is calculated and printed.

**Note:** This documentation assumes proper indentation and code structure in the original code.
