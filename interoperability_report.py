#!/usr/bin/python

from ctypes import c_char_p
from enum import Enum
from multiprocessing import Process, Queue, Value, Array
from operator import truediv

import time
import re
import pexpect
import sys
import multiprocessing 
import numpy as np

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

class QOS(Enum):
    DOMAIN = 0
    RELIABILITY = 1
    HISTORY = 2
    DEADLINE = 3
    OWNERSHIP = 4
    TOPIC = 5
    COLOR = 6
    PARTITION = 7
    DURABILITY = 8

QOS = Enum('QOS',
        [
            'DOMAIN', 'RELIABILITY', 'HISTORY', 'DEADLINE', 
            'OWNERSHIP', 'TOPIC', 'COLOR', 'PARTITION', 'DURABILITY'
        ])


def subscriber(name_executable, parameters, key, time_out, code, data, event):
    """ Run the executable with the parameters and save the error code obtained

        name_executable : name of the executable to run as a Subscriber
        parameters : QOS to use
        time_out : time pexpect will wait until it finds a pattern
        code : this variable will be overwritten with the obtained ErrorCode
        data : this variable will be overwritten with the obtained data
            (only uses if we have compiled with the new shape_main.cxx)
        event : object event from multiprocessing 
        key : test we are testing

        The function will run the executable with the Qos as a Subscriber.
        It will follow the next steps until it does not find the pattern 
        and it will save the ErrorCode found:
            * Wait until the topic is created
            * Wait until the reader is created
            * Wait until the reader matches with a writer
            * Wait until the reader detects the writer as alive
            * Wait until the reader receives data

        If at a each point the step is not achieved successfully, 
        the function will stop and the ErrorCode will be saved.
    
    """

    # Step 1 : run the executable
    child_sub = pexpect.spawn('%s -S %s' % (name_executable, parameters))

    # Step 2 : Check if the topic is created
    index = child_sub.expect(
        [
            'Create topic:', 
            pexpect.TIMEOUT, 
            'please specify topic name', 
            'unrecognized value'
        ],
        time_out
    )
    if index == 1 or index == 2:
        code[0] = ErrorCode.TOPIC_NOT_CREATED
    elif index == 3:
        code[0] = ErrorCode.UNRECOGNIZED_VALUE
   
    elif index == 0:
        # Step 3 : Check if the reader is created
        index = child_sub.expect(
            [
                'Create reader for topic:',
                pexpect.TIMEOUT,
                'failed to create content filtered topic'
            ], 
            time_out
        )
        if index == 1:
            code[0] = ErrorCode.READER_NOT_CREATED
        elif index == 2:
            code[0] = ErrorCode.FILTER_NOT_CREATED
        
        elif index == 0:
            # Step 4 : Check if the reader matches the writer
            index = child_sub.expect(
                [
                    'on_subscription_matched()', 
                    pexpect.TIMEOUT, 
                    'on_requested_incompatible_qos()'
                ], 
                time_out
            )
            if index == 1:
                code[0] = ErrorCode.WRITER_NOT_MATCHED
            elif index == 2:
                code[0] = ErrorCode.INCOMPATIBLE_QOS
                
            elif index == 0:
                # Step 5: Check if the reader detects the writer as alive 
                index = child_sub.expect(
                    [
                        'on_liveliness_changed()', 
                        pexpect.TIMEOUT
                    ], 
                    time_out
                )
                if index == 1:
                    code[0] = ErrorCode.WRITER_NOT_ALIVE 
                
                elif index == 0:
                    #Step 6 : Check if the reader receives the samples
                    index = child_sub.expect(
                            [
                                '\[20\]', 
                                pexpect.TIMEOUT
                            ], 
                            time_out
                        )
                    if index == 0:
                        
                        if key == 'Test_Ownership_3':
                            red_received = False
                            blue_received = False
                            code[0] = ErrorCode.RECEIVING_FROM_ONE
                            for x in range(0,100,1):
                                sub_string_red = re.search('RED', child_sub.before)
                                sub_string_blue = re.search('BLUE', child_sub.before)
                            
                                if sub_string_red != None:
                                    red_received = True
                            
                                if sub_string_blue != None:
                                    blue_received = True

                                if blue_received and red_received:
                                    code[0] = ErrorCode.RECEIVING_FROM_BOTH
                                    break
                                child_sub.expect(
                                            [
                                            '\[20\]', 
                                            pexpect.TIMEOUT
                                            ], 
                                            time_out
                                )                               
                                
                        else:
                            code[0] = ErrorCode.OK
                           
                    elif index == 1:
                        code[0] = ErrorCode.DATA_NOT_RECEIVED
                         
    event.set()   
    return


