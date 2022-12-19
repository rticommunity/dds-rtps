#!/usr/bin/python

from multiprocessing import Process, Queue
import time
import re
import pexpect
import multiprocessing
import argparse 
import os
from junitparser import TestCase, TestSuite, JUnitXml, Error, Attr
from datetime import datetime

from utilities import ReturnCode, path_executables
from testSuite import dict_param_expected_code_timeout


def subscriber(name_executable, parameters, key, time_out, code, data,
                subscriber_finished, publisher_finished):
    """ Run the executable with the parameters and save 
        the error code obtained

        name_executable     : name of the ShapeApplication to run
                              as a Subscriber
        parameters          : QOS to use with the Shape Application
        key                 : test is being tested 
                             (from dict_param_expected_code_timeout)
        time_out            : time pexpect waits until it finds a pattern
        code                : this variable will be overwritten with 
                              the obtained ReturnCode
        data                : this variable contains the samples 
                              the Publisher sends
        subscriber_finished : object event from multiprocessing that is set
                              when the subscriber is finished
        publisher_finished  : object event from multiprocessing that is set
                              when the publisher is finished

        The function runs the Shape Application as a Subscriber 
        with the QoS defined.
        It follows the next steps: 
            * Wait until the topic is created
            * Wait until the reader is created
            * Wait until the reader matches with a writer
            * Wait until the reader detects the writer as alive
            * Wait until the reader receives data
    
    """
    
    # Step 1 : run the executable
    child_sub = pexpect.spawnu(f'{name_executable} {parameters}')

    # Save the child's output in the file created
    msg_sub_verbose = open('log_sub.txt', 'w') 
    child_sub.logfile = msg_sub_verbose
   
    # Step 2 : Check if the topic is created
    index = child_sub.expect(
        [
            'Create topic:', 
            pexpect.TIMEOUT, 
            'please specify topic name', 
            'unrecognized value',
            pexpect.EOF
        ],
        time_out
    )

    if index == 1 or index == 2 or index == 4:
        code[0] = ReturnCode.TOPIC_NOT_CREATED
    elif index == 3:
        code[0] = ReturnCode.UNRECOGNIZED_VALUE
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
            code[0] = ReturnCode.READER_NOT_CREATED
        elif index == 2:
            code[0] = ReturnCode.FILTER_NOT_CREATED        
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
                code[0] = ReturnCode.WRITER_NOT_MATCHED
            elif index == 2:
                code[0] = ReturnCode.INCOMPATIBLE_QOS                
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
                    code[0] = ReturnCode.WRITER_NOT_ALIVE 
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
                        
                        if key == 'Test_Reliability_4':
                            for x in range(0, 3, 1):
                                sub_string = re.search('[0-9]{3} [0-9]{3}', 
                                                        child_sub.before)
                                if data.get() == sub_string.group(0):
                                    code[0] = ReturnCode.OK
                                else:
                                    code[0] = ReturnCode.DATA_NOT_CORRECT
                                    break
                                child_sub.expect(
                                            [
                                            '\[20\]', 
                                            pexpect.TIMEOUT
                                            ], 
                                            time_out
                                )
                        elif key == 'Test_Ownership_3':
                            red_received = False
                            blue_received = False
                            code[0] = ReturnCode.RECEIVING_FROM_ONE
                            for x in range(0,100,1):
                                sub_string_red = re.search('RED', 
                                                        child_sub.before)
                                sub_string_blue = re.search('BLUE', 
                                                        child_sub.before)
                            
                                if sub_string_red != None:
                                    red_received = True
                            
                                if sub_string_blue != None:
                                    blue_received = True

                                if blue_received and red_received:
                                    code[0] = ReturnCode.RECEIVING_FROM_BOTH
                                    break
                                child_sub.expect(
                                            [
                                            '\[20\]', 
                                            pexpect.TIMEOUT
                                            ], 
                                            time_out
                                )                               
                        elif key == 'Test_Ownership_4':
                            
                            second_received = False
                            list_data_received_second = []
                            for x in range(0,40,1):
                                sub_string = re.search('[0-9]{3} [0-9]{3}', 
                                                        child_sub.before)
                               
                                try:
                                    list_data_received_second.append(data.get(True, 5))
                                except:
                                    break;
                            
                                if sub_string.group(0) in list_data_received_second:
                                    second_received = True
                                    code[0] = ReturnCode.RECEIVING_FROM_BOTH
                                                       
                                child_sub.expect(
                                            [
                                            '\[20\]', 
                                            pexpect.TIMEOUT
                                            ], 
                                            time_out
                                )
                            
                            if second_received == False:
                                code[0] = ReturnCode.RECEIVING_FROM_ONE        
                        
                        else:
                            code[0] = ReturnCode.OK
                           
                    elif index == 1:
                        code[0] = ReturnCode.DATA_NOT_RECEIVED

                     
    subscriber_finished.set()   # set subscriber as finished
    publisher_finished.wait()   # wait for publisher to finish
    return


