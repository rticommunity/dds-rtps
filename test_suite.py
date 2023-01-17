from utilities import ReturnCode

# rtps_test_suite_1 is a dictionary where we define the TestSuite
# (with its TestCases that we will test in interoperability_report.py).
# The dictionary has the following structure:
#       'name' : [parameters_publisher, parameters_subscriber,
#              expected_return_code_publisher, expected_return_code_subscriber]
# where:
#       * name is the TestCase's name (defined by us)
#       * parameters_publisher are the parameters we will run with
#         the shape_main publisher application
#       * parameters_subscriber are the parameters we will run with
#         the shape_main subscriber application
#       * expected_return_code_publisher is the ReturnCode the publisher
#         is expected to produce in a non error situation
#       * expected_return_code_subscriber is the ReturnCode the subscriber
#         is expected to produce in a non error situation
#
# There are also two testCases that contains more parameters:
#       Test_Ownership_3 and Test_Ownership_4.
# That is because in these two cases two publishers are run
# (and one subscriber).
# The parameters in this case are:
#       * name is the TestCase's name (defined by us)
#       * parameters_publisher1 are the parameters we will run
#         with the shape_main publisher 1 application
#       * parameters_publisher2 are the parameters we will run
#         with the shape_main publisher 2 application
#       * parameters_subscriber are the parameters we will run
#         with the shape_main subscriber application
#       * expected_return_code_publisher1 is the ReturnCode the
#         publisher 1 is expected to produce in a non error situation
#       * expected_return_code_publisher2 is the ReturnCode the publisher 2
#         is expected to produce in a non error situation
#       * expected_return_code_subscriber is the ReturnCode the subscriber
#         is expected to produce in a non error situation