def publisher(name_executable, parameters, key, time_out, code, data, id_pub, event):
    """ Run the executable with the parameters and save the error code obtained

        name_executable : name of the executable to run as a Publisher
        parameters : QOS to use
        time_out : time pexpect will wait until it finds a pattern
        code : this variable will be overwritten with the obtained ErrorCode
        data : this variable will be overwritten with the obtained data
            (only uses if we have compiled with the new shape_main.cxx)
        event : object event from multiprocessing 
        key : test we are testing

        The function will run the executable with the Qos as a Publisher.
        It will follow the next steps until it does not find the pattern 
        and it will save the ErrorCode found:
            * Wait until the topic is created
            * Wait until the writer is created
            * Wait until the writer matches with a reader
            * Wait until the writer sends data

        If at a each point the step is not achieved successfully, 
        the function will stop and the ErrorCode will be saved.
    
    """
    
    # Step 1 : run the executable
    child_pub = pexpect.spawn('%s -P %s'% (name_executable, parameters))

    # Step 2 : Check if the topic is created
    index = child_pub.expect(
        [
            'Create topic:', 
            pexpect.TIMEOUT, 
            'please specify topic name', 
            'unrecognized value'
        ], 
        time_out
    )
    if index == 1 or index == 2:
        code[id_pub] = ErrorCode.TOPIC_NOT_CREATED
    elif index == 3:
        code[id_pub] = ErrorCode.UNRECOGNIZED_VALUE
    
    elif index == 0:
        # Step 3 : Check if the writer is created
        index = child_pub.expect(
            [
                'Create writer for topic', 
                pexpect.TIMEOUT
            ], 
            time_out 
        )
        if index == 1:
            code[id_pub] = ErrorCode.WRITER_NOT_CREATED
            
        elif index == 0:
            # Step 4 : Check if the writer matches the reader
            index = child_pub.expect(
                [
                    'on_publication_matched()',
                    pexpect.TIMEOUT,
                    'on_offered_incompatible_qos'
                ], 
                time_out
            )
            if index == 1:      
                code[id_pub] = ErrorCode.READER_NOT_MATCHED
            elif index == 2:
                code[id_pub] = ErrorCode.INCOMPATIBLE_QOS
            elif index == 0:
                code[id_pub] = ErrorCode.OK
            
    event.wait()                
    return


def run_test(key, param_pub, param_sub, 
                expected_code_pub, expected_code_sub, 
                time_out=20):
    """ Run the Publisher and the Subscriber and check the ErrorCode

        expected_code_pub : ErrorCode the Publisher will obtain if 
                        everything goes as expected
        expected_code_sub : ErrorCode the Subscriber will obtain if 
                        everything goes as expected
        param_pub : qos for the Publisher
        param_sub : qos for the Subscriber
        time_out : timeout for pexpect # should be optional
        key : test we are testing

        The function will run in two different Processes
        the Publisher and the Subscriber. 
        Then it will check that the code obtained is the one
        we expected.
    """
    #name_executable = # /home/carias/shape_main/opendds3.21_shape_main_linux
    name_executable = '/home/carias/shape_main/dds-rtps/srcCxx/objs/x64Linux4gcc7.3.0/rti_connext_dds-6.1.1_shape_main_linux '
    manager = multiprocessing.Manager()
    code = manager.list(range(2))
    data = Queue()
    event = multiprocessing.Event()
    
    pub = Process(target=publisher, 
                    args=[name_executable, param_pub, key, time_out, code, data,1, event])
    sub = Process(target=subscriber, 
                    args=[name_executable, param_sub, key, time_out, code, data, event])
    sub.start()
    pub.start()
    sub.join()
    pub.join()

    if expected_code_pub ==  code[1] and expected_code_sub == code[0]:
        print ('%s : Ok' %key)
    else:
        print('Error in : %s' % (key))
        print('Pub expected code: %s; Code found: %s' % (expected_code_pub, code[1]))
        print('Sub expected code: %s; Code found: %s' % (expected_code_sub, code[0]))
    



def run_test_pub_pub_sub(key, param_pub1, param_pub2, param_sub, expected_code_pub1, 
                        expected_code_pub2, expected_code_sub, time_out):
    """ Run two Publisher and one Subscriber and check the ErrorCode

        expected_code_pub : ErrorCode the Publisher will obtain if 
                        everything goes as expected
        expected_code_sub : ErrorCode the Subscriber will obtain if 
                        everything goes as expected
        param_pub : qos for the Publisher
        param_sub : qos for the Subscriber
        time_out : timeout for pexpect # should be optional
        key : test we are testing

        The function will run in two different Processes
        the Publisher and the Subscriber. 
        Then it will check that the code obtained is the one
        we expected.
    """

    name_executable = '/home/carias/shape_main/dds-rtps/srcCxx/objs/x64Linux4gcc7.3.0/rti_connext_dds-6.1.1_shape_main_linux '
    manager = multiprocessing.Manager()
    code = manager.list(range(3))
    data = Queue()
    event = multiprocessing.Event()
   
    if key == 'Test_Ownership_3':
        pub1 = Process(target=publisher, 
                        args=[name_executable, param_pub1, key, time_out, code, data,
                        1, event])
        pub2 = Process(target=publisher, 
                        args=[name_executable, param_pub2, key, time_out, code, data,
                        2, event])                
        sub = Process(target=subscriber, 
                        args=[name_executable, param_sub, key, time_out, code, data, event])

    sub.start()
    pub1.start()
    time.sleep(1)
    pub2.start()
    
    
    sub.join()
    pub1.join()
    pub2.join()

    if expected_code_pub1 ==  code[1] and expected_code_sub == code[0] \
        and expected_code_pub2 == code[2]:
        print ('%s : Ok' %key)
    else:
        print('Error in : %s' % (key))
        print('Pub_1 expected code: %s; Code found: %s' % (expected_code_pub1, code[1]))
        print('Pub_2 expected code: %s; Code found: %s' % (expected_code_pub2, code[2]))
        print('Sub expected code: %s; Code found: %s' % (expected_code_sub, code[0]))


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

def main():
    for k, v in dict_param_expected_code_timeout.items():
        # celia : change this so time_out can be optional
        if k ==  'Test_Ownership_3':
            run_test_pub_pub_sub(k,v[0], v[1], v[2], v[3], v[4], v[5], v[6])
        else:
            run_test(k,v[0], v[1], v[2], v[3], v[4])

    
if __name__ == '__main__':
    main()