/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;

}

header my_header {

bit<8>    nsf_22;


}

struct local_metadata_t {
    /* empty */
    bit<8>    nsf_1;
        bit<8>    nsf_2;
        bit<8>    nsf_3;
        bit<8>    nsf_4;
        bit<8>    nsf_5;
        bit<8>    nsf_6;
        bit<8>    nsf_7;
        bit<8>    nsf_8;
        bit<8>    nsf_9;
        bit<8>    nsf_10;
        bit<8>    nsf_11;
}

struct headers {
    ethernet_t   ethernet;
    my_header       my_hdr;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout local_metadata_t meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.my_hdr);
        transition accept;
    }

}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout local_metadata_t meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout local_metadata_t meta,
                  inout standard_metadata_t standard_metadata) {
   /*----------------Stateful memory declaration -------------------*------------------*/
      register<bit<16>>(1024) sf_1;
      register<bit<16>>(1024) sf_2;
      register<bit<16>>(1024) sf_3;
   action set_nsf_1(bit<8> action_param) {
       meta.nsf_1 = action_param;
   }

   table mat_nsf1 {
       key = {
           meta.nsf_1: lpm;
       }
       actions = {
           set_nsf_1;
       }
       size = 1024;
   }
    action set_nsf_2(bit<8> action_param) {
      meta.nsf_2 = action_param;
    }

    table mat_nsf2 {
      key = {
          meta.nsf_2: lpm;
      }
      actions = {
          set_nsf_2;
      }
      size = 1024;
    }
    action set_nsf_3(bit<8> action_param) {
       meta.nsf_3 = action_param;
    }

    table mat_nsf3 {
       key = {
           meta.nsf_3: lpm;
       }
       actions = {
           set_nsf_3;
       }
       size = 1024;
    }
    action set_nsf_4(bit<8> action_param) {
       meta.nsf_3= action_param;
    }

    table mat_nsf4 {
       key = {
           meta.nsf_4: lpm;
       }
       actions = {
           set_nsf_4;
       }
       size = 1024;
    }
    action set_nsf_5(bit<8> action_param) {
       meta.nsf_1 = action_param;
    }

    table mat_nsf5 {
       key = {
           meta.nsf_5: lpm;
       }
       actions = {
           set_nsf_5;
       }
       size = 1024;
    }

    action set_sf_123(bit<8> action_param) {
       sf_1.write((bit<32>)(1), (bit<16>) action_param);
       sf_2.write((bit<32>)(1), (bit<16>) action_param);
       sf_3.write((bit<32>)(1), (bit<16>) action_param);
    }

    table mat_sf123 {
       key = {
           meta.nsf_1: lpm;
       }
       actions = {
           set_sf_123;
       }
       size = 1024;
    }

    action set_sf_12(bit<8> action_param) {
       sf_1.write((bit<32>)(1), (bit<16>) action_param);
       sf_2.write((bit<32>)(1), (bit<16>) action_param);
    }

    table mat_sf12 {
       key = {
           meta.nsf_6: lpm;
       }
       actions = {
           set_sf_12;
       }
       size = 1024;
    }
    action set_sf_1(bit<8> action_param) {
       sf_1.write((bit<32>)(1), (bit<16>) action_param);
    }

    table mat_sf1 {
       key = {
           meta.nsf_1: lpm;
       }
       actions = {
           set_sf_1;
       }
       size = 1024;
    }
    action set_sf_3(bit<8> action_param) {
       sf_3.write((bit<32>)(1), (bit<16>) action_param);
    }

    table mat_sf3 {
       key = {
           meta.nsf_3: lpm;
       }
       actions = {
           set_sf_3;
       }
       size = 1024;
    }
    action set_sf_2(bit<8> action_param) {
       sf_2.write((bit<32>)(1), (bit<16>) action_param);
    }

    table mat_sf2 {
       key = {
           meta.nsf_6: lpm;
       }
       actions = {
           set_sf_2;
       }
       size = 1024;
    }




    apply {
        if (mat_nsf1.apply().hit){
            if (mat_nsf2.apply().hit){
                mat_sf123.apply();
            }else{
                mat_sf1.apply();
                mat_nsf3.apply();
                mat_nsf4.apply();
                mat_sf2.apply();
            }
        }else{
            mat_sf12.apply();
            mat_nsf5.apply();
            mat_sf3.apply();
        }



    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout local_metadata_t meta,
                 inout standard_metadata_t standard_metadata) {
    apply {  }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout local_metadata_t meta) {
     apply {

    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.my_hdr);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;