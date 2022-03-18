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

#define ROUTABLE_SIZE 64
#define SMAC_VLAN_SIZE 160000
#define VRF_SIZE 40000
#define CHECK_IPV6_SIZE 1
#define IPv6_PREFIX_SIZE 1000
#define CHECK_UCAST_IPV4_SIZE 1
#define IPV4_FORWARDING_SIZE 160000
#define IPV6_FORWARDING_SIZE 5000
#define NEXT_HOP_SIZE 41250
#define IPV4_XCAST_FORWARDING_SIZE 16000
#define IPV6_XCAST_FORWARDING_SIZE 1000
#define URPF_V4_SIZE 160000
#define URPF_V6_SIZE 5000
#define IGMP_SNOOPING_SIZE 16000
#define DMAC_VLAN_SIZE 160000
#define ACL_SIZE 80000

#define VRF_BIT_WIDTH 12

header_type hop_metadata_t {

        bit<VRF_BIT_WIDTH> vrf ;
        bit<64> ipv6_prefix ;
        bit<16> next_hop_index;
        bit<16> mcast_grp ;
        bit<1> urpf_fail ;
        bit<8> drop_reason;

}

metadata hop_metadata_t hop_metadata;

header_type ethernet_t {
        bit<48>  dstAddr;
        bit<48> srcAddr;
        bit<16> etherType;
}

header_type vlan_tag_t {
        bit<3>  pcp : 3;
        bit<> cfi : 1;
        bit<> vid : 12;
        bit<> etherType : 16;
}

header_type mpls_t {
        bit<> label : 20;
        bit<> exp : 3;
        bit<> bos : 1;
        bit<> ttl : 8;
}

header_type ipv4_t {
        bit<> version : 4;
        bit<> ihl : 4;
        bit<> diffserv : 8;
        bit<> totalLen : 16;
        bit<> identification : 16;
        bit<> flags : 3;
        bit<> fragOffset : 13;
        bit<> ttl : 8;
        bit<> protocol : 8;
        bit<> hdrChecksum : 16;
        bit<> srcAddr : 32;
        bit<> dstAddr: 32;
}

header_type ipv6_t {
        bit<> version : 4;
        bit<> trafficClass : 8;
        bit<> flowLabel : 20;
        bit<> payloadLen : 16;
        bit<> nextHdr : 8;
        bit<> hopLimit : 8;
        bit<> srcAddr : 128;
        bit<> dstAddr : 128;
}

header_type icmp_t {
        bit<> type_ : 8;
        bit<> code : 8;
        bit<> hdrChecksum : 16;

}

header_type tcp_t {
        bit<> srcPort : 16;
        bit<> dstPort : 16;
        bit<> seqNo : 32;
        bit<> ackNo : 32;
        bit<> dataOffset : 4;
        bit<> res : 3;
        bit<> ecn : 3;
        bit<> ctrl : 6;
        bit<> window : 16;
        bit<> checksum : 16;
        bit<> urgentPtr : 16;
}

header_type udp_t {
        bit<> srcPort : 16;
        bit<> dstPort : 16;
        bit<> length_ : 16;
        bit<> checksum : 16;
}

header_type gre_t {
        bit<> C : 1;
        bit<> R : 1;
        bit<> K : 1;
        bit<> S : 1;
        bit<> s : 1;
        bit<> recurse : 3;
        bit<> flags : 5;
        bit<> ver : 3;
        bit<> proto : 16;
}

header_type arp_rarp_t {
        bit<> hwType : 16;
        bit<> protoType : 16;
        bit<> hwAddrLen : 8;
        bit<> protoAddrLen : 8;
        bit<> opcode : 16;
}