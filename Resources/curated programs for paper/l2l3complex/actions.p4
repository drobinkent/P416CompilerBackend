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

action on_hit() {
}
action on_miss() {
}
action nop() {
}

action action_drop(drop_reason) {
    modify_field(hop_metadata.drop_code, drop_reason);
    drop();
}

action set_bd_index_and_ig_lif(bd_index, ig_lif) {
    modify_field(hop_metadata.bd_index, bd_index);
    modify_field(hop_metadata.ig_lif, ig_lif);
}

action generate_learn_notify() {
    generate_digest(MAC_LEARN_RECEIVER, mac_learn_digest);
}

meter storm_control_meter {
    type : bytes;
    result : hop_metadata.storm_control_color;
    instance_count : IG_BCAST_STORM_SIZE;
}

action set_bcast_storm_meter(meter_idx) {
    execute_meter(storm_control_meter, meter_idx,
                  hop_metadata.storm_control_color);
}

action set_ig_props(vrf_index, urpf, bd_acl_label, lif_acl_label) {
    modify_field(hop_metadata.vrf_index, vrf_index);
    modify_field(hop_metadata.urpf, urpf);
    modify_field(hop_metadata.bd_acl_label, bd_acl_label);
    modify_field(hop_metadata.lif_acl_label, lif_acl_label);
}

action on_ipv4_ucast_hit() {
}

action on_ipv4_xcast_hit() {
}

action on_ipv6_ucast_hit() {
}

action on_ipv6_xcast_hit() {
}

action set_next_hop_ipv4(next_hop_index, ecmp_index) {
    modify_field(hop_metadata.ipv4_next_hop_index, next_hop_index);
    modify_field(hop_metadata.ipv4_ecmp_index, ecmp_index);
    modify_field_with_hash_based_offset(hop_metadata.l3_hash, 0, l3_hash_ipv4, 0);
}

action set_next_hop_ipv6(next_hop_index, ecmp_index) {
    modify_field(hop_metadata.ipv6_next_hop_index, next_hop_index);
    modify_field(hop_metadata.ipv6_ecmp_index, ecmp_index);
    modify_field_with_hash_based_offset(hop_metadata.l3_hash, 0, l3_hash_ipv6, 0);
}

action set_multicast_replication_list(mc_index) {
    modify_field(hop_metadata.mcast_grp, mc_index);
}

action set_urpf_fail() {
    modify_field(hop_metadata.urpf_check_fail, 1);
}

action set_ecmp_next_hop_ipv4(dst_index) {
    modify_field(hop_metadata.ipv4_next_hop_index, dst_index);
}

action set_ecmp_next_hop_ipv6(dst_index) {
    modify_field(hop_metadata.ipv6_next_hop_index, dst_index);
}

action set_ethernet_addr(bd_index, smac, dmac) {
    modify_field(hop_metadata.bd_index, bd_index);
    modify_field(ethernet.srcAddr, smac);
    modify_field(ethernet.dstAddr, dmac);
}

action set_eg_lif(eg_lif) {
    modify_field(hop_metadata.eg_lif, eg_lif);
    modify_field_with_hash_based_offset(hop_metadata.l2_hash, 0, l2_hash_calc, 0);
}

action set_egress_port(e_port) {
    modify_field(standard_metadata.egress_spec, e_port);
}

action set_egress_props(bd_acl_label, lif_acl_label) {
    modify_field(hop_metadata.bd_acl_label, bd_acl_label);
    modify_field(hop_metadata.lif_acl_label, lif_acl_label);
}

action set_vlan(vlan_id) {
    modify_field(vlan_tag_[0].vid, vlan_id);
}
