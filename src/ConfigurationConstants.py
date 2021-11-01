

LOG_FILE_PATH = "../log/mylog.log"
MAX_LOG_FILE_SIZE  =  52428800 #50 MB
MAX_LOG_FILE_BACKUP_COUNT = 250  # MAximum 25 files will be kept




DUMMY_START_NODE = "DUMMY_START_NODE"
DUMMY_END_NODE = "DUMMY_END_NODE"
SUPER_MAT_PREFIX = "SUPER_MAT_"
CONVERTED_ACTION_PREFIX = "CONVERTED_ACTION"

SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_INGRESS_KEY_NAME = "local_metadata.ingress_conditioanl_carry"
SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_INGRESS ={
                    "match_type" : "exact",
                    "name" : "local_metadata.ingress_conditioanl_carry",
                    "target" : ["local_metadata", "ingress_conditioanl_carry"],
                    "mask" : None
                }
SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_INGRESS_BIT_WIDTH = 8
SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_EGRESS ={
                    "match_type" : "exact",
                    "name" : "local_metadata.egress_conditioanl_carry",
                    "target" : ["local_metadata", "egress_conditioanl_carry"],
                    "mask" : None
                }
SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_EGRESS_BIT_WIDTH = 8
SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_EGRESS_KEY_NAME = "local_metadata.egress_conditioanl_carry"