def publisher(name_executable, parameters, key, time_out, code, data,
                id_pub, subscriber_finished, publisher_finished):
    """ Run the executable with the parameters and save 
        the error code obtained

        name_executable     : name of the ShapeApplication to run
                              as a Publisher
        parameters          : QOS to use with the Shape Application
        key                 : test is being tested 
                             (from dict_param_expected_code_timeout)
        time_out            : time pexpect waits until it finds a pattern
        code                : this variable will be overwritten with 
                              the obtained ReturnCode
        data                : this variable contains the samples 
                              the Publisher sends
        id_pub              : Publisher's id (1|2)
        subscriber_finished : object event from multiprocessing that is set
                              when the subscriber is finished
        publisher_finished  : object event from multiprocessing that is set
                              when the publisher is finished

        The function runs the Shape Application as a Publisher
        with the QoS defined.
            * Wait until the topic is created
            * Wait until the writer is created
            * Wait until the writer matches with a reader
            * Wait until the writer sends data

        If it finds the pattern it will continue to the next step, 
        if not it will stop and save the corresponding ReturnCode.
    
    """
    
    # Step 1 : run the executable
    child_pub = pexpect.spawnu(f'{name_executable} {parameters}')

    # Save the child's output in the file created
    file = 'log_pub_'+str(id_pub)+'.txt'
    msg_pub_verbose = open(file, 'w')
    child_pub.logfile = msg_pub_verbose

    # Step 2 : Check if the topic is created
    index = child_pub.expect(
        [
            'Create topic:', 
            pexpect.TIMEOUT, 
            'please specify topic name', 
            'unrecognized value',
            pexpect.EOF
        ], 
        time_out
    )
 
    if index == 1 or index == 2 or index == 4:
        code[id_pub] = ReturnCode.TOPIC_NOT_CREATED
    elif index == 3:
        code[id_pub] = ReturnCode.UNRECOGNIZED_VALUE
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
            code[id_pub] = ReturnCode.WRITER_NOT_CREATED
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
                code[id_pub] = ReturnCode.READER_NOT_MATCHED
            elif index == 2:
                code[id_pub] = ReturnCode.INCOMPATIBLE_QOS
            elif index == 0:
                if '-v' in parameters:
                    #Step  5: Check if the writer sends the samples
                    index = child_pub.expect(
                            [
                                '\[20\]', 
                                pexpect.TIMEOUT
                            ], 
                            time_out
                        )
                    if index == 0:
                        code[id_pub] = ReturnCode.OK
                        if key == 'Test_Reliability_4' or key == 'Test_Ownership_4':
                            for x in range(0, 40 ,1):
                                pub_string = re.search('[0-9]{3} [0-9]{3}', 
                                                            child_pub.before )
                                data.put(pub_string.group(0))
                                    
                                child_pub.expect([
                                            '\[20\]', 
                                            pexpect.TIMEOUT
                                                ], 
                                            time_out
                                )
                        
                    elif index == 1:
                        code[id_pub] = ReturnCode.DATA_NOT_SENT
                else:
                    code[id_pub] = ReturnCode.OK
       
    subscriber_finished.wait() # wait for subscriber to finish
    publisher_finished.set()   # set publisher as finished            
    return


