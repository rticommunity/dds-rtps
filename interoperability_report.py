#!/usr/bin/python

from ctypes import c_char_p

from multiprocessing import Process, Queue, Value, Array
from operator import truediv


import time
import re
import pexpect
import sys
import multiprocessing 
import numpy as np
import argparse
import os

from qos import dict_param_expected_code_timeout, ErrorCode, names


def subscriber(name_executable, parameters, key, time_out, code, data, event, event2):
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
    child_sub = pexpect.spawn('%s %s' % (name_executable, parameters))
    msg_sub_verbose = open('log_sub.txt', 'w')
    child_sub.logfile = msg_sub_verbose
    
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
        #msg_sub_verbose.put(child_sub.before + str(child_sub.after))
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
            #msg_sub_verbose.put(child_sub.before + str(child_sub.after))
        elif index == 2:
            code[0] = ErrorCode.FILTER_NOT_CREATED
            #msg_sub_verbose.put(child_sub.before + str(child_sub.after))
        
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
                #msg_sub_verbose.put(child_sub.before + str(child_sub.after))
            elif index == 2:
                code[0] = ErrorCode.INCOMPATIBLE_QOS
                #msg_sub_verbose.put(child_sub.before + str(child_sub.after))
                
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
                    #msg_sub_verbose.put(child_sub.before + str(child_sub.after))
                
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
                                    #msg_sub_verbose.put(child_sub.before + str(child_sub.after))
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
                            #msg_sub_verbose.put(child_sub.before + str(child_sub.after))
                           
                    elif index == 1:
                        code[0] = ErrorCode.DATA_NOT_RECEIVED
                        #msg_sub_verbose.put(child_sub.before + str(child_sub.after))
                         
    event.set()
    event2.wait()   
    return


def publisher(name_executable, parameters, key, time_out, code, data, id_pub, event, event2):
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
    child_pub = pexpect.spawn('%s %s'% (name_executable, parameters))
    file = 'log_pub_'+str(id_pub)+'.txt'
    msg_pub_verbose = open(file, 'w')
    child_pub.logfile = msg_pub_verbose
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
        #msg_pub_verbose.put(child_pub.before + str(child_pub.after))
    elif index == 3:
        code[id_pub] = ErrorCode.UNRECOGNIZED_VALUE
        #msg_pub_verbose.put(child_pub.before + str(child_pub.after))
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
            #msg_pub_verbose.put(child_pub.before + str(child_pub.after))
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
                #msg_pub_verbose.put(child_pub.before + str(child_pub.after))
            elif index == 2:
                code[id_pub] = ErrorCode.INCOMPATIBLE_QOS
                #msg_pub_verbose.put(child_pub.before + str(child_pub.after))
            elif index == 0:
                code[id_pub] = ErrorCode.OK
                #msg_pub_verbose.put(child_pub.before + str(child_pub.after))
            
    event.wait()
    event2.set()                
    return


