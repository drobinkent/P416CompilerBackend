/*
Copyright (c) 2015-2016 by The Board of Trustees of the Leland
Stanford Junior University.  All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


 Author: Lisa Yan (yanlisa@stanford.edu)
*/

#include "defines.p4"
#include "parser.p4"
#include "headers.p4"
#include "actions.p4"
#include "tables.p4"


control process_control_packet {
   apply(match_control_packet);
}






control ingress {
    /* Ingress properties, learning */

    if(valid(control_packet)){
        process_control_packet();
    }
    else {
        //l3_checks_ipv4();
        apply(ipv4_nexthop){
            hit {
                apply(ipv6_nexthop);
            }
        }
    }




}

control egress {
}
