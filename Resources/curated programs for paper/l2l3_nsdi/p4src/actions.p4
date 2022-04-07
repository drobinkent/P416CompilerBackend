action set_mcast_idx(idx) {
  modify_field(meta.mcast_ind, idx);
}

action set_sMac(sMac) {
  modify_field(ethernet.sMac, sMac);
}

// dMac
// vlan

// set_egress
// set_drop_code