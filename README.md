# P416CompilerBackend

# Language features not supported yet 

  ## In Parser

    -- header stack, union 
    -- variable length header 
    
  ## In Match-action stages 
  
    -- Indirect Counter and meter (direct meter and counters are supported. Indirect counter and meters are not supported yet. However, indirect meter and counters can be replaced in P4 code using SRAM based stateful memory). 
    -- Custom externs are not supported. However they can be supported easily. I will add how to support them as soon as possible. 
    


# How to run this compiler backend

See the next section for installing the software that P416Compiler
depends upon.

  ## You need to provide the hardware resources at first. Example hardware resources are given in following folder 
  
    -- P416CompilerBackend/Resources/HardwareConfigs/
    For details of this JSON format you can look at my paper. 
    
 ## Compiler your P4 program using P4C compiler (of course for P4 16 version) 
 
 ## Save the intermediate representation in a json file. 
 
 ## Now get the path for the hardwar resource and the intermediate representation JSON file. 
 
 ## Go to following python file 
 
 -- P416CompilerBackend/src/main.py
 
 In line 15 of the code provide the path for these two JSON file. Then simply run the main.py file. 
 you will get the mapping if the compiler backend can map the P4 program. Otherwise it will show you not possible. 
 
 # NOTE: Besides  this there are few P4 16 language features are well supported yet. In most of the cases the compiler backend will give you descriptive message. If you need to support new language features or new externs, look at the code. I will try to make a detailed documentation on this as soon as possible. 
 
# If you are interested in extending the compiler backend kindly let me know, I will try to help you as far as I can. 
  
  
  
# Install steps

On a supported Linux distribution and version, which currently includes:

+ Ubuntu 20.04, 22.04
+ Fedora 36, 37, 38

run this script to install software that P416Compiler depends upon:

```bash
cd P416CompilerBackend
./src/install.sh
```
