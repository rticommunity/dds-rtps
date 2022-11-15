#!/usr/bin/python

from multiprocessing import Process, Queue, Value, Array
import tempfile

import time
import re
import pexpect
import multiprocessing 
import argparse
import os

from junitparser import TestCase, TestSuite, JUnitXml, Skipped, Error
from datetime import date

from qos import dict_param_expected_code_timeout, ErrorCode, names


def subscriber(name_executable, parameters, key, time_out, code, 
                subscriber_finished, publisher_finished):
    """ Run the executable with the parameters and save the error code obtained

        name_executable : name of the executable to run as a Subscriber
        parameters : QOS to use
        key : test is being tested (from dict_param_expected_code_timeout)
        time_out : time pexpect waits until it finds a pattern
        code : this variable will be overwritten with the obtained ErrorCode
        subscriber_finished : object event from multiprocessing that is set
            when the subscriber is finished
        publisher_finished : object event from multiprocessing that is set
            when the publisher is finished

        The function runs the executable with the Qos as a Subscriber.
        It follows the next steps until it does not find the pattern 
        and it saves the ErrorCode found:
            * Wait until the topic is created
            * Wait until the reader is created
            * Wait until the reader matches with a writer
            * Wait until the reader detects the writer as alive
            * Wait until the reader receives data

        If at a each point the step is not achieved successfully, 
        the function stops and the ErrorCode is saved.
    
    """

    # Step 1 : run the executable
    child_sub = pexpect.spawn('%s %s' % (name_executable, parameters))

    # Save the output of the child in the file created
    msg_sub_verbose = open('log_sub.txt', 'w') 
    #msg_sub_verbose = tempfile.TemporaryFile()
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
                         
    subscriber_finished.set() 
    publisher_finished.wait()   # wait for publisher to finish
    return


def publisher(name_executable, parameters, time_out, code, id_pub, 
                subscriber_finished, publisher_finished):
    """ Run the executable with the parameters and save the error code obtained

        name_executable : name of the executable to run as a Publisher
        parameters : QOS to use
        time_out : time pexpect waits until it finds a pattern
        code : this variable will be overwritten with the obtained ErrorCode
        id_pub : id of the Publisher (1 or 2)
        subscriber_finished : object event from multiprocessing that is set
            when the subscriber is finished
        publisher_finished : object event from multiprocessing that is set
            when the publisher is finished

        The function runs the executable with the Qos as a Publisher.
        It follows the next steps until it does not find the pattern 
        and it saves the ErrorCode found:
            * Wait until the topic is created
            * Wait until the writer is created
            * Wait until the writer matches with a reader
            * Wait until the writer sends data

        If at a each point the step is not achieved successfully, 
        the function stops and the ErrorCode is saved.
    
    """
    
    # Step 1 : run the executable
    child_pub = pexpect.spawn('%s %s'% (name_executable, parameters))

    # Save the output of the child in the file created
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
            
    subscriber_finished.wait() # wait for subscriber to finish
    publisher_finished.set()                
    return


