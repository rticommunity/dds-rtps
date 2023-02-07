from rtps_test_utilities import ReturnCode, log_message
import re
import pexpect
# rtps_test_suite_1 is a dictionary where we define the TestSuite
# (with its TestCases that we will test in interoperability_report.py).
# The dictionary has the following structure:
#       'name' : [[parameters], [expected_return_codes], <OPTIONAL>:function]
# where:
#       * name: TestCase's name (defined by us)
#       * parameters: list with parameters for the shape_main application.
#       * expected_return_codes: list with expected ReturnCode
#         for a succeed test execution.
#       * function[OPTIONAL]: function to check how the Subscribers receive
#         the samples from the Publishers. By default it does not check
#         anything.
# The number of elements in parameters will define how many shape_main
# application we will run. It should be the same as the number of
# elements in expected_return_codes.
#
# test_ownership3_4 and test_reliability_4 are two functions defined
# to check how the Subscriber receives the samples.

# It checks from which Publisher the Subscriber is receiving the samples.
def test_ownership3_4(child_sub, samples_sent, timeout, verbosity):
    first_received_first_time = False
    second_received_first_time = False
    first_received = False
    second_received = False
    list_data_received_second = []
    max_samples_received = 80
    max_wait_time = 5
    for x in range(0,max_samples_received,1):
        sub_string = re.search('[0-9]{3} [0-9]{3}',
            child_sub.before)
        try:
            list_data_received_second.append(samples_sent[1].get(True, max_wait_time))
        except:
            break
        if sub_string.group(0) not in list_data_received_second \
                and second_received_first_time:
            first_received = True
        elif sub_string.group(0) in list_data_received_second \
                and first_received_first_time:
            second_received = True

        if sub_string.group(0) not in list_data_received_second:
            first_received_first_time = True
        elif sub_string.group(0) in list_data_received_second:
            second_received_first_time = True
        log_message('S: Waiting for receiving samples', verbosity)
        child_sub.expect(
            [
                '\[[0-9][0-9]\]', # index = 0
                pexpect.TIMEOUT # index = 1
            ],
            timeout
        )
        if second_received == True and first_received == True:
            return ReturnCode.RECEIVING_FROM_BOTH

    return ReturnCode.RECEIVING_FROM_ONE

# It checks if the Subscriber is receiving the samples in order.
def test_reliability_4(child_sub, samples_sent, timeout, verbosity):
    max_samples_received = 3
    max_wait_time = 5
    for x in range(0, max_samples_received, 1):
        sub_string = re.search('[0-9]{3} [0-9]{3}', child_sub.before)
        if samples_sent[0].get(True,max_wait_time) == sub_string.group(0):
            produced_code = ReturnCode.OK
        else:
            produced_code = ReturnCode.DATA_NOT_CORRECT
            break
        log_message('S: Waiting for receiving samples', verbosity)
        child_sub.expect(
            [
                '\[[0-9][0-9]\]', # index = 0
                pexpect.TIMEOUT # index = 1
            ],
            timeout
        )
    return produced_code

