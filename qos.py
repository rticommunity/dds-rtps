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
    'Test_Domain_0' :
        ['-t Square', '-t Square', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout], 
    'Test_Domain_1' :
        ['-t Square', '-t Square -d 1', 
                ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED, 
                short_timeout],
    'Test_Domain_2':
        ['-t Square -d 1', '-t Square', 
                ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED,  
                short_timeout],
    'Test_Domain_3':
        ['-t Square -d 1', '-t Square -d 1', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],

    # RELIABILITY
    'Test_Reliability_0':
        ['-t Square -b', '-t Square -b', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Reliability_1':
        ['-t Square -b', '-t Square -r', 
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS,  
                short_timeout],
    'Test_Reliability_2':
        ['-t Square -r', '-t Square -b', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Reliability_3':
    # reliable, but we only check that they exchange data       
        ['-t Square -r -k 3', '-t Square -r', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],

    # DEADLINE
    'Test_Deadline_0':
        ['-t Square -f 3', '-t Square -f 5', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Deadline_1':
        ['-t Square -f 5', '-t Square -f 5', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Deadline_2':
        ['-t Square -f 7', '-t Square -f 5', 
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS,  
                short_timeout],
    
    # OWNERSHIP
    'Test_Ownership_0':
        ['-t Square -s -1', '-t Square -s -1', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Ownership_1':
        ['-t Square -s -1', '-t Square -s 3', 
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, 
                short_timeout],
    'Test_Ownership_2':
        ['-t Square -s 3', '-t Square -s -1', 
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, 
                short_timeout],
    'Test_Ownership_3':
        ['-t Square -s 3 -c BLUE', '-t Square -s 4 -c RED',
                    '-t Square -s 2 -r -k 3', 
                ErrorCode.OK, ErrorCode.OK, ErrorCode.RECEIVING_FROM_BOTH, 
                long_timeout],

    # TOPIC
    'Test_Topic_0':
        ['-t Square', '-t Square', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Topic_1':
        ['-t Square', '-t Circle', 
                ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED,  
                short_timeout],
    'Test_Topic_2':
        ['-t Circle', '-t Square', 
                ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED,
                short_timeout],
    'Test_Topic_3':
        ['-t Circle', '-t Circle', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],

    # COLOR
    'Test_Color_0':
        ['-t Square -c BLUE', '-t Square -c BLUE', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Color_1':
        ['-t Square -c BLUE', '-t Square -c RED', 
                ErrorCode.OK, ErrorCode.DATA_NOT_RECEIVED,  
                short_timeout],
    'Test_Color_2':
        ['-t Square -c BLUE', '-t Square', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Color_3':
        ['-t Square -c RED', '-t Square -c BLUE', 
                ErrorCode.OK, ErrorCode.DATA_NOT_RECEIVED,  
                short_timeout],
    'Test_Color_4':
        ['-t Square -c RED', '-t Square -c RED', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Color_5':
        ['-t Square -c RED', '-t Square', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Color_6':
        ['-t Square', '-t Square -c BLUE', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Color_7':
        ['-t Square', '-t Square -c RED', 
                ErrorCode.OK, ErrorCode.DATA_NOT_RECEIVED,  
                short_timeout],
    'Test_Color_8':
        ['-t Square', '-t Square', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],

    # PARTITION
    'Test_Partition_0':
        ['-t Square -p "p1"', '-t Square -p "p1"', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Partition_1':
        ['-t Square -p "p1"', '-t Square -p "p2"',  
                ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED, 
                short_timeout],
    'Test_Partition_2':
        ['-t Square -p "p2"', '-t Square -p "p1"', 
                ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED,  
                short_timeout],
    'Test_Partition_3':
        ['-t Square -p "p2"', '-t Square -p "p2"',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],

    # DURABILITY
    'Test_Durability_0':
        [ '-t Square -D v', '-t Square -D v', 
                ErrorCode.OK, ErrorCode.OK, 
                long_timeout],
    'Test_Durability_1':
        ['-t Square -D v', '-t Square -D l', 
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS,  
                short_timeout],
    'Test_Durability_2':
        ['-t Square -D v', '-t Square -D t', 
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS,  
                short_timeout],
    'Test_Durability_3':
        ['-t Square -D v', '-t Square -D p', 
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS,  
                short_timeout],

    'Test_Durability_4':
        [ '-t Square -D l', '-t Square -D v',
                ErrorCode.OK, ErrorCode.OK, 
                long_timeout],
    'Test_Durability_5':
        ['-t Square -D l', '-t Square -D l',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Durability_6':
        ['-t Square -D l', '-t Square -D t',
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS,  
                short_timeout],
    'Test_Durability_7':
        ['-t Square -D l', '-t Square -D p',
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS,  
                short_timeout],

    'Test_Durability_8':
        ['-t Square -D t', '-t Square -D v',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Durability_9':
        ['-t Square -D t', '-t Square -D l',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Durability_10':
        ['-t Square -D t', '-t Square -D t',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Durability_11':
        ['-t Square -D t', '-t Square -D p',
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, 
                short_timeout],

    'Test_Durability_12':
        ['-t Square -D p', '-t Square -D v',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Durability_13':
        ['-t Square -D p', '-t Square -D l',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Durability_14':
        ['-t Square -D p', '-t Square -D t',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    'Test_Durability_15':
        ['-t Square -D p', '-t Square -D p',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],

    # HISTORY
    'Test_History_0':
    [ '-t Square -k 3', '-t Square -k 3',
            ErrorCode.OK, ErrorCode.OK, 
            long_timeout],
    'Test_History_1':
    ['-t Square -k 3', '-t Square -k 0',
            ErrorCode.OK, ErrorCode.OK,  
            long_timeout],
    'Test_History_2':
    ['-t Square -k 0', '-t Square -k 3',
            ErrorCode.OK, ErrorCode.OK,  
            long_timeout],
    'Test_History_3':
    ['-t Square -k 0', '-t Square -k 0',
            ErrorCode.OK, ErrorCode.OK,  
            long_timeout],
}