def run_test(name_pub, name_sub, key, param_pub, param_sub, 
                expected_code_pub, expected_code_sub, verbose,
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
    event2 = multiprocessing.Event()

    pub = Process(target=publisher, 
                    args=[name_pub, param_pub, key, time_out, code, data,1, event, event2])
    sub = Process(target=subscriber, 
                    args=[name_sub, param_sub, key, time_out, code, data, event, event2])
    sub.start()
    pub.start()
    sub.join()
    pub.join()

    msg_pub_verbose = open('log_pub_1.txt', 'r')
    msg_sub_verbose = open('log_sub.txt', 'r')

    if expected_code_pub ==  code[1] and expected_code_sub == code[0]:
        print ('%s : Ok' %key)
    else:
        print('Error in : %s' % (key))
        print('Pub expected code: %s; Code found: %s' % (expected_code_pub, code[1]))
        print('Sub expected code: %s; Code found: %s' % (expected_code_sub, code[0]))
        if verbose:
            if expected_code_pub !=  code[1]:
                print('####################################################################################')
                print('Information about the Publisher:')
                print('%s' % msg_pub_verbose.read(500))
                print('####################################################################################')
            if expected_code_sub !=  code[0]:
                print('####################################################################################')
                print('Information about the Subscriber:')
                print('%s' % msg_sub_verbose.read())
                print('####################################################################################')
    
    os.remove('log_pub_1.txt')
    os.remove('log_sub.txt')

def run_test_pub_pub_sub(name_pub, name_sub, key, param_pub1, param_pub2, param_sub, expected_code_pub1, 
                        expected_code_pub2, expected_code_sub, verbose, time_out):
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
    event2 = multiprocessing.Event()


    if key == 'Test_Ownership_3':
        pub1 = Process(target=publisher, 
                        args=[name_pub, param_pub1, key, time_out, code, data,
                        1, event, event2])
        pub2 = Process(target=publisher, 
                        args=[name_pub, param_pub2, key, time_out, code, data,
                        2, event, event2])                
        sub = Process(target=subscriber, 
                        args=[name_sub, param_sub, key, time_out, code, data, event, event2])
    
    #msg_pub_verbose = open('log_pub.txt', 'r')
    #msg_sub_verbose = open('log_sub.txt', 'r')

    sub.start()
    pub1.start()
    time.sleep(1)
    pub2.start()
    
    
    sub.join()
    pub1.join()
    pub2.join()

    msg_pub1_verbose = open('log_pub_1.txt', 'r')
    msg_pub2_verbose = open('log_pub_2.txt', 'r')
    msg_sub_verbose = open('log_sub.txt', 'r')

    if expected_code_pub1 ==  code[1] and expected_code_sub == code[0] \
        and expected_code_pub2 == code[2]:
        print ('%s : Ok' %key)
    else:
        print('Error in : %s' % (key))
        print('Pub_1 expected code: %s; Code found: %s' % (expected_code_pub1, code[1]))
        print('Pub_2 expected code: %s; Code found: %s' % (expected_code_pub2, code[2]))
        print('Sub expected code: %s; Code found: %s' % (expected_code_sub, code[0]))
        if verbose:
            if expected_code_pub1 !=  code[1]:
                print('####################################################################################')
                print('Information about the Publisher 1:')
                print('%s' % msg_pub1_verbose.read(500))
                print('####################################################################################')
            if expected_code_pub2 !=  code[2]:
                print('####################################################################################')
                print('Information about the Publisher 2:')
                print('%s' % msg_pub2_verbose.read(500))
                print('####################################################################################')
            if expected_code_sub !=  code[0]:
                print('####################################################################################')
                print('Information about the Subscriber:')
                print('%s' % msg_sub_verbose.read())
                print('####################################################################################')

    os.remove('log_pub_1.txt')
    os.remove('log_pub_2.txt')
    os.remove('log_sub.txt')

def main():
    parser = argparse.ArgumentParser(description='Interoperability test.')
    parser.add_argument('-P', 
                metavar='publisher_name', #cambiar a que tambien se pueda llamar asi con --
                choices=['connext6.1.1', 'opendds', 'connext5.2.3'],
                default=None,
                required=True,
                type=str, # Celia : is it okey?
                help='Path of the publisher')
    parser.add_argument('-S', #cambiar a que tambien se pueda llamar asi con --
                metavar='subscriber_name',
                choices=['connext6.1.1', 'opendds', 'connext5.2.3'],
                default=None,
                required=True,
                type=str, # Celia : is it okey?
                help='Path of the subscriber')
    parser.add_argument("-v","--verbose",
                action="store_true",
                default=False,
                help="Print more information to stdout.")
    parser.add_argument("-f", "--output-format",
                choices=['junit', 'csv', 'xlxs'],
                type=str,
                default='junit',
                help="Output format.")
    parser.add_argument("-o", "--output",
                metavar='filename',
                type=str,
                default='report', #celia : change this #if this contain an extension this should be the extension of the file, and -f should be empty
                                    #add_mutually_exclusive_group(required=False)
                help="Output format.")
    args = parser.parse_args()

    for k, v in dict_param_expected_code_timeout.items():
        # celia : change this so time_out can be optional
        if k ==  'Test_Ownership_3':
            run_test_pub_pub_sub(names[args.P], names[args.S], k,v[0], v[1], v[2], v[3], v[4], v[5], args.verbose, v[6])
        else:
            run_test(names[args.P], names[args.S], k,v[0], v[1], v[2], v[3], args.verbose, v[4])

    
if __name__ == '__main__':
    main()