def run_test(name_pub, name_sub, key, param_pub, param_sub, 
                expected_code_pub, expected_code_sub, verbose, case,
                time_out=20):
    """ Run the Publisher and the Subscriber and check the ErrorCode

        name_pub : name of the executable to run as a Publisher
        name_sub : name of the executable to run as a Subscriber
        key : test is being tested (from dict_param_expected_code_timeout)
        param_pub : qos for the Publisher
        param_sub : qos for the Subscriber
        expected_code_pub : ErrorCode the Publisher will obtain in a non error 
                            situation
        expected_code_sub : ErrorCode the Subscriber will obtain in a non error
                            situation
        verbose : boolean. True means the output of the Publisher and Subscriber 
                will be shown on the console if there is an error.
        time_out : timeout for pexpect. Optional, default value = 20.

        The function runs in two different Processes
        the Publisher and the Subscriber. 
        Then it checks that the code obtained is the one
        we expected.
    """
    manager = multiprocessing.Manager()
    code = manager.list(range(2)) # used for storing the obtained ErrorCode (from Publisher and Subscriber)

    subscriber_finished = multiprocessing.Event()
    publisher_finished = multiprocessing.Event()

    pub = Process(target=publisher, 
                    args=[name_pub, param_pub, time_out, code, 1, 
                          subscriber_finished, publisher_finished])
    sub = Process(target=subscriber, 
                    args=[name_sub, param_sub, key, time_out, code,
                          subscriber_finished, publisher_finished])
    sub.start()
    pub.start()
    sub.join()
    pub.join()

    # temporal files
    msg_pub_verbose = open('log_pub_1.txt', 'r')
    msg_sub_verbose = open('log_sub.txt', 'r')

    if expected_code_pub ==  code[1] and expected_code_sub == code[0]:
        print ('%s : Ok' %key)
        case.result = [('OK')]
    else:
        print('Error in : %s' % (key))
        print('Pub expected code: %s; Code found: %s' % (expected_code_pub, code[1]))
        print('Sub expected code: %s; Code found: %s' % (expected_code_sub, code[0]))
        if verbose:
            if expected_code_pub !=  code[1]:
                print('#############################################################')
                print('Information about the Publisher:')
                print('%s' % msg_pub_verbose.read()) # read only 500 characters because the output of the Publisher is too long
                print('#############################################################')
            if expected_code_sub !=  code[0]:
                print('#############################################################')
                print('Information about the Subscriber:')
                print('%s' % msg_sub_verbose.read())
                print('#############################################################')      
        
        additional_info_pub = msg_pub_verbose.read().replace('\n', '<br>')        
        additional_info_sub = msg_sub_verbose.read().replace('\n', '<br>')   
        case.result = [Error('<strong> Publisher expected code </strong> %s ; <strong> Code found: </strong>  %s  <br> \
                             <strong> Sub expected code: </strong>  %s; <strong> Code found: </strong>  %s <br> \
                             <strong> Information Publisher: </strong>  <br> %s \
                             <strong> Information Subscriber: </strong>  <br> %s' % 
                             (expected_code_pub, code[1],
                             expected_code_sub, code[0], additional_info_pub, additional_info_sub ))
                      ]

       
        #case.result = [Error(f'Publisher expected code {expected_code_pub} ; Code found: {code[1]}  \
         #                    Sub expected code: {expected_code_sub}; Code found: {code[0]} )]
    
    
    # Delete the temporal files
    os.remove('log_pub_1.txt')
    os.remove('log_sub.txt')
    #mirar ficheros temporales

