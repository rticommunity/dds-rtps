from utilities import ReturnCode

# timeout for pexpect. short_timeout for the cases where there should not be communication
# and long_timeout for the cases where there should be
short_timeout = 5
long_timeout = 20


ReturnCode.export_to(globals())

dict_param_expected_code_timeout = {
    # DATA REPRESENTATION
    'Test_DataRepresentation_0' : ['-P -t Square -x 1', '-S -t Square -x 1',
                         ReturnCode.OK, ReturnCode.OK, long_timeout], 
    'Test_DataRepresentation_1' : ['-P -t Square -x 1', '-S -t Square -x 2', 
                         ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],
 
    'Test_DataRepresentation_2' : ['-P -t Square -x 2', '-S -t Square -x 1',
                         ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, long_timeout], 
    'Test_DataRepresentation_3' : ['-P -t Square -x 2', '-S -t Square -x 2', 
                         ReturnCode.OK, ReturnCode.OK, short_timeout],

    # DOMAIN
    'Test_Domain_0' : ['-P -t Square -x 2', '-S -t Square -x 2',
                         ReturnCode.OK, ReturnCode.OK, long_timeout], 
    'Test_Domain_1' : ['-P -t Square -x 2', '-S -t Square -d 1 -x 2', 
                         ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED, short_timeout],
 
    'Test_Domain_2' : ['-P -t Square -d 1 -x 2', '-S -t Square -x 2',
                         ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED, long_timeout], 
    'Test_Domain_3' : ['-P -t Square -d 1 -x 2', '-S -t Square -d 1 -x 2', 
                         ReturnCode.OK, ReturnCode.OK, short_timeout],

    #RELIABILITY
    'Test_Reliability_0' : ['-P -t Square -b -x 2', '-S -t Square -b -x 2', 
                            ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Reliability_1' : ['-P -t Square -b -x 2', '-S -t Square -r -x 2', 
                            ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],



    'Test_Reliability_2' : ['-P -t Square -r -x 2', '-S -t Square -b -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # reliable, but we only check that they exchange data  
    'Test_Reliability_3' : ['-P -t Square -r -k 3 -x 2', '-S -t Square -r -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # reliable, but we check that they receive the data in order 
    'Test_Reliability_4' : ['-P -t Square -r -k 0 -v -x 2', '-S -t Square -r -k 0 -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],

    # DEADLINE
    'Test_Deadline_0' : ['-P -t Square -f 3 -x 2', '-S -t Square -f 5 -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Deadline_1' : ['-P -t Square -f 5 -x 2', '-S -t Square -f 5 -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Deadline_2' : ['-P -t Square -f 7 -x 2', '-S -t Square -f 5 -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],
    
    # OWNERSHIP
    'Test_Ownership_0': ['-P -t Square -s -1 -x 2', '-S -t Square -s -1 -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Ownership_1': ['-P -t Square -s -1 -x 2', '-S -t Square -s 3 -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],
    'Test_Ownership_2': ['-P -t Square -s 3 -x 2', '-S -t Square -s -1 -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],
    # Two Publishers and One Subscriber to test that if each one has a different color, the ownership strength does not matter
    'Test_Ownership_3': ['-P -t Square -s 3 -c BLUE -v -x 2', '-P -t Square -s 4 -c RED -v -x 2', '-S -t Square -s 2 -r -k 0 -x 2', 
                         ReturnCode.OK, ReturnCode.OK, ReturnCode.RECEIVING_FROM_BOTH,  long_timeout],
    # Two Publishers and One Subscriber to test that the Subscriber only receives samples from the Publisher with the greatest ownership
    'Test_Ownership_4': ['-P -t Square -s 5 -r -k 0 -v -x 2', '-P -t Square -s 4 -r -k 0 -v -x 2', '-S -t Square -s 2 -r -k 0 -x 2', 
                            ReturnCode.OK, ReturnCode.OK, ReturnCode.RECEIVING_FROM_ONE, long_timeout],

    # TOPIC
    'Test_Topic_0' : ['-P -t Square -x 2', '-S -t Square -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Topic_1' : ['-P -t Square -x 2', '-S -t Circle -x 2', ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED, short_timeout],
    'Test_Topic_2' : ['-P -t Circle -x 2', '-S -t Square -x 2', ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED, short_timeout],
    'Test_Topic_3' : ['-P -t Circle -x 2', '-S -t Circle -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],

    #COLOR
    'Test_Color_0' : ['-P -t Square -c BLUE -x 2', '-S -t Square -c BLUE -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Color_1' : ['-P -t Square -c BLUE -x 2', '-S -t Square -c RED -x 2', ReturnCode.OK, ReturnCode.DATA_NOT_RECEIVED, short_timeout],
    'Test_Color_2' : ['-P -t Square -c BLUE -x 2', '-S -t Square -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Color_3' : ['-P -t Square -c RED -x 2', '-S -t Square -c BLUE -x 2', ReturnCode.OK, ReturnCode.DATA_NOT_RECEIVED, short_timeout],
    'Test_Color_4' : ['-P -t Square -c RED -x 2', '-S -t Square -c RED -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Color_5' : ['-P -t Square -c RED -x 2', '-S -t Square -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Color_6' : ['-P -t Square -x 2', '-S -t Square -c BLUE -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Color_7' : ['-P -t Square -x 2', '-S -t Square -c RED -x 2', ReturnCode.OK, ReturnCode.DATA_NOT_RECEIVED, short_timeout],
    'Test_Color_8' : ['-P -t Square -x 2', '-S -t Square -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],

    #PARTITION
    'Test_Partition_0' : ['-P -t Square -p "p1" -x 2', '-S -t Square -p "p1" -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Partition_1' : ['-P -t Square -p "p1" -x 2', '-S -t Square -p "p2" -x 2', ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED, short_timeout],
    'Test_Partition_2' : ['-P -t Square -p "p2" -x 2', '-S -t Square -p "p1" -x 2', ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED, short_timeout],
    'Test_Partition_3' : ['-P -t Square -p "p2" -x 2', '-S -t Square -p "p2" -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],

    #DURABILITY
    'Test_Durability_0' : ['-P -t Square -D v -x 2', '-S -t Square -D v -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Durability_1' : ['-P -t Square -D v -x 2', '-S -t Square -D l -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],
    'Test_Durability_2' : ['-P -t Square -D v -x 2', '-S -t Square -D t -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],
    'Test_Durability_3' : ['-P -t Square -D v -x 2', '-S -t Square -D p -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],

    'Test_Durability_4' : ['-P -t Square -D l -x 2', '-S -t Square -D v -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Durability_5' : ['-P -t Square -D l -x 2', '-S -t Square -D l -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Durability_6' : ['-P -t Square -D l -x 2', '-S -t Square -D t -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],
    'Test_Durability_7' : ['-P -t Square -D l -x 2', '-S -t Square -D p -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],

    'Test_Durability_8' : ['-P -t Square -D t -x 2', '-S -t Square -D v -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Durability_9' : ['-P -t Square -D t -x 2', '-S -t Square -D l -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Durability_10': ['-P -t Square -D t -x 2', '-S -t Square -D t -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Durability_11': ['-P -t Square -D t -x 2', '-S -t Square -D p -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],

    'Test_Durability_12' : ['-P -t Square -D p -x 2', '-S -t Square -D v -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Durability_13' : ['-P -t Square -D p -x 2', '-S -t Square -D l -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Durability_14' : ['-P -t Square -D p -x 2', '-S -t Square -D t -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_Durability_15' : ['-P -t Square -D p -x 2', '-S -t Square -D p -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],

    #HISTORY
    'Test_History_0' : ['-P -t Square -k 3 -x 2', '-S -t Square -k 3 -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_History_1' : ['-P -t Square -k 3 -x 2', '-S -t Square -k 0 -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_History_2' : ['-P -t Square -k 0 -x 2', '-S -t Square -k 3 -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout],
    'Test_History_3' : ['-P -t Square -k 0 -x 2', '-S -t Square -k 0 -x 2', ReturnCode.OK, ReturnCode.OK, long_timeout]
}