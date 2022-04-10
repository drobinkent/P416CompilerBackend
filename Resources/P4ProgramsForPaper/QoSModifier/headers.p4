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

header_type hop_metadata_t {
    fields {
        bd_index: 16;
        ig_lif: 16;
        vrf_index: 12;
        urpf: 2;
        ingress_port:9;
        egress_port:9;
        bd_acl_label: 24;
        lif_acl_label: 24;
        ipv4_next_hop_index: 16;
        ipv4_ecmp_index: 16;
        ipv6_next_hop_index: 16;
        ipv6_ecmp_index: 16;
        ipv6_prefix : 64;
        l3_hash : 16;
        l2_hash : 16;
        mcast_grp : 16;
        urpf_check_fail : 1;
        drop_code : 8;
        eg_lif : 16;
        storm_control_color : 1; /* 0: pass, 1: fail */
        register_tmp : 32;
    }
}
metadata hop_metadata_t hop_metadata;



header_type ethernet_t {
    fields {
        dstAddr : 48;
        srcAddr : 48;
        etherType : 16;
    }
}


header_type ipv4_t {
    fields {
        version : 4;
        ihl : 4;
        diffserv : 8;
        totalLen : 16;
        identification : 16;
        flags : 3;
        fragOffset : 13;
        ttl : 8;
        protocol : 8;
        hdrChecksum : 16;
        srcAddr : 32;
        dstAddr: 32;
    }
}

header_type ipv6_t {
    fields {
        version : 4;
        trafficClass : 8;
        flowLabel : 20;
        payloadLen : 16;
        nextHdr : 8;
        hopLimit : 8;
        srcAddr : 128;
        dstAddr : 128;
    }
}

header_type control_packet_t {
    fields {
        ipv4_diffserv : 8;
        ipv6_trafficClass : 8;
        index: 8;

    }
}