rtps_test_suite_1 = {
    # DATA REPRESENTATION
    'Test_DataRepresentation_0' : [['-P -t Square -x 1', '-S -t Square -x 1'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_DataRepresentation_1' : [['-P -t Square -x 1', '-S -t Square -x 2'], [ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS]],
    'Test_DataRepresentation_2' : [['-P -t Square -x 2', '-S -t Square -x 1'], [ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS]],
    'Test_DataRepresentation_3' : [['-P -t Square -x 2', '-S -t Square -x 2'], [ReturnCode.OK, ReturnCode.OK]],

    # DOMAIN
    'Test_Domain_0' : [['-P -t Square -x 2', '-S -t Square -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Domain_1' : [['-P -t Square -x 2', '-S -t Square -d 1 -x 2'], [ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED]],
    'Test_Domain_2' : [['-P -t Square -d 1 -x 2', '-S -t Square -x 2'], [ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED]],
    'Test_Domain_3' : [['-P -t Square -d 1 -x 2', '-S -t Square -d 1 -x 2'], [ReturnCode.OK, ReturnCode.OK]],

    # RELIABILITY
    'Test_Reliability_0' : [['-P -t Square -b -x 2', '-S -t Square -b -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Reliability_1' : [['-P -t Square -b -x 2', '-S -t Square -r -x 2'], [ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS]],
    'Test_Reliability_2' : [['-P -t Square -r -x 2', '-S -t Square -b -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    # This test only checks that data is received correctly
    'Test_Reliability_3' : [['-P -t Square -r -k 3 -x 2', '-S -t Square -r -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    # This test checks that data is received in the right order
    'Test_Reliability_4' : [['-P -t Square -r -k 0 -w -x 2', '-S -t Square -r -k 0 -x 2'], [ReturnCode.OK, ReturnCode.OK], test_reliability_4],

    # DEADLINE
    'Test_Deadline_0' : [['-P -t Square -f 3 -x 2', '-S -t Square -f 5 -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Deadline_1' : [['-P -t Square -f 5 -x 2', '-S -t Square -f 5 -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Deadline_2' : [['-P -t Square -f 7 -x 2', '-S -t Square -f 5 -x 2'], [ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS]],

    # OWNERSHIP
    'Test_Ownership_0': [['-P -t Square -s -1 -x 2', '-S -t Square -s -1 -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Ownership_1': [['-P -t Square -s -1 -x 2', '-S -t Square -s 3 -x 2'], [ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS]],
    'Test_Ownership_2': [['-P -t Square -s 3 -x 2', '-S -t Square -s -1 -x 2'], [ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS]],

    # TOPIC
    'Test_Topic_0' : [['-P -t Square -x 2', '-S -t Square -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Topic_1' : [['-P -t Square -x 2', '-S -t Circle -x 2'], [ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED]],
    'Test_Topic_2' : [['-P -t Circle -x 2', '-S -t Square -x 2'], [ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED]],
    'Test_Topic_3' : [['-P -t Circle -x 2', '-S -t Circle -x 2'], [ReturnCode.OK, ReturnCode.OK]],

    # COLOR
    'Test_Color_0' : [['-P -t Square -c BLUE -x 2', '-S -t Square -c BLUE -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Color_1' : [['-P -t Square -c BLUE -x 2', '-S -t Square -c RED -x 2'], [ReturnCode.OK, ReturnCode.DATA_NOT_RECEIVED]],
    'Test_Color_2' : [['-P -t Square -c BLUE -x 2', '-S -t Square -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Color_3' : [['-P -t Square -c RED -x 2', '-S -t Square -c BLUE -x 2'], [ReturnCode.OK, ReturnCode.DATA_NOT_RECEIVED]],
    'Test_Color_4' : [['-P -t Square -c RED -x 2', '-S -t Square -c RED -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Color_5' : [['-P -t Square -c RED -x 2', '-S -t Square -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Color_6' : [['-P -t Square -x 2', '-S -t Square -c BLUE -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Color_7' : [['-P -t Square -x 2', '-S -t Square -c RED -x 2'], [ReturnCode.OK, ReturnCode.DATA_NOT_RECEIVED]],
    'Test_Color_8' : [['-P -t Square -x 2', '-S -t Square -x 2'], [ReturnCode.OK, ReturnCode.OK]],

    # PARTITION
    'Test_Partition_0' : [['-P -t Square -p "p1" -x 2', '-S -t Square -p "p1" -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Partition_1' : [['-P -t Square -p "p1" -x 2', '-S -t Square -p "p2" -x 2'], [ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED]],
    'Test_Partition_2' : [['-P -t Square -p "p2" -x 2', '-S -t Square -p "p1" -x 2'], [ReturnCode.READER_NOT_MATCHED, ReturnCode.WRITER_NOT_MATCHED]],
    'Test_Partition_3' : [['-P -t Square -p "p2" -x 2', '-S -t Square -p "p2" -x 2'], [ReturnCode.OK, ReturnCode.OK]],

    # DURABILITY
    'Test_Durability_0' : [['-P -t Square -D v -x 2', '-S -t Square -D v -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Durability_1' : [['-P -t Square -D v -x 2', '-S -t Square -D l -x 2'], [ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS]],
    'Test_Durability_2' : [['-P -t Square -D v -x 2', '-S -t Square -D t -x 2'], [ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS]],
    'Test_Durability_3' : [['-P -t Square -D v -x 2', '-S -t Square -D p -x 2'], [ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS]],

    'Test_Durability_4' : [['-P -t Square -D l -x 2', '-S -t Square -D v -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Durability_5' : [['-P -t Square -D l -x 2', '-S -t Square -D l -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Durability_6' : [['-P -t Square -D l -x 2', '-S -t Square -D t -x 2'], [ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS]],
    'Test_Durability_7' : [['-P -t Square -D l -x 2', '-S -t Square -D p -x 2'], [ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS]],

    'Test_Durability_8' : [['-P -t Square -D t -x 2', '-S -t Square -D v -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Durability_9' : [['-P -t Square -D t -x 2', '-S -t Square -D l -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Durability_10': [['-P -t Square -D t -x 2', '-S -t Square -D t -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Durability_11': [['-P -t Square -D t -x 2', '-S -t Square -D p -x 2'], [ReturnCode.INCOMPATIBLE_QOS, ReturnCode.INCOMPATIBLE_QOS]],

    'Test_Durability_12' : [['-P -t Square -D p -x 2', '-S -t Square -D v -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Durability_13' : [['-P -t Square -D p -x 2', '-S -t Square -D l -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Durability_14' : [['-P -t Square -D p -x 2', '-S -t Square -D t -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_Durability_15' : [['-P -t Square -D p -x 2', '-S -t Square -D p -x 2'], [ReturnCode.OK, ReturnCode.OK]],

    # HISTORY
    'Test_History_0' : [['-P -t Square -k 3 -x 2', '-S -t Square -k 3 -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_History_1' : [['-P -t Square -k 3 -x 2', '-S -t Square -k 0 -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_History_2' : [['-P -t Square -k 0 -x 2', '-S -t Square -k 3 -x 2'], [ReturnCode.OK, ReturnCode.OK]],
    'Test_History_3' : [['-P -t Square -k 0 -x 2', '-S -t Square -k 0 -x 2'], [ReturnCode.OK, ReturnCode.OK]],

}

rtps_test_suite_2 = {
    # OWNERSHIP
    # Two Publishers and One Subscriber to test that if each one has a different color, the ownership strength does not matter
    'Test_Ownership_3': [['-P -t Square -s 3 -c BLUE -w -x 2', '-P -t Square -s 4 -c RED -w -x 2', '-S -t Square -s 2 -r -k 0 -x 2'],
                         [ReturnCode.OK, ReturnCode.OK, ReturnCode.RECEIVING_FROM_BOTH], test_ownership3_4],
    # Two Publishers and One Subscriber to test that the Subscriber only receives samples from the Publisher with the greatest ownership
    'Test_Ownership_4': [['-P -t Square -s 5 -r -k 0 -w -x 2', '-P -t Square -s 4 -r -k 0 -w -x 2', '-S -t Square -s 2 -r -k 0 -x 2'],
                         [ReturnCode.OK, ReturnCode.OK, ReturnCode.RECEIVING_FROM_ONE], test_ownership3_4],
}