def run_test_pub_pub_sub(name_pub, name_sub, key, param_pub1, param_pub2, param_sub,
                         expected_code_pub1, expected_code_pub2, expected_code_sub, 
                         verbose, case, time_out):
    """ Run two Publisher and one Subscriber and check the ErrorCode

        name_pub : name of the executable to run as a Publisher
        name_sub : name of the executable to run as a Subscriber
        key : test that is being tested (from dict_param_expected_code_timeout)
        param_pub1 : qos for the Publisher 1
        param_pub2 : qos for the Publisher 2
        param_sub : qos for the Subscriber
        expected_code_pub1 : ErrorCode the Publisher 1 will obtain in a non error 
                            situation
        expected_code_pub2 : ErrorCode the Publisher 2 will obtain in a non error 
                            situation
        expected_code_sub : ErrorCode the Subscriber will obtain in a non error
                            situation
        verbose : boolean. True means the output of the Publisher and Subscriber 
                will be shown on the console if there is an error.
        time_out : timeout for pexpect. Optional, default value = 20.

        The function runs in three different Processes
        the first Publisher, the second Publisher and the Subscriber. 
        Then it checks that the code obtained is the one
        we expected.
    """
    manager = multiprocessing.Manager()
    code = manager.list(range(3)) # used for storing the obtained ErrorCode (from Publisher 1, Publisher 2 and Subscriber)

    subscriber_finished = multiprocessing.Event()
    publisher_finished = multiprocessing.Event()


    if key == 'Test_Ownership_3':
        pub1 = Process(target=publisher, 
                        args=[name_pub, param_pub1, time_out, code, 1, 
                              subscriber_finished, publisher_finished])
        pub2 = Process(target=publisher, 
                        args=[name_pub, param_pub2, time_out, code, 2, 
                              subscriber_finished, publisher_finished])                
        sub = Process(target=subscriber, 
                        args=[name_sub, param_sub, key, time_out, code, 
                              subscriber_finished, publisher_finished])

    sub.start()
    pub1.start()
    time.sleep(1) # used to simulate the manual execution. In the case where the ownership strength is being tested
                  # if the second Publisher starts first we could receive samples from it, but it means that 
                  # the first Publisher is not created yet, not that the strength of the second is bigger
    pub2.start()
    
    
    sub.join()
    pub1.join()
    pub2.join()

    # temporal files
    msg_pub1_verbose = open('log_pub_1.txt', 'r')
    msg_pub2_verbose = open('log_pub_2.txt', 'r')
    msg_sub_verbose = open('log_sub.txt', 'r')

    if expected_code_pub1 ==  code[1] and expected_code_sub == code[0] \
        and expected_code_pub2 == code[2]:
        print ('%s : Ok' %key)
        case.result = [('OK')]
    else:
        print('Error in : %s' % (key))
        print('Pub_1 expected code: %s; Code found: %s' % (expected_code_pub1, code[1]))
        print('Pub_2 expected code: %s; Code found: %s' % (expected_code_pub2, code[2]))
        print('Sub expected code: %s; Code found: %s' % (expected_code_sub, code[0]))
        if verbose:
            if expected_code_pub1 !=  code[1]:
                print('#############################################################')
                print('Information about the Publisher 1:')
                print('%s' % msg_pub1_verbose.read()) # read only 500 characters because the output of the Publisher is too long
                print('#############################################################')
            if expected_code_pub2 !=  code[2]:
                print('#############################################################')
                print('Information about the Publisher 2:')
                print('%s' % msg_pub2_verbose.read()) # read only 500 characters because the output of the Publisher is too long
                print('#############################################################')
            if expected_code_sub !=  code[0]:
                print('#############################################################')
                print('Information about the Subscriber:')
                print('%s' % msg_sub_verbose.read())
                print('#############################################################')
        additional_info_pub1 = msg_pub1_verbose.read().replace('\n', '<br>')      
        additional_info_pub2 = msg_pub2_verbose.read().replace('\n', '<br>')  
        additional_info_sub = msg_sub_verbose.read().replace('\n', '<br>')  

        case.result = [Error('<strong> Publisher 1 expected code </strong> %s ; <strong> Code found: </strong> %s <br> \
                              <strong> Publisher 2 expected code </strong> %s : <strong> Code found </strong> %s <br> \
                              <strong> Sub expected code: </strong> %s; <strong> Code found: </strong>%s <br>\
                              <strong> Information Publisher 1: </strong>  <br> %s \
                              <strong> Information Publisher 2: </strong>  <br> %s \
                              <strong> Information Subscriber: </strong>  <br> %s' % 
                             (expected_code_pub1, code[1],
                             expected_code_pub2, code[2],
                             expected_code_sub, code[0],
                             additional_info_pub1,
                             additional_info_pub2,
                             additional_info_sub)
                          )
                      ]

    # Delete the temporal files
    os.remove('log_pub_1.txt')
    os.remove('log_pub_2.txt')
    os.remove('log_sub.txt')

def main():
    today = date.today()
    #d4 = today.strftime("%b-%d-%Y")
    d4 = today.strftime('%Y%m%d-%H:%M:%S')

    parser = argparse.ArgumentParser(description='Interoperability test.')
    parser.add_argument('-P', 
                choices=['connext6.1.1', 'opendds', 'connext5.2.3'],
                default=None,
                required=True,
                type=str, 
                help='Path of the publisher')
    parser.add_argument('-S', 
                choices=['connext6.1.1', 'opendds', 'connext5.2.3'],
                default=None,
                required=True,
                type=str, 
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
                default='default', 
                help="Output format.")


    args = parser.parse_args()


    if args.output == 'default':
        args.output = args.P+'-'+args.S+'-'+d4+'.xml'
        xml = JUnitXml()
    else:
        xml = JUnitXml.fromfile(args.output)
    #xml = JUnitXml.fromfile('./junit.xml')
    
    suite = TestSuite('%s---%s' %(args.P,args.S))

    for k, v in dict_param_expected_code_timeout.items():
        
        case = TestCase('%s' %k)
        if k ==  'Test_Ownership_3':
            run_test_pub_pub_sub(names[args.P], names[args.S], k,v[0], v[1], v[2],
                                 v[3], v[4], v[5], args.verbose, case, v[6])
        else:
            run_test(names[args.P], names[args.S], k,v[0], v[1], v[2], v[3], 
                           args.verbose, case, v[4])
        
        suite.add_testcase(case)


    xml.add_testsuite(suite)   
 
    xml.write(args.output)

    # jv = require('junit-viewer')
    # parsedData = jv.parse(args.output)
    # renderedData = jv.render(parsedData)
    # parsedAndRenderData = jv.unit_viewer(args.output)
    
    
if __name__ == '__main__':
    main()