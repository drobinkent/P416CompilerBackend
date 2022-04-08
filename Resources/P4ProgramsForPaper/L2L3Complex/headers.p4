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
    }
}
metadata hop_metadata_t hop_metadata;

field_list l3_hash_fields_ipv4 {
    ipv4.srcAddr;
    ipv4.dstAddr;
    ipv4.protocol;
    tcp.srcPort;
    tcp.dstPort;
    udp.srcPort;
    udp.dstPort;
}

field_list_calculation l3_hash_ipv4 {
    input {
        l3_hash_fields_ipv4;
    }
    algorithm : crc16;
    output_width : ECMP_BIT_WIDTH;
}

field_list l3_hash_fields_ipv6 {
    ipv6.srcAddr;
    ipv6.dstAddr;
    ipv6.nextHdr;
    tcp.srcPort;
    tcp.dstPort;
    udp.srcPort;
    udp.dstPort;
}

field_list_calculation l3_hash_ipv6 {
    input {
        l3_hash_fields_ipv6;
    }
    algorithm : crc16;
    output_width : ECMP_BIT_WIDTH;
}

field_list l2_hash_fields {
    ethernet.srcAddr;
    ethernet.dstAddr;
    ethernet.etherType;
}

field_list_calculation l2_hash_calc {
    input {
        l2_hash_fields;
    }
    algorithm : crc16;
    output_width : ECMP_BIT_WIDTH;
}

field_list mac_learn_digest {
    hop_metadata.bd_index;
    ethernet.srcAddr;
    hop_metadata.ig_lif;
}
 
header_type ethernet_t {
    fields {
        dstAddr : 48;
        srcAddr : 48;
        etherType : 16;
    }
}

header_type vlan_tag_t {
    fields {
        pcp : 3;
        cfi : 1;
        vid : 12;
        etherType : 16;
    }
}

header_type mpls_t {
    fields {
        label : 20;
        exp : 3;
        bos : 1;
        ttl : 8;
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

header_type icmp_t {
    fields {
        type_ : 8;
        code : 8;
        hdrChecksum : 16;
    }
}

header_type tcp_t {
    fields {
        srcPort : 16;
        dstPort : 16;
        seqNo : 32;
        ackNo : 32;
        dataOffset : 4;
        res : 3;
        ecn : 3;
        ctrl : 6;
        window : 16;
        checksum : 16;
        urgentPtr : 16;
    }
}

header_type udp_t {
    fields {
        srcPort : 16;
        dstPort : 16;
        length_ : 16;
        checksum : 16;
    }
}

header_type gre_t {
    fields {
        C : 1;
        R : 1;
        K : 1;
        S : 1;
        s : 1;
        recurse : 3;
        flags : 5;
        ver : 3;
        proto : 16;
    }
}

header_type arp_rarp_t {
    fields {
        hwType : 16;
        protoType : 16;
        hwAddrLen : 8;
        protoAddrLen : 8;
        opcode : 16;
    }
}
