#include <core.p4>
#define V1MODEL_VERSION 20200408
#include <v1model.p4>

struct hop_metadata_t {
    bit<16> bd_index;
    bit<16> ig_lif;
    bit<12> vrf_index;
    bit<2>  urpf;
    bit<9>  ingress_port;
    bit<9>  egress_port;
    bit<24> bd_acl_label;
    bit<24> lif_acl_label;
    bit<16> ipv4_next_hop_index;
    bit<16> ipv4_ecmp_index;
    bit<16> ipv6_next_hop_index;
    bit<16> ipv6_ecmp_index;
    bit<64> ipv6_prefix;
    bit<16> l3_hash;
    bit<16> l2_hash;
    bit<16> mcast_grp;
    bit<1>  urpf_check_fail;
    bit<8>  drop_code;
    bit<16> eg_lif;
    bit<1>  storm_control_color;
    bit<32> register_tmp;
}

header control_packet_t {
    bit<8> ipv4_diffserv;
    bit<8> ipv6_trafficClass;
    bit<8> index;
}

header ethernet_t {
    bit<48> dstAddr;
    bit<48> srcAddr;
    bit<16> etherType;
}

header ipv4_t {
    bit<4>  version;
    bit<4>  ihl;
    bit<8>  diffserv;
    bit<16> totalLen;
    bit<16> identification;
    bit<3>  flags;
    bit<13> fragOffset;
    bit<8>  ttl;
    bit<8>  protocol;
    bit<16> hdrChecksum;
    bit<32> srcAddr;
    bit<32> dstAddr;
}

header ipv6_t {
    bit<4>   version;
    bit<8>   trafficClass;
    bit<20>  flowLabel;
    bit<16>  payloadLen;
    bit<8>   nextHdr;
    bit<8>   hopLimit;
    bit<128> srcAddr;
    bit<128> dstAddr;
}

struct metadata {
    @name(".hop_metadata") 
    hop_metadata_t hop_metadata;
}

struct headers {
    @name(".control_packet") 
    control_packet_t control_packet;
    @name(".ethernet") 
    ethernet_t       ethernet;
    @name(".ipv4") 
    ipv4_t           ipv4;
    @name(".ipv6") 
    ipv6_t           ipv6;
}

parser ParserImpl(packet_in packet, out headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    @name(".parse_control") state parse_control {
        packet.extract(hdr.control_packet);
        transition accept;
    }
    @name(".parse_ethernet") state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            16w0x800: parse_ipv4;
            16w0x86dd: parse_ipv6;
            16w0x806: parse_control;
            default: accept;
        }
    }
    @name(".parse_ipv4") state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition accept;
    }
    @name(".parse_ipv6") state parse_ipv6 {
        packet.extract(hdr.ipv6);
        transition accept;
    }
    @name(".start") state start {
        transition parse_ethernet;
    }
}

control egress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    apply {
    }
}

@name(".ipv4_port_qos") register<bit<8>, bit<7>>(32w128) ipv4_port_qos;

@name(".ipv6_port_qos") register<bit<8>, bit<7>>(32w128) ipv6_port_qos;

control process_control_packet(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    @name(".set_ipv4_ipv6_qos") action set_ipv4_ipv6_qos() {
        ipv4_port_qos.write((bit<7>)(bit<7>)hdr.control_packet.index, (bit<8>)hdr.control_packet.ipv4_diffserv);
        ipv6_port_qos.write((bit<7>)(bit<7>)hdr.control_packet.index, (bit<8>)hdr.control_packet.ipv6_trafficClass);
    }
    @name(".match_control_packet") table match_control_packet {
        actions = {
            set_ipv4_ipv6_qos;
        }
        key = {
            hdr.control_packet.isValid(): exact;
        }
        size = 256;
    }
    apply {
        match_control_packet.apply();
    }
}

control ingress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    @name(".set_next_hop_ipv4") action set_next_hop_ipv4(bit<9> port) {
        meta.hop_metadata.egress_port = port;
        ipv4_port_qos.read(hdr.ipv4.diffserv, (bit<7>)(bit<7>)port);
        hdr.ipv6.dstAddr = hdr.ipv6.srcAddr;
    }
    @name(".ipv4_miss") action ipv4_miss() {
        hdr.ipv6.dstAddr = 128w9898989;
    }
    @name(".set_next_hop_ipv6") action set_next_hop_ipv6(bit<9> port) {
        meta.hop_metadata.egress_port = port;
        ipv6_port_qos.read(hdr.ipv6.trafficClass, (bit<7>)(bit<7>)port);
    }
    @name(".ipv4_nexthop") table ipv4_nexthop {
        actions = {
            set_next_hop_ipv4;
            ipv4_miss;
        }
        key = {
            hdr.ipv4.dstAddr: exact;
        }
        size = 1600;
    }
    @name(".ipv6_nexthop") table ipv6_nexthop {
        actions = {
            set_next_hop_ipv6;
        }
        key = {
            hdr.ipv6.dstAddr: exact;
        }
        size = 1600;
    }
    @name(".process_control_packet") process_control_packet() process_control_packet_0;
    apply {
        if (hdr.control_packet.isValid()) {
            process_control_packet_0.apply(hdr, meta, standard_metadata);
        } else {
            switch (ipv4_nexthop.apply().action_run) {
                ipv4_miss: {
                    ipv6_nexthop.apply();
                }
            }
        }
    }
}

control DeparserImpl(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.control_packet);
        packet.emit(hdr.ipv6);
        packet.emit(hdr.ipv4);
    }
}

control verifyChecksum(inout headers hdr, inout metadata meta) {
    apply {
        verify_checksum(hdr.ipv4.ihl == 4w5, { hdr.ipv4.version, hdr.ipv4.ihl, hdr.ipv4.diffserv, hdr.ipv4.totalLen, hdr.ipv4.identification, hdr.ipv4.flags, hdr.ipv4.fragOffset, hdr.ipv4.ttl, hdr.ipv4.protocol, hdr.ipv4.srcAddr, hdr.ipv4.dstAddr }, hdr.ipv4.hdrChecksum, HashAlgorithm.csum16);
    }
}

control computeChecksum(inout headers hdr, inout metadata meta) {
    apply {
        update_checksum(hdr.ipv4.ihl == 4w5, { hdr.ipv4.version, hdr.ipv4.ihl, hdr.ipv4.diffserv, hdr.ipv4.totalLen, hdr.ipv4.identification, hdr.ipv4.flags, hdr.ipv4.fragOffset, hdr.ipv4.ttl, hdr.ipv4.protocol, hdr.ipv4.srcAddr, hdr.ipv4.dstAddr }, hdr.ipv4.hdrChecksum, HashAlgorithm.csum16);
    }
}

V1Switch(ParserImpl(), verifyChecksum(), ingress(), egress(), computeChecksum(), DeparserImpl()) main;