def run_test(name_pub, name_sub, key, param_pub, param_sub, 
                expected_code_pub, expected_code_sub, verbose, case,
                time_out):
    """ Run the Publisher and the Subscriber and check the ReturnCode

        name_pub          : name of the Shape Application to run 
                            as a Publisher
        name_sub          : name of the Shape Application to run 
                            as a Subscriber
        key               : test is being tested 
                            (from dict_param_expected_code_timeout)
        param_pub         : QoS for the Publisher
        param_sub         : QoS for the Subscriber
        expected_code_pub : ReturnCode the Publisher would obtain 
                            in a non error situation
        expected_code_sub : ReturnCode the Subscriber would obtain 
                            in a non error situation
        verbose           : boolean. True means the Publisher and Subscriber's 
                            output will be shown on the console if there is 
                            an error.
        case              : testCase
        time_out          : timeout for pexpect. 

        The function runs in two different Processes
        the Publisher and the Subscriber. 
        Then it checks that the code obtained is the one
        we expected.
    """
    manager = multiprocessing.Manager()
     # used for storing the obtained ReturnCode 
     # (from Publisher and Subscriber)
    code = manager.list(range(2))
    data = Queue() # used for storing the samples

    subscriber_finished = multiprocessing.Event()
    publisher_finished = multiprocessing.Event()

    pub = Process(target=publisher, 
                    args=[path_executables[name_pub], param_pub, key, 
                            time_out, code, data, 1, subscriber_finished,
                            publisher_finished])
    sub = Process(target=subscriber, 
                    args=[path_executables[name_sub], param_sub, key, 
                            time_out, code, data, subscriber_finished, 
                            publisher_finished])
    sub.start()
    pub.start()
    sub.join()
    pub.join()

    msg_pub_verbose = open('log_pub_1.txt', 'r')
    msg_sub_verbose = open('log_sub.txt', 'r')
    information_publisher = msg_pub_verbose.read()
    information_subscriber = msg_sub_verbose.read()
    
    TestCase.custom = Attr('Parameters')
    case.custom = (f'\
                        {name_pub} {param_pub} \
                        | {name_sub} {param_sub}'
                      )

    if expected_code_pub ==  code[1] and expected_code_sub == code[0]:
        print (f'{key} : Ok')
        
    else:
        print(f'Error in : {key}')
        print(f'Publisher expected code: {expected_code_pub}; \
                Code found: {code[1]}')
        print(f'Subscriber expected code: {expected_code_sub}; \
                Code found: {code[0]}')
        if verbose:
            if expected_code_pub !=  code[1] or expected_code_sub != code[0]:
                print('\nInformation about the Publisher:')
                print(f'{information_publisher}') 
                print('\nInformation about the Subscriber:')
                print(f'{information_subscriber}\n')
        
        additional_info_pub = information_publisher.replace('\n', '<br>')        
        additional_info_sub = information_subscriber.replace('\n', '<br>')   
        case.result = [Error(f'<strong> Publisher expected code: </strong> {expected_code_pub}; \
                               <strong> Code found: </strong>  {code[1]} <br> \
                               <strong> Subscriber expected code: </strong>  {expected_code_sub}; \
                               <strong> Code found: </strong>  {code[0]} <br> \
                               <strong> Information Publisher: </strong>  <br> {additional_info_pub} <br>\
                               <strong> Information Subscriber: </strong>  <br> {additional_info_sub}' 
                            )
                      ]
    
    
    # Delete the temporal files
    os.remove('log_pub_1.txt')
    os.remove('log_sub.txt')
    

