from enum import Enum

class ErrorCode(Enum):
    TOPIC_NOT_CREATED = 0
    READER_NOT_CREATED = 1
    WRITER_NOT_MATCHED = 2
    UNRECOGNIZED_VALUE = 3
    FILTER_NOT_CREATED = 4
    INCOMPATIBLE_QOS = 5
    WRITER_NOT_ALIVE = 6
    WRITER_NOT_CREATED = 7
    READER_NOT_MATCHED = 8
    DATA_NOT_RECEIVED = 9
    DATA_NOT_SENT = 10
    DATA_NOT_CORRECT = 11
    RECEIVING_FROM_ONE = 12
    RECEIVING_FROM_BOTH = 13
    OK = 14

ErrorCode = Enum('ErrorCode', 
                [
                    'TOPIC_NOT_CREATED', 'READER_NOT_CREATED', 'WRITER_NOT_MATCHED',
                    'WRITER_NOT_CREATED', 'UNRECOGNIZED_VALUE', 'FILTER_NOT_CREATED', 
                    'INCOMPATIBLE_QOS', 'WRITER_NOT_ALIVE', 'READER_NOT_MATCHED', 
                    'DATA_NOT_RECEIVED', 'DATA_NOT_SENT', 'DATA_NOT_CORRECT', 
                    'RECEIVING_FROM_ONE', 'RECEIVING_FROM_BOTH',
                    'OK'
                ])


short_timeout = 5
long_timeout = 20


