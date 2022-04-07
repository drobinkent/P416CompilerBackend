#define ROUTABLE_CHECK_MULTICAST_SIZE 64
#define ROUTABLE_CHECK_ROUTABLE_SIZE 64
#define UNICAST_ROUTING_SIZE 32000
#define MULTICAST_ROUTING_SIZE 24000
#define MAC_LEARNING_SIZE 68000
#define IGMP_SIZE 24000
#define SWITCHING_SIZE 68000
#define ACL_SIZE 1600

table routable_check_multicast {
    reads {
     ethernet.srcAddr: exact;
     ethernet.dstAddr: exact;
     vlan_tag_[0].vid: exact;
    }
    actions {
     multicast_action;
     nop;
    }
    size : ROUTABLE_CHECK_MULTICAST_SIZE;
}

action multicast_action() {
    modify_field(ingress_metadata.is_multicast, 1);
}

table routable_check_routable {
    reads {
     ethernet.srcAddr: exact;
     ethernet.dstAddr: exact;
     vlan_tag_[0].vid: exact;
    }
    actions {
     routable_action;
    }
    size : ROUTABLE_CHECK_ROUTABLE_SIZE;
}

action routable_action() {
    modify_field(ingress_metadata.is_routable, 1);
}



table unicast_routing {
    reads {
     ipv4.dstAddr : ternary;
    }
    actions { 
    set_next_hop;
    }
    size : UNICAST_ROUTING_SIZE;
}

action set_next_hop(smac, dmac, vlan_id) {
    modify_field(ethernet.srcAddr, smac);
    modify_field(ethernet.dstAddr, dmac);
    modify_field(vlan_tag_[0].vid, vlan_id);
}

table multicast_routing {
    reads {
    ipv4.dstAddr : ternary;
    }
    
    actions {
        set_mcast_idx;
    }
    size : MULTICAST_ROUTING_SIZE;
}

action set_mcast_idx(idx) {
    modify_field(ingress_metadata.mc_idx, idx);
}

table mac_learning {
    reads { 
    	ethernet.srcAddr : exact;
	vlan_tag_[0].vid: exact;	
    }
    actions {
      nop;
    }
    size : MAC_LEARNING_SIZE;
}

action nop() {
}
table igmp {
    reads {
        ipv4.dstAddr: ternary;
	    vlan_tag_[0].vid: exact;
        standard_metadata.ingress_port : exact;
    }
    actions {
      set_mcast_idx;
    }
    size : IGMP_SIZE;
}

table switching {
    reads {
     ethernet.dstAddr : exact;
     vlan_tag_[0].vid: exact;	
    }
    actions {
     set_egress;
    }
    size : SWITCHING_SIZE;
}

action set_egress(port) {
    modify_field(standard_metadata.egress_spec, port);
}


table acl {
    reads {
     ethernet.srcAddr : ternary;
     ethernet.dstAddr : ternary;
     vlan_tag_[0].vid: exact;
     standard_metadata.ingress_port : exact;
     ingress_metadata.is_routable : ternary;
     ingress_metadata.is_multicast : ternary;
     ipv4.dstAddr : ternary;
     standard_metadata.egress_spec : ternary;
    }
    actions {
     set_drop_code;
    }
    size : ACL_SIZE;
}

action set_drop_code(code) {
    modify_field(ingress_metadata.drop_code, code);
}
