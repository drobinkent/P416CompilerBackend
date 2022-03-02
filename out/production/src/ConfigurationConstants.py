

LOG_FILE_PATH = "../log/mylog.log"
MAX_LOG_FILE_SIZE  =  52428800 #50 MB
MAX_LOG_FILE_BACKUP_COUNT = 250  # MAximum 25 files will be kept



BIFURCATED_MAT_NAME_PREFIX = "BIFURCATED_MAT_"

DUMMY_START_NODE = "DUMMY_START_NODE"
DUMMY_END_NODE = "DUMMY_END_NODE"
# SUPER_MAT_PREFIX = "SUPER_MAT_"
CONVERTED_ACTION_PREFIX = "CONVERTED_ACTION_FOR_"

SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_INGRESS_KEY_NAME = "scalars.userMetadata.ingress_conditioanl_carry"
SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_INGRESS ={
                    "match_type" : "exact",
                    "name" : "scalars.userMetadata.ingress_conditioanl_carry",
                    "target" : ["scalars.userMetadata", "ingress_conditioanl_carry"],
                    "mask" : None
                }
SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_INGRESS_BIT_WIDTH = 8

SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_EGRESS_KEY_NAME = "scalars.userMetadata.egress_conditioanl_carry"
SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_EGRESS ={
                    "match_type" : "exact",
                    "name" : "scalars.userMetadata.egress_conditioanl_carry",
                    "target" : ["scalars.userMetadata", "egress_conditioanl_carry"],
                    "mask" : None
                }
SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_EGRESS_BIT_WIDTH = 8


SPECIAL_KEY_FOR_DIVIDING_MAT_IN_INGRESS_NAME = "scalars.userMetadata.mat_divider"
SPECIAL_KEY_FOR_DIVIDING_MAT_IN_INGRESS ={
    "match_type" : "exact",
    "name" : "scalars.userMetadata.mat_divider",
    "target" : ["scalars.userMetadata", "mat_divider"],
    "mask" : None
}
SPECIAL_KEY_FOR_DIVIDING_MAT_IN_INGRESS_BIT_WIDTH = 8


SPECIAL_KEY_FOR_DIVIDING_MAT_IN_EGRESS_NAME = "scalars.userMetadata.mat_divider"
SPECIAL_KEY_FOR_DIVIDING_MAT_IN_EGRESS ={
    "match_type" : "exact",
    "name" : "scalars.userMetadata.mat_divider",
    "target" : ["scalars.userMetadata", "mat_divider"],
    "mask" : None
}
SPECIAL_KEY_FOR_DIVIDING_MAT_IN_EGRESS_BIT_WIDTH = 8

MAT_DIVIDER_KEY_COUNTER = 0
DIVIDED_MAT_MAX_ENTRIES= 64 #Each stage can handle 64 actions, therefore if we divide a MAT and make two MAT then the newly created stage can also habe maximum 65 actions.
# TODO: in future these should be in hardware deifinition