def run_test_pub_pub_sub(name_pub, name_sub, key, param_pub1, param_pub2, param_sub,
                         expected_code_pub1, expected_code_pub2, expected_code_sub, 
                         verbose, case, time_out):
    """ Run two Publisher and one Subscriber and check the ReturnCode

        name_pub           : name of the Shape Application to run 
                             as a Publisher
        name_sub           : name of the Shape Application to run 
                             as a Subscriber
        key                : test that is being tested 
                            (from dict_param_expected_code_timeout)
        param_pub1         : QoS for the Publisher 1
        param_pub2         : QoS for the Publisher 2
        param_sub          : QoS for the Subscriber
        expected_code_pub1 : ReturnCode the Publisher 1 would obtain 
                             in a non error situation
        expected_code_pub2 : ReturnCode the Publisher 2 would obtain 
                             in a non error situation
        expected_code_sub  : ReturnCode the Subscriber would obtain 
                             in a non error situation
        verbose            : boolean. True means the Publisher and Subscriber's 
                             output will be shown on the console if there is 
                             an error.
        time_out           : timeout for pexpect.

        The function runs in three different Processes
        the first Publisher, the second Publisher and the Subscriber. 
        Then it checks that the code obtained is the one
        we expected.
    """
    manager = multiprocessing.Manager()
    # used for storing the obtained ReturnCode 
    # (from Publisher 1, Publisher 2 and Subscriber)
    code = manager.list(range(3)) 
    data = Queue() # used for storing the samples
    subscriber_finished = multiprocessing.Event()
    publisher_finished = multiprocessing.Event()


    if key == 'Test_Ownership_3':
        pub1 = Process(target=publisher, 
                        args=[path_executables[name_pub], param_pub1, key, 
                                time_out, code, data, 1, 
                                subscriber_finished, publisher_finished])
        pub2 = Process(target=publisher, 
                        args=[path_executables[name_pub], param_pub2, key,
                                time_out, code, data, 2, 
                                subscriber_finished, publisher_finished])                
        sub = Process(target=subscriber, 
                        args=[path_executables[name_sub], param_sub, key, 
                                time_out, code, data,
                                subscriber_finished, publisher_finished])
    
    if key == 'Test_Ownership_4':
        pub1 = Process(target=publisher, 
                        args=[path_executables[name_pub], param_pub1, key, 
                                time_out, code, Queue(), 1, 
                                subscriber_finished, publisher_finished])
        pub2 = Process(target=publisher, 
                        args=[path_executables[name_pub], param_pub2, key, 
                                time_out, code, data, 2, 
                                subscriber_finished, publisher_finished])                
        sub = Process(target=subscriber, 
                        args=[path_executables[name_sub], param_sub, key, 
                                time_out, code, data, 
                                subscriber_finished, publisher_finished])

    sub.start()
    pub1.start()
    time.sleep(1) # used to make the two Publishers have different seeds
                  # to generate the samples
    pub2.start()
    
    
    sub.join()
    pub1.join()
    pub2.join()

    # temporal files
    msg_pub1_verbose = open('log_pub_1.txt', 'r')
    msg_pub2_verbose = open('log_pub_2.txt', 'r')
    msg_sub_verbose = open('log_sub.txt', 'r')

    information_publisher1 = msg_pub1_verbose.read()
    information_publisher2 = msg_pub2_verbose.read()
    information_subscriber = msg_sub_verbose.read()

    TestCase.custom = Attr('Parameters')
    case.custom = (f'\
                        {name_pub} {param_pub1} \
                        | {name_pub} {param_pub2} \
                        | {name_sub} {param_sub}'
                      )
    if expected_code_pub1 ==  code[1] and expected_code_sub == code[0] \
        and expected_code_pub2 == code[2]:
        print (f'{key} : Ok')

    else:
        print(f'Error in : {key}')
        print(f'Publisher 1 expected code: {expected_code_pub1}; \
                Code found: {code[1]}')
        print(f'Publisher 2 expected code: {expected_code_pub2}; \
                Code found: {code[2]}')
        print(f'Subscriber expected code: {expected_code_sub}; \
                Code found: {code[0]}')
        if verbose:
            if expected_code_pub1 !=  code[1] or expected_code_pub2 !=  code[2] or expected_code_sub !=  code[0]:
                print('\nInformation about the Publisher 1:')
                print(f'{information_publisher1}')
                print('\nInformation about the Publisher 2:')
                print(f'{information_publisher2}')
                print('\nInformation about the Subscriber:')
                print(f'{information_subscriber}\n')
        
        additional_info_pub1 = information_publisher1.replace('\n', '<br>')      
        additional_info_pub2 = information_publisher2.replace('\n', '<br>')  
        additional_info_sub = information_subscriber.replace('\n', '<br>')  

        case.result = [Error(f'<strong> Publisher 1 expected code: </strong> {expected_code_pub1}; <strong> Code found: </strong> {code[1]} <br> \
                               <strong> Publisher 2 expected code: </strong> {expected_code_pub2}: <strong> Code found: </strong> {code[2]} <br> \
                               <strong> Subscriber expected code: </strong> {expected_code_sub}; <strong> Code found: </strong> {code[0]} <br>\
                              <strong> Information Publisher 1: </strong>  <br> {additional_info_pub1} <br>\
                              <strong> Information Publisher 2: </strong>  <br> {additional_info_pub2} <br>\
                              <strong> Information Subscriber: </strong>  <br> {additional_info_sub}' 
                          )
                      ]

    # Delete the temporal files
    os.remove('log_pub_1.txt')
    os.remove('log_pub_2.txt')
    os.remove('log_sub.txt')

