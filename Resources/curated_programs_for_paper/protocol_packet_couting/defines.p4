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

/* Should be 16 tables
 * Do we need check_ipv6_size though? it kinda sucks
 */
#define MAC_LEARN_RECEIVER 1024

#define CONTROL_TABLE_SIZE 256
#define IG_PHY_META_SIZE 4000
#define IG_SMAC_SIZE 128000
#define IG_PROPS_SIZE 4000
#define IG_BCAST_STORM_SIZE 64
#define IG_ACL1_SIZE 8000
#define IG_ROUTER_MAC_SIZE 1000
#define IPV4_UCAST_HOST_SIZE 128000
#define IPV4_UCAST_LPM_SIZE 16000
#define IPV4_MCAST_SIZE 32000
#define IPV4_URPF_SIZE 16000
#define IPV6_UCAST_HOST_SIZE 128000
#define IPV6_UCAST_LPM_SIZE 16000
#define IPV6_MCAST_SIZE 32000
#define IPV6_URPF_SIZE 16000
#define IPV4_ECMP_SIZE 256
#define IPV4_NEXTHOP_SIZE 1600
#define IPV6_ECMP_SIZE 245
#define IPV6_NEXTHOP_SIZE 1600
#define IG_DMAC_SIZE 128000
#define IG_AGG_INTF_SIZE 64
#define IG_ACL2_SIZE 8000
#define EG_PROPS_SIZE 64
#define EG_PHY_META_SIZE 4000
#define EG_ACL1_SIZE 16000

#define VRF_BIT_WIDTH 12
#define ECMP_BIT_WIDTH 36
#define L2_HASH_WIDTH 20
#define CONTROLLER_IP 9898989
