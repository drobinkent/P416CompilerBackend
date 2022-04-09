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









/*
 * Table 7: Ipv4_Ucast_Host
 */
table ipv4_ucast_host {
    reads {
        hop_metadata.vrf_index : exact;
        ipv4.dstAddr : exact;
    }
    actions {
        set_next_hop_ipv4;
        on_miss;
    }
    size : IPV4_UCAST_HOST_SIZE;
}

/*
 * Table 8: Ipv4_Ucast_LPM
 */
table ipv4_ucast_lpm {
    reads {
        hop_metadata.vrf_index : exact;
        ipv4.dstAddr : lpm;
    }
    actions {
        set_next_hop_ipv4;
        on_miss;
    }
    size : IPV4_UCAST_LPM_SIZE;
}

/*
 * Table 9: Ipv4_Mcast
 */
table ipv4_mcast {
    reads {
        hop_metadata.vrf_index : exact;
        hop_metadata.bd_index : exact;
        ipv4.srcAddr : lpm;
        ipv4.dstAddr : exact;
    }
    actions {
        set_multicast_replication_list;
    }
    size : IPV4_MCAST_SIZE;
}

/*
 * Table 10: Ipv4_Urpf
 */
table ipv4_urpf {
    reads {
        hop_metadata.bd_index : exact;
        ipv4.srcAddr : exact;
        hop_metadata.urpf : exact;
    }
    actions {
        set_urpf_fail;
        nop;
    }
    size : IPV4_URPF_SIZE;
}

/*
 * Table 11: Ipv6_Ucast_Host
 */
table ipv6_ucast_host {
    reads {
        hop_metadata.vrf_index : exact;
        ipv6.dstAddr : exact;
    }
    actions {
        set_next_hop_ipv6;
        on_miss;
    }
    size : IPV6_UCAST_HOST_SIZE;
}

/*
 * Table 12: Ipv6_Ucast_LPM
 */
table ipv6_ucast_lpm {
    reads {
        hop_metadata.vrf_index : exact;
        ipv6.dstAddr : lpm;
    }
    actions {
        set_next_hop_ipv6;
        on_miss;
    }
    size : IPV6_UCAST_LPM_SIZE;
}

/*
 * Table 13: Ipv6_Mcast
 */
table ipv6_mcast {
    reads {
        hop_metadata.vrf_index : exact;
        hop_metadata.bd_index : exact;
        ipv6.srcAddr : lpm;
        ipv6.dstAddr : exact;
    }
    actions {
        set_multicast_replication_list;
    }
    size : IPV6_MCAST_SIZE;
}

/*
 * Table 14: Ipv6_Urpf
 */
table ipv6_urpf {
    reads {
        hop_metadata.bd_index : exact;
        ipv6.srcAddr : exact;
        hop_metadata.urpf : exact;
    }
    actions {
        set_urpf_fail;
        nop;
    }
    size : IPV6_URPF_SIZE;
}

/*
 * Table 15: Ipv4_Ecmp
 */
table ipv4_ecmp {
    reads {
        hop_metadata.ipv6_ecmp_index : exact;
        hop_metadata.l3_hash : exact;
    }
    actions {
        set_ecmp_next_hop_ipv4;
        on_miss;
    }
    size : IPV4_ECMP_SIZE;
}

/*
 * Table 16: Ipv4_Nexthop
 */
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

/*
 * Table 17: Ipv6_Ecmp
 */
table ipv6_ecmp {
    reads {
        hop_metadata.ipv4_ecmp_index : exact;
        hop_metadata.l3_hash : exact;
    }
    actions {
        set_ecmp_next_hop_ipv6;
        on_miss;
    }
    size : IPV6_ECMP_SIZE;
}

/*
 * Table 18: Ipv6_Nexthop
 */
table ipv6_nexthop {
    reads {
        ipv6.dstAddr : exact;
    }
    actions {
        set_next_hop_ipv6;
    }
    size : IPV6_NEXTHOP_SIZE;
}

/*
 * Table 19: IG_Dmac
 */
table ig_dmac {
    reads {
        hop_metadata.bd_index : exact;
        ethernet.dstAddr : exact;
    }
    actions {
        set_eg_lif;
    }
    size : IG_DMAC_SIZE;
}

/*
 * Table 20: IG_Agg_Intf
 */
table ig_agg_intf {
    reads {
        hop_metadata.eg_lif : exact;
        hop_metadata.l2_hash : exact;
    }
    actions {
        set_egress_port;
    }
    size : IG_AGG_INTF_SIZE;
}

/*
 * Table 21: IG_ACL2
 */
table ig_acl2 {
    reads {
        hop_metadata.ipv4_next_hop_index : ternary;
        hop_metadata.ipv6_next_hop_index : ternary;
    }
    actions {
        action_drop;
        nop;
    }
    size : IG_ACL2_SIZE;
}

/*
 * Table 22: EG_Props
 */
table eg_props {
    reads {
        hop_metadata.bd_index : exact;
        hop_metadata.eg_lif : exact;
    }
    actions {
        set_egress_props;
    }
    size : EG_PROPS_SIZE;
}

/*
 * Table 23: EG_Phy_Meta
 */
table eg_phy_meta {
    reads {
        standard_metadata.egress_spec : exact;
        hop_metadata.bd_index : exact;
    }
    actions {
        set_vlan;
        action_drop;
    }
    size : EG_PHY_META_SIZE;
}

/*
 * Table 24: EG_ACL1
 */
table eg_acl1 {
    reads {
        hop_metadata.bd_index : ternary;
        hop_metadata.bd_acl_label : ternary;
        hop_metadata.lif_acl_label : ternary;
    }
    actions {
        action_drop;
    }
    size : EG_ACL1_SIZE;
}
