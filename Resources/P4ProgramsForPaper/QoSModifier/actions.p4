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






action set_ipv4_ipv6_qos(){
    register_write(ipv4_port_qos, control_packet.index, control_packet.ipv4_diffserv);
    register_write(ipv6_port_qos, control_packet.index, control_packet.ipv6_trafficClass);

}
register ipv4_port_qos {
    width: 8;
    //static: m_table;
    instance_count: 128;
}



action set_next_hop_ipv4(port) {
      modify_field(hop_metadata.egress_port, port);
       register_read(ipv4.diffserv, ipv4_port_qos, port);
       modify_field(ipv6.dstAddr, CONTROLLER_IP);
}


register ipv6_port_qos {
    width: 8;
    //static: m_table;
    instance_count: 128;
}


action set_next_hop_ipv6(port) {
     modify_field(hop_metadata.egress_port, port);

    register_read(ipv6.trafficClass, ipv6_port_qos, port);
}



action set_egress_port(e_port) {
    modify_field(standard_metadata.egress_spec, e_port);
}


