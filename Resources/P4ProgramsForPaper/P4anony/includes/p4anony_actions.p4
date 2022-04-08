/************ ACTIONS ************/

/* Set output port */
action set_egr_action(egress_spec) {
    //modify_field(ig_intr_md_for_tm.ucast_egress_port, egress_spec);
    modify_field(standard_metadata.egress_spec, egress_spec);
}

action nop_action() {
}

action _drop_action() {
    drop();
}

action multicast_mac_catch_action() {
    bit_and(localm.dst_mac_mc_oui,ethernet.dstAddr_oui,0x110000);
}

/***************************************************************
 * Prepare hashing by dividing subnet part and hash part
 * by masking.  SRC IP.
 * 
 * mask1:    subnet mask (e.g., 255.255.255.0)
 * mask2:    wildcard part mask (e.g., 0.0.0.255)
 */
action prepare_srcip_hash_action(mask1,mask2) {
    bit_and(localm.srcip_subnet_part,localm.ipv4_srcip,mask1);
    bit_and(localm.srcip_hash_part,localm.ipv4_srcip,mask2);

    modify_field(localm.srcip_subnetmask, mask1);
}

/***************************************************************
 * Prepare hashing by dividing subnet part and hash part
 * by masking. DST IP. 
 * 
 * mask1:    subnet mask (e.g., 255.255.255.0)
 * mask2:    wildcard part mask (e.g., 0.0.0.255)
 */
action prepare_dstip_hash_action(mask1,mask2) {
    bit_and(localm.dstip_subnet_part,localm.ipv4_dstip,mask1);
    bit_and(localm.dstip_hash_part,localm.ipv4_dstip,mask2);

    modify_field(localm.dstip_subnetmask, mask1);
}

action hash_mac_src_id_action() {
    hash(ethernet.srcAddr_id, HashAlgorithm.crc32, 0, {localm.src_mac_id}, 16777216);
    //modify_field_with_hash_based_offset(ethernet.srcAddr_id, 0, mac_src_calc_id, 16777216);
    modify_field(localm.hashed_mac_srcAddr_id, 1);
}

action hash_mac_src_oui_action() {
    hash(ethernet.srcAddr_oui, HashAlgorithm.crc32, 0, {localm.src_mac_oui}, 16777216);
    //modify_field_with_hash_based_offset(ethernet.srcAddr_oui, 0, mac_src_calc_oui, 16777216);
    modify_field(localm.hashed_mac_srcAddr_oui, 1);
}

action hash_arp_mac_src_id_action() {
    modify_field(arp_ipv4.srcHwAddr_id,ethernet.srcAddr_id);
}

action hash_arp_mac_src_oui_action() {
    modify_field(arp_ipv4.srcHwAddr_oui,ethernet.srcAddr_oui);
}

action hash_mac_dst_id_action() {
    hash(ethernet.dstAddr_id, HashAlgorithm.crc32, 0, {localm.dst_mac_id}, 16777216);
    //modify_field_with_hash_based_offset(ethernet.dstAddr_id, 0, mac_dst_calc_id, 16777216);
    modify_field(localm.hashed_mac_dstAddr_id, 1);
}

action hash_mac_dst_oui_action() {
    hash(ethernet.dstAddr_oui, HashAlgorithm.crc32, 0, {localm.dst_mac_oui}, 16777216);
    //modify_field_with_hash_based_offset(ethernet.dstAddr_oui, 0, mac_dst_calc_oui, 16777216);
    modify_field(localm.hashed_mac_dstAddr_oui, 1);
}

action hash_arp_mac_dst_id_action() {
    modify_field(arp_ipv4.dstHwAddr_id,ethernet.dstAddr_id);
}

action hash_arp_mac_dst_oui_action() {
    modify_field(arp_ipv4.dstHwAddr_oui,ethernet.dstAddr_oui);
}

action hash_and_modify_src0_action() { 
    hash(localm.srcip_hash_part, HashAlgorithm.crc32, 0, {localm.srcip_hash_part}, 4294967296);
    //modify_field_with_hash_based_offset(localm.srcip_hash_part,0,ipv4_src_part_calc0,4294967296);
}
action hash_and_modify_src8_action() { 
    hash(localm.srcip_hash_part, HashAlgorithm.crc32_custom, 0, {localm.srcip_hash_part}, 16777216);
    //modify_field_with_hash_based_offset(localm.srcip_hash_part,0,ipv4_src_part_calc8,4294967296);
}
action hash_and_modify_src16_action() { 
    hash(localm.srcip_hash_part, HashAlgorithm.crc16, 0, {localm.srcip_hash_part}, 65536);
    //modify_field_with_hash_based_offset(localm.srcip_hash_part,0,ipv4_src_part_calc16,4294967296);
}
action hash_and_modify_src24_action() { 
    hash(localm.srcip_hash_part, HashAlgorithm.crc16_custom, 0, {localm.srcip_hash_part}, 256);
    //modify_field_with_hash_based_offset(localm.srcip_hash_part,0,ipv4_src_part_calc24,4294967296);
}
action hash_and_modify_dst0_action() { 
    hash(localm.dstip_hash_part, HashAlgorithm.crc32, 0, {localm.dstip_hash_part}, 4294967296);
    //modify_field_with_hash_based_offset(localm.dstip_hash_part,0,ipv4_dst_part_calc0,4294967296);
}
action hash_and_modify_dst8_action() { 
    hash(localm.dstip_hash_part, HashAlgorithm.crc32_custom, 0, {localm.dstip_hash_part}, 16777216);
    //modify_field_with_hash_based_offset(localm.dstip_hash_part,0,ipv4_dst_part_calc8,4294967296);
}
action hash_and_modify_dst16_action() { 
    hash(localm.dstip_hash_part, HashAlgorithm.crc16, 0, {localm.dstip_hash_part}, 65536);
    //modify_field_with_hash_based_offset(localm.dstip_hash_part,0,ipv4_dst_part_calc16,4294967296);
}
action hash_and_modify_dst24_action() { 
    hash(localm.dstip_hash_part, HashAlgorithm.crc16_custom, 0, {localm.dstip_hash_part}, 256);
    //modify_field_with_hash_based_offset(localm.dstip_hash_part,0,ipv4_dst_part_calc24,4294967296);
}

action ip_overwrite_action() { 
    bit_or(ipv4.srcAddr,localm.srcip_subnet_part,localm.srcip_hash_part);
    bit_or(ipv4.dstAddr,localm.dstip_subnet_part,localm.dstip_hash_part);
}

action arp_ip_overwrite_action() { 
    bit_or(arp_ipv4.srcProtoAddr,localm.srcip_subnet_part,localm.srcip_hash_part);
    bit_or(arp_ipv4.dstProtoAddr,localm.dstip_subnet_part,localm.dstip_hash_part);
}
