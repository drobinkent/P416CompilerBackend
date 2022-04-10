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

table match_control_packet {
    reads {
        control_packet: valid;

    }
    actions {
        set_ipv4_ipv6_qos;
    }
    size :  CONTROL_TABLE_SIZE;
}



table ipv4_nexthop {
    reads {
        ipv4.dstAddr : exact;
    }
    actions {
        set_next_hop_ipv4;
        ipv4_miss;
    }
    size : IPV4_NEXTHOP_SIZE;
}


table ipv6_nexthop {
    reads {
        ipv6.dstAddr : exact;
    }
    actions {
        set_next_hop_ipv6;
    }
    size : IPV6_NEXTHOP_SIZE;
}