rtps_test_suite_1 = {
    # DATA REPRESENTATION
    'Test_DataRepresentation_0' : ['-P -t Square -x 1', '-S -t Square -x 1', ReturnCode.OK, ReturnCode.OK],
    'Test_DataRepresentation_1' : ['-P -t Square -x 1', '-S -t Square -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS],
    'Test_DataRepresentation_2' : ['-P -t Square -x 2', '-S -t Square -x 1', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS],
    'Test_DataRepresentation_3' : ['-P -t Square -x 2', '-S -t Square -x 2', ReturnCode.OK, ReturnCode.OK],

    # DOMAIN
    'Test_Domain_0' : ['-P -t Square -x 2', '-S -t Square -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Domain_1' : ['-P -t Square -x 2', '-S -t Square -d 1 -x 2', ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED],
    'Test_Domain_2' : ['-P -t Square -d 1 -x 2', '-S -t Square -x 2', ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED],
    'Test_Domain_3' : ['-P -t Square -d 1 -x 2', '-S -t Square -d 1 -x 2', ReturnCode.OK, ReturnCode.OK],

    # RELIABILITY
    'Test_Reliability_0' : ['-P -t Square -b -x 2', '-S -t Square -b -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Reliability_1' : ['-P -t Square -b -x 2', '-S -t Square -r -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS],
    'Test_Reliability_2' : ['-P -t Square -r -x 2', '-S -t Square -b -x 2', ReturnCode.OK, ReturnCode.OK],
    # This test only checks that data is received correctly
    'Test_Reliability_3' : ['-P -t Square -r -k 3 -x 2', '-S -t Square -r -x 2', ReturnCode.OK, ReturnCode.OK],
    # This test checks that data is received in the right order
    'Test_Reliability_4' : ['-P -t Square -r -k 0 -w -x 2', '-S -t Square -r -k 0 -x 2', ReturnCode.OK, ReturnCode.OK],

    # DEADLINE
    'Test_Deadline_0' : ['-P -t Square -f 3 -x 2', '-S -t Square -f 5 -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Deadline_1' : ['-P -t Square -f 5 -x 2', '-S -t Square -f 5 -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Deadline_2' : ['-P -t Square -f 7 -x 2', '-S -t Square -f 5 -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS],

    # OWNERSHIP
    'Test_Ownership_0': ['-P -t Square -s -1 -x 2', '-S -t Square -s -1 -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Ownership_1': ['-P -t Square -s -1 -x 2', '-S -t Square -s 3 -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS],
    'Test_Ownership_2': ['-P -t Square -s 3 -x 2', '-S -t Square -s -1 -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS],
    # Two Publishers and One Subscriber to test that if each one has a different color, the ownership strength does not matter
    'Test_Ownership_3': ['-P -t Square -s 3 -c BLUE -w -x 2', '-P -t Square -s 4 -c RED -w -x 2', '-S -t Square -s 2 -r -k 0 -x 2',
                         ReturnCode.OK, ReturnCode.OK, ReturnCode.RECEIVING_FROM_BOTH],
    # Two Publishers and One Subscriber to test that the Subscriber only receives samples from the Publisher with the greatest ownership
    'Test_Ownership_4': ['-P -t Square -s 5 -r -k 0 -w -x 2', '-P -t Square -s 4 -r -k 0 -w -x 2', '-S -t Square -s 2 -r -k 0 -x 2',
                         ReturnCode.OK, ReturnCode.OK, ReturnCode.RECEIVING_FROM_ONE],

    # TOPIC
    'Test_Topic_0' : ['-P -t Square -x 2', '-S -t Square -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Topic_1' : ['-P -t Square -x 2', '-S -t Circle -x 2', ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED],
    'Test_Topic_2' : ['-P -t Circle -x 2', '-S -t Square -x 2', ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED],
    'Test_Topic_3' : ['-P -t Circle -x 2', '-S -t Circle -x 2', ReturnCode.OK, ReturnCode.OK],

    # COLOR
    'Test_Color_0' : ['-P -t Square -c BLUE -x 2', '-S -t Square -c BLUE -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Color_1' : ['-P -t Square -c BLUE -x 2', '-S -t Square -c RED -x 2', ReturnCode.OK, ReturnCode.DATA_NOT_RECEIVED],
    'Test_Color_2' : ['-P -t Square -c BLUE -x 2', '-S -t Square -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Color_3' : ['-P -t Square -c RED -x 2', '-S -t Square -c BLUE -x 2', ReturnCode.OK, ReturnCode.DATA_NOT_RECEIVED],
    'Test_Color_4' : ['-P -t Square -c RED -x 2', '-S -t Square -c RED -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Color_5' : ['-P -t Square -c RED -x 2', '-S -t Square -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Color_6' : ['-P -t Square -x 2', '-S -t Square -c BLUE -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Color_7' : ['-P -t Square -x 2', '-S -t Square -c RED -x 2', ReturnCode.OK, ReturnCode.DATA_NOT_RECEIVED],
    'Test_Color_8' : ['-P -t Square -x 2', '-S -t Square -x 2', ReturnCode.OK, ReturnCode.OK],

    # PARTITION
    'Test_Partition_0' : ['-P -t Square -p "p1" -x 2', '-S -t Square -p "p1" -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Partition_1' : ['-P -t Square -p "p1" -x 2', '-S -t Square -p "p2" -x 2', ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED],
    'Test_Partition_2' : ['-P -t Square -p "p2" -x 2', '-S -t Square -p "p1" -x 2', ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED],
    'Test_Partition_3' : ['-P -t Square -p "p2" -x 2', '-S -t Square -p "p2" -x 2', ReturnCode.OK, ReturnCode.OK],

    # DURABILITY
    'Test_Durability_0' : ['-P -t Square -D v -x 2', '-S -t Square -D v -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Durability_1' : ['-P -t Square -D v -x 2', '-S -t Square -D l -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS],
    'Test_Durability_2' : ['-P -t Square -D v -x 2', '-S -t Square -D t -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS],
    'Test_Durability_3' : ['-P -t Square -D v -x 2', '-S -t Square -D p -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS],

    'Test_Durability_4' : ['-P -t Square -D l -x 2', '-S -t Square -D v -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Durability_5' : ['-P -t Square -D l -x 2', '-S -t Square -D l -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Durability_6' : ['-P -t Square -D l -x 2', '-S -t Square -D t -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS],
    'Test_Durability_7' : ['-P -t Square -D l -x 2', '-S -t Square -D p -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS],

    'Test_Durability_8' : ['-P -t Square -D t -x 2', '-S -t Square -D v -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Durability_9' : ['-P -t Square -D t -x 2', '-S -t Square -D l -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Durability_10': ['-P -t Square -D t -x 2', '-S -t Square -D t -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Durability_11': ['-P -t Square -D t -x 2', '-S -t Square -D p -x 2', ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS],

    'Test_Durability_12' : ['-P -t Square -D p -x 2', '-S -t Square -D v -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Durability_13' : ['-P -t Square -D p -x 2', '-S -t Square -D l -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Durability_14' : ['-P -t Square -D p -x 2', '-S -t Square -D t -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_Durability_15' : ['-P -t Square -D p -x 2', '-S -t Square -D p -x 2', ReturnCode.OK, ReturnCode.OK],

    # HISTORY
    'Test_History_0' : ['-P -t Square -k 3 -x 2', '-S -t Square -k 3 -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_History_1' : ['-P -t Square -k 3 -x 2', '-S -t Square -k 0 -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_History_2' : ['-P -t Square -k 0 -x 2', '-S -t Square -k 3 -x 2', ReturnCode.OK, ReturnCode.OK],
    'Test_History_3' : ['-P -t Square -k 0 -x 2', '-S -t Square -k 0 -x 2', ReturnCode.OK, ReturnCode.OK]
}
