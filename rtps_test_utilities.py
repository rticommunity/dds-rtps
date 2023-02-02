from enum import Enum
import re
import pexpect
class ReturnCode(Enum):
    """"
    Codes to give information about Shape Applications' behavior.

    OK                   : Publisher/Subscriber sent/received data correctly
    UNRECOGNIZED_VALUE   : Parameters for the Publisher/Subscriber not supported
    TOPIC_NOT_CREATED    : Publisher/Subscriber does not create the topic
    READER_NOT_CREATED   : Subscriber does not create the Data Reader
    WRITER_NOT_CREATED   : Publisher does not create the Data Writer
    FILTER_NOT_CREATED   : Subscriber does not create the content filter
    INCOMPATIBLE_QOS     : Publisher/Subscriber with incompatible QoS.
    READER_NOT_MATCHED   : Publisher does not find any compatible Data Reader
    WRITER_NOT_MATCHED   : Subscriber does not find any compatible Data Writer
    WRITER_NOT_ALIVE     : Subscriber does not find any live Data Writer
    DATA_NOT_RECEIVED    : Subscriber does not receive the data
    DATA_NOT_SENT        : Publisher does not send the data
    DATA_NOT_CORRECT     : Subscriber does not find the data expected
    RECEIVING_FROM_ONE   : Subscriber receives from one Publisher
    RECEIVING_FROM_BOTH  : Subscriber receives from two Publishers
    """
    OK = 0
    UNRECOGNIZED_VALUE = 1
    TOPIC_NOT_CREATED = 2
    READER_NOT_CREATED = 3
    WRITER_NOT_CREATED = 4
    FILTER_NOT_CREATED = 5
    INCOMPATIBLE_QOS = 6
    READER_NOT_MATCHED = 7
    WRITER_NOT_MATCHED = 8
    WRITER_NOT_ALIVE = 9
    DATA_NOT_RECEIVED = 10
    DATA_NOT_SENT = 11
    DATA_NOT_CORRECT = 12
    RECEIVING_FROM_ONE = 13
    RECEIVING_FROM_BOTH = 14

def log_message(message, verbosity):
    if verbosity:
        print(message)

#test_ownership3-4 explain what is doing
def check_receiving_from(child_sub, samples_sent, timeout, verbosity):
    first_received_first_time = False
    second_received_first_time = False
    first_received = False
    second_received = False
    list_data_received_second = []
    for x in range(0,80,1): #variable instead of 80
        sub_string = re.search('[0-9]{3} [0-9]{3}',
            child_sub.before)
        try:
            list_data_received_second.append(samples_sent[1].get(True, 5)) #timeout instead of 5
        except:
            break;
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

def check_reliability(child_sub, samples_sent, timeout, verbosity):
    for x in range(0, 3, 1):
        sub_string = re.search('[0-9]{3} [0-9]{3}', child_sub.before)
        if samples_sent[0].get(True,5) == sub_string.group(0):
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

def no_check(child_sub, samples_sent, timeout, verbosity):
    return ReturnCode.OK