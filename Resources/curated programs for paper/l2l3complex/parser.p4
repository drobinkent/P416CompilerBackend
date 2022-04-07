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

parser start {
    return parse_ethernet;
}

#define ETHERTYPE_BF_FABRIC    0x9000
#define ETHERTYPE_BF_SFLOW     0x9001
#define ETHERTYPE_VLAN         0x8100, 0x9100
#define ETHERTYPE_MPLS         0x8847
#define ETHERTYPE_IPV4         0x0800
#define ETHERTYPE_IPV6         0x86dd
#define ETHERTYPE_ARP          0x0806
#define ETHERTYPE_RARP         0x8035
#define ETHERTYPE_NSH          0x894f
#define ETHERTYPE_ETHERNET     0x6558
#define ETHERTYPE_TRILL        0x22f3
#define ETHERTYPE_VNTAG        0x8926

#define IPV4_MULTICAST_MAC 0x01005E
#define IPV6_MULTICAST_MAC 0x3333

/* Tunnel types */
#define INGRESS_TUNNEL_TYPE_NONE               0
#define INGRESS_TUNNEL_TYPE_VXLAN              1
#define INGRESS_TUNNEL_TYPE_GRE                2
#define INGRESS_TUNNEL_TYPE_GENEVE             3
#define INGRESS_TUNNEL_TYPE_NVGRE              4
#define INGRESS_TUNNEL_TYPE_MPLS_L2VPN         5
#define INGRESS_TUNNEL_TYPE_MPLS_L3VPN         8

#define PARSE_ETHERTYPE                                    \
        ETHERTYPE_VLAN : parse_vlan;                       \
        ETHERTYPE_MPLS : parse_mpls;                       \
        ETHERTYPE_IPV4 : parse_ipv4;                       \
        ETHERTYPE_IPV6 : parse_ipv6;                       \
        ETHERTYPE_ARP : parse_arp_rarp;                    \
        ETHERTYPE_RARP : parse_arp_rarp;                   \
        default: ingress

header ethernet_t ethernet;

parser parse_ethernet {
    extract(ethernet);
    return select(latest.etherType) {
        PARSE_ETHERTYPE;
    }
}

#define VLAN_DEPTH 1
header vlan_tag_t vlan_tag_[VLAN_DEPTH];

parser parse_vlan {
    extract(vlan_tag_[next]);
    return select(latest.etherType) {
        PARSE_ETHERTYPE;
    }
}

#define MPLS_DEPTH 1
header mpls_t mpls[MPLS_DEPTH];

parser parse_mpls {
    extract(mpls[next]);
    return select(latest.bos) {
        0 : parse_mpls;
        default: ingress;
    }
}

#define IP_PROTOCOLS_ICMP              1
#define IP_PROTOCOLS_IGMP              2
#define IP_PROTOCOLS_IPV4              4
#define IP_PROTOCOLS_TCP               6
#define IP_PROTOCOLS_UDP               17
#define IP_PROTOCOLS_IPV6              41
#define IP_PROTOCOLS_GRE               47
#define IP_PROTOCOLS_IPSEC_ESP         50
#define IP_PROTOCOLS_IPSEC_AH          51
#define IP_PROTOCOLS_ICMPV6            58
#define IP_PROTOCOLS_EIGRP             88
#define IP_PROTOCOLS_OSPF              89
#define IP_PROTOCOLS_PIM               103
#define IP_PROTOCOLS_VRRP              112

#define IP_PROTOCOLS_IPHL_ICMP         0x501
#define IP_PROTOCOLS_IPHL_IPV4         0x504
#define IP_PROTOCOLS_IPHL_TCP          0x506
#define IP_PROTOCOLS_IPHL_UDP          0x511
#define IP_PROTOCOLS_IPHL_IPV6         0x529
#define IP_PROTOCOLS_IPHL_GRE          0x52f

header ipv4_t ipv4;

field_list ipv4_checksum_list {
        ipv4.version;
        ipv4.ihl;
        ipv4.diffserv;
        ipv4.totalLen;
        ipv4.identification;
        ipv4.flags;
        ipv4.fragOffset;
        ipv4.ttl;
        ipv4.protocol;
        ipv4.srcAddr;
        ipv4.dstAddr;
}

field_list_calculation ipv4_checksum {
    input {
        ipv4_checksum_list;
    }
    algorithm : csum16;
    output_width : 16;
}

calculated_field ipv4.hdrChecksum  {
    verify ipv4_checksum if (ipv4.ihl == 5);
    update ipv4_checksum if (ipv4.ihl == 5);
}

parser parse_ipv4 {
    extract(ipv4);
    return select(latest.fragOffset, latest.ihl, latest.protocol) {
        IP_PROTOCOLS_IPHL_ICMP : parse_icmp;
        IP_PROTOCOLS_IPHL_TCP : parse_tcp;
        IP_PROTOCOLS_IPHL_UDP : parse_udp;
        IP_PROTOCOLS_IPHL_GRE : parse_gre;
        default: ingress;
    }
}

header ipv6_t ipv6;

parser parse_ipv6 {
    extract(ipv6);
    return select(latest.nextHdr) {
        IP_PROTOCOLS_ICMPV6 : parse_icmp;
        IP_PROTOCOLS_TCP : parse_tcp;
        IP_PROTOCOLS_UDP : parse_udp;
        IP_PROTOCOLS_GRE : parse_gre;
        default: ingress;
    }
}

header icmp_t icmp;

parser parse_icmp {
    extract(icmp);
    return ingress;
}

#define TCP_PORT_BGP                   179
#define TCP_PORT_MSDP                  639

header tcp_t tcp;
parser parse_tcp {
    extract(tcp);
    return ingress;
}

header udp_t udp;

parser parse_udp {
    extract(udp);
    return ingress;
}

#define GRE_PROTOCOLS_NVGRE            0x20006558
#define GRE_PROTOCOLS_ERSPAN_T3        0x22EB   /* Type III version 2 */

header gre_t gre;

parser parse_gre {
    extract(gre);
    return ingress;
}

#define ARP_PROTOTYPES_ARP_RARP_IPV4 0x0800

header arp_rarp_t arp_rarp;

parser parse_arp_rarp {
    extract(arp_rarp);
    return ingress;
}
