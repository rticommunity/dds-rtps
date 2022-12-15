from utilities import ReturnCode

# timeout for pexpect. short_timeout for the cases where there should not be communication
# and long_timeout for the cases where there should be
short_timeout = 5
long_timeout = 20


ReturnCode.export_to(globals())

dict_param_expected_code_timeout = {
    # DOMAIN
    'Test_Domain_0' : ['-P -t Square', '-S -t Square',
                         ReturnCode.OK, ReturnCode.OK, long_timeout], 
    'Test_Domain_1' : ['-P -t Square', '-S -t Square -d 1', 
                         ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED, short_timeout],
 
    # 'Test_Domain_3' : ['-P -t Square -d 1', '-S -t Square',
    #                      ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED, long_timeout], 
    # 'Test_Domain_4' : ['-P -t Square -d 1', '-S -t Square -d 1', 
    #                      ReturnCode.OK, ReturnCode.OK, short_timeout],

    # # RELIABILITY
    # 'Test_Reliability_0' : ['-P -t Square -b', '-S -t Square -b', 
    #                         ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Reliability_1' : ['-P -t Square -b', '-S -t Square -r', 
    #                         ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],



    # 'Test_Reliability_2' : ['-P -t Square -r', '-S -t Square -b', ReturnCode.OK, ReturnCode.OK, long_timeout],
    #  # reliable, but we only check that they exchange data  
    # 'Test_Reliability_3' : ['-P -t Square -r -k 3', '-S -t Square -r', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # #reliable, but we check that they receive the data in order 
    # 'Test_Reliability_4' : ['-P -t Square -r -k 0 -v', '-S -t Square -r -k 0', ReturnCode.OK, ReturnCode.OK, long_timeout],

    # # DEADLINE
    # 'Test_Deadline_0' : ['-P -t Square -f 3', '-S -t Square -f 5', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Deadline_1' : ['-P -t Square -f 5', '-S -t Square -f 5', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Deadline_2' : ['-P -t Square -f 7', '-S -t Square -f 5', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],
    
    # # OWNERSHIP
    # 'Test_Ownership_0': ['-P -t Square -s -1', '-S -t Square -s -1', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Ownership_1': ['-P -t Square -s -1', '-S -t Square -s 3', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],
    # 'Test_Ownership_2': ['-P -t Square -s 3', '-S -t Square -s -1', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],
    # # Two Publishers and One Subscriber to test that if each one has a different color, the ownership strength does not matter
    # 'Test_Ownership_3': ['-P -t Square -s 3 -c BLUE -v', '-P -t Square -s 4 -c RED -v', '-S -t Square -s 2 -r -k 0', 
    #                      ReturnCode.OK, ReturnCode.OK, ReturnCode.RECEIVING_FROM_BOTH,  long_timeout],
    # # Two Publishers and One Subscriber to test that the Subscriber only receives samples from the Publisher with the greatest ownership
    # 'Test_Ownership_4': ['-P -t Square -s 5 -r -k 0 -v', '-P -t Square -s 4 -r -k 0 -v', '-S -t Square -s 2 -r -k 0', 
    #                         ReturnCode.OK, ReturnCode.OK, ReturnCode.RECEIVING_FROM_ONE, long_timeout],

    # # TOPIC
    # 'Test_Topic_0' : ['-P -t Square', '-S -t Square', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Topic_1' : ['-P -t Square', '-S -t Circle', ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED, short_timeout],
    # 'Test_Topic_2' : ['-P -t Circle', '-S -t Square', ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED, short_timeout],
    # 'Test_Topic_3' : ['-P -t Circle', '-S -t Circle', ReturnCode.OK, ReturnCode.OK, long_timeout],

    # #COLOR
    # 'Test_Color_0' : ['-P -t Square -c BLUE', '-S -t Square -c BLUE', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Color_1' : ['-P -t Square -c BLUE', '-S -t Square -c RED', ReturnCode.OK, ReturnCode.DATA_NOT_RECEIVED, short_timeout],
    # 'Test_Color_2' : ['-P -t Square -c BLUE', '-S -t Square', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Color_3' : ['-P -t Square -c RED', '-S -t Square -c BLUE', ReturnCode.OK, ReturnCode.DATA_NOT_RECEIVED, short_timeout],
    # 'Test_Color_4' : ['-P -t Square -c RED', '-S -t Square -c RED', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Color_5' : ['-P -t Square -c RED', '-S -t Square', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Color_6' : ['-P -t Square', '-S -t Square -c BLUE', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Color_7' : ['-P -t Square', '-S -t Square -c RED', ReturnCode.OK, ReturnCode.DATA_NOT_RECEIVED, short_timeout],
    # 'Test_Color_8' : ['-P -t Square', '-S -t Square', ReturnCode.OK, ReturnCode.OK, long_timeout],

    # #PARTITION
    # 'Test_Partition_0' : ['-P -t Square -p "p1"', '-S -t Square -p "p1"', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Partition_1' : ['-P -t Square -p "p1"', '-S -t Square -p "p2"', ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED, short_timeout],
    # 'Test_Partition_2' : ['-P -t Square -p "p2"', '-S -t Square -p "p1"', ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED, short_timeout],
    # 'Test_Partition_3' : ['-P -t Square -p "p2"', '-S -t Square -p "p2"', ReturnCode.OK, ReturnCode.OK, long_timeout],

    # #DURABILITY
    # 'Test_Durability_0' : ['-P -t Square -D v', '-S -t Square -D v', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Durability_1' : ['-P -t Square -D v', '-S -t Square -D l', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],
    # 'Test_Durability_2' : ['-P -t Square -D v', '-S -t Square -D t', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],
    # 'Test_Durability_3' : ['-P -t Square -D v', '-S -t Square -D p', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],

    # 'Test_Durability_4' : ['-P -t Square -D l', '-S -t Square -D v', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Durability_5' : ['-P -t Square -D l', '-S -t Square -D l', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Durability_6' : ['-P -t Square -D l', '-S -t Square -D t', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],
    # 'Test_Durability_7' : ['-P -t Square -D l', '-S -t Square -D p', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],

    # 'Test_Durability_8' : ['-P -t Square -D t', '-S -t Square -D v', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Durability_9' : ['-P -t Square -D t', '-S -t Square -D l', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Durability_10': ['-P -t Square -D t', '-S -t Square -D t', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Durability_11': ['-P -t Square -D t', '-S -t Square -D p', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS, short_timeout],

    # 'Test_Durability_12' : ['-P -t Square -D p', '-S -t Square -D v', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Durability_13' : ['-P -t Square -D p', '-S -t Square -D l', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Durability_14' : ['-P -t Square -D p', '-S -t Square -D t', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_Durability_15' : ['-P -t Square -D p', '-S -t Square -D p', ReturnCode.OK, ReturnCode.OK, long_timeout],

    # #HISTORY
    # 'Test_History_0' : ['-P -t Square -k 3', '-S -t Square -k 3', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_History_1' : ['-P -t Square -k 3', '-S -t Square -k 0', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_History_2' : ['-P -t Square -k 0', '-S -t Square -k 3', ReturnCode.OK, ReturnCode.OK, long_timeout],
    # 'Test_History_3' : ['-P -t Square -k 0', '-S -t Square -k 0', ReturnCode.OK, ReturnCode.OK, long_timeout]
}