class Arguments:
    def parser():
        parser = argparse.ArgumentParser(
            description='Interoperability Test',
            add_help=True)

        gen_opts = parser.add_argument_group(title='general options')
        gen_opts.add_argument('-P', '--publisher',
            default=None,
            required=True,
            type=str,
            choices=['connext611', 'opendds321', 'connext5.2.3'],
            metavar='publisher_name',
            help='Publisher Shape Application')
        gen_opts.add_argument('-S', '--subscriber',
            default=None,
            required=True,
            type=str, 
            choices=['connext611', 'opendds321', 'connext5.2.3'],
            metavar='subscriber_name',
            help='Subscriber Shape Application')
        
        optional = parser.add_argument_group(title='optional parameters')

        optional.add_argument('-v','--verbose',
            default=False,
            required=False,
            action='store_true',
            help='Print more information to stdout.')

        out_opts = parser.add_argument_group(title='output options')

        out_opts.add_argument('-f', '--output-format',
            default='junit',
            required=False,
            type=str,
            choices=['junit', 'csv', 'xlxs'],
            help='Output format.')
        out_opts.add_argument('-e', '--extend',
            default=False,
            required=False, 
            action='store_true',
            help='Save the results in a report that exists previously.')
        out_opts.add_argument('-o', '--output-name',
            required=False, 
            metavar='filename',
            type=str,
            help='Report filename.')
        
        return parser
    
   

def main():

    parser = Arguments.parser()
    args = parser.parse_args()

    gen_args = {
        'publisher': args.publisher,
        'subscriber': args.subscriber,
        'verbose' : args.verbose,
        'extend' : args.extend
    }


    if args.output_format is None:
        gen_args['output_format'] = 'junit'
    else:
        gen_args['output_format'] = args.output_format
    if args.output_name is None:
        now = datetime.now()
        date_time = now.strftime('%Y%m%d-%H_%M_%S')
        gen_args['filename_report'] = gen_args['publisher']+'-'+gen_args['subscriber']+'-'+date_time+'.xml'
        xml = JUnitXml()

    else:
        gen_args['filename_report'] = args.output_name
        if gen_args['extend']:
            xml = JUnitXml.fromfile(gen_args['filename_report'])
        else:
            xml = JUnitXml()
        
    
    suite = TestSuite(f"{gen_args['publisher']}---{gen_args['subscriber']}")

    for k, v in dict_param_expected_code_timeout.items():
        
        case = TestCase(f'{k}')
        if k ==  'Test_Ownership_3' or k == 'Test_Ownership_4':
            run_test_pub_pub_sub(gen_args['publisher'], gen_args['subscriber'], k, v[0], v[1], v[2],
                                 v[3], v[4], v[5], gen_args['verbose'], case, v[6])
        else:
            run_test(gen_args['publisher'], gen_args['subscriber'], k, v[0], v[1], v[2], v[3], 
                           gen_args['verbose'], case, v[4])
        
        suite.add_testcase(case)


    xml.add_testsuite(suite)   
 
    xml.write(gen_args['filename_report'])
   
    
if __name__ == '__main__':
    main()