dict_param_expected_code_timeout = {
    # DOMAIN
    'Test_Domain_0' : ['-P -t Square', '-S -t Square', ErrorCode.OK, ErrorCode.OK,  long_timeout], 
    'Test_Domain_1' : ['-P -t Square', '-S -t Square -d 1', ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED, short_timeout],
    'Test_Domain_2' : ['-P -t Square -d 1', '-S -t Square', ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED, short_timeout],
    'Test_Domain_3' : ['-P -t Square -d 1', '-S -t Square -d 1', ErrorCode.OK, ErrorCode.OK, long_timeout],

    # RELIABILITY
    'Test_Reliability_0' : ['-P -t Square -b', '-S -t Square -b', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Reliability_1' : ['-P -t Square -b', '-S -t Square -r', ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, short_timeout],
    'Test_Reliability_2' : ['-P -t Square -r', '-S -t Square -b', ErrorCode.OK, ErrorCode.OK, long_timeout],
     # reliable, but we only check that they exchange data  
    'Test_Reliability_3' : ['-P -t Square -r -k 3', '-S -t Square -r', ErrorCode.OK, ErrorCode.OK, long_timeout],

    # DEADLINE
    'Test_Deadline_0' : ['-P -t Square -f 3', '-S -t Square -f 5', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Deadline_1' : ['-P -t Square -f 5', '-S -t Square -f 5', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Deadline_2' : ['-P -t Square -f 7', '-S -t Square -f 5', ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, short_timeout],
    
    # OWNERSHIP
    'Test_Ownership_0': ['-P -t Square -s -1', '-S -t Square -s -1', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Ownership_1': ['-P -t Square -s -1', '-S -t Square -s 3', ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, short_timeout],
    'Test_Ownership_2': ['-P -t Square -s 3', '-S -t Square -s -1', ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, short_timeout],
    #Two Publishers and One Subscriber to test that if each one has a different color, the ownership strength does not matter
    'Test_Ownership_3': ['-P -t Square -s 3 -c BLUE', '-P -t Square -s 4 -c RED', '-S -t Square -s 2 -r -k 3', 
                         ErrorCode.OK, ErrorCode.OK, ErrorCode.RECEIVING_FROM_BOTH,  long_timeout],

    # TOPIC
    'Test_Topic_0' : ['-P -t Square', '-S -t Square', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Topic_1' : ['-P -t Square', '-S -t Circle', ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED, short_timeout],
    'Test_Topic_2' : ['-P -t Circle', '-S -t Square', ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED, short_timeout],
    'Test_Topic_3' : ['-P -t Circle', '-S -t Circle', ErrorCode.OK, ErrorCode.OK, long_timeout],

    #COLOR
    'Test_Color_0' : ['-P -t Square -c BLUE', '-S -t Square -c BLUE', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Color_1' : ['-P -t Square -c BLUE', '-S -t Square -c RED', ErrorCode.OK, ErrorCode.DATA_NOT_RECEIVED, short_timeout],
    'Test_Color_2' : ['-P -t Square -c BLUE', '-S -t Square', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Color_3' : ['-P -t Square -c RED', '-S -t Square -c BLUE', ErrorCode.OK, ErrorCode.DATA_NOT_RECEIVED, short_timeout],
    'Test_Color_4' : ['-P -t Square -c RED', '-S -t Square -c RED', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Color_5' : ['-P -t Square -c RED', '-S -t Square', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Color_6' : ['-P -t Square', '-S -t Square -c BLUE', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Color_7' : ['-P -t Square', '-S -t Square -c RED', ErrorCode.OK, ErrorCode.DATA_NOT_RECEIVED, short_timeout],
    'Test_Color_8' : ['-P -t Square', '-S -t Square', ErrorCode.OK, ErrorCode.OK, long_timeout],

    #PARTITION
    'Test_Partition_0' : ['-P -t Square -p "p1"', '-S -t Square -p "p1"', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Partition_1' : ['-P -t Square -p "p1"', '-S -t Square -p "p2"', ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED, short_timeout],
    'Test_Partition_2' : ['-P -t Square -p "p2"', '-S -t Square -p "p1"', ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED, short_timeout],
    'Test_Partition_3' : ['-P -t Square -p "p2"', '-S -t Square -p "p2"', ErrorCode.OK, ErrorCode.OK, long_timeout],

    #DURABILITY
    'Test_Durability_0' : ['-P -t Square -D v', '-S -t Square -D v', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Durability_1' : ['-P -t Square -D v', '-S -t Square -D l', ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, short_timeout],
    'Test_Durability_2' : ['-P -t Square -D v', '-S -t Square -D t', ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, short_timeout],
    'Test_Durability_3' : ['-P -t Square -D v', '-S -t Square -D p', ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, short_timeout],

    'Test_Durability_4' : ['-P -t Square -D l', '-S -t Square -D v', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Durability_5' : ['-P -t Square -D l', '-S -t Square -D l', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Durability_6' : ['-P -t Square -D l', '-S -t Square -D t', ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, short_timeout],
    'Test_Durability_7' : ['-P -t Square -D l', '-S -t Square -D p', ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, short_timeout],

    'Test_Durability_8' : ['-P -t Square -D t', '-S -t Square -D v', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Durability_9' : ['-P -t Square -D t', '-S -t Square -D l', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Durability_10': ['-P -t Square -D t', '-S -t Square -D t', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Durability_11': ['-P -t Square -D t', '-S -t Square -D p', ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, short_timeout],

    'Test_Durability_12' : ['-P -t Square -D p', '-S -t Square -D v', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Durability_13' : ['-P -t Square -D p', '-S -t Square -D l', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Durability_14' : ['-P -t Square -D p', '-S -t Square -D t', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_Durability_15' : ['-P -t Square -D p', '-S -t Square -D p', ErrorCode.OK, ErrorCode.OK, long_timeout],

    #HISTORY
    'Test_History_0' : ['-P -t Square -k 3', '-S -t Square -k 3', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_History_1' : ['-P -t Square -k 3', '-S -t Square -k 0', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_History_2' : ['-P -t Square -k 0', '-S -t Square -k 3', ErrorCode.OK, ErrorCode.OK, long_timeout],
    'Test_History_3' : ['-P -t Square -k 0', '-S -t Square -k 0', ErrorCode.OK, ErrorCode.OK, long_timeout],
}


names = {
    'connext6.1.1' : '/home/carias/shape_main/dds-rtps/srcCxx/objs/x64Linux4gcc7.3.0/connext6.1.1_shape_main',
    'opendds' : '/home/carias/shape_main/opendds3.21_shape_main_linux'
    #'connext5.2.3' : '/home/carias/shape_main/5.2.3/rti_shapes_5.2.3_linux'
}