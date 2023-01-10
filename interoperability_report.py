#!/usr/bin/python

from multiprocessing import Process, Queue
import sys
import time
import re
import pexpect
import multiprocessing
import argparse
import os
from junitparser import TestCase, TestSuite, JUnitXml, Error, Attr, Failure
from datetime import datetime
import tempfile
from os.path import exists

from utilities import ReturnCode, path_executables
from testSuite import rtps_test_suite_1

def log_message(message, verbosity):
    if verbosity:
        print(message)

def subscriber(name_executable, parameters, testCase, time_out, producedCode, samplesSent,
                subscriber_finished, publisher_finished, file, verbosity):
    """ Run the executable with the parameters and save
        the error code obtained

        name_executable     : name of the ShapeApplication to run
                              as a Subscriber
        parameters          : QOS to use with the Shape Application
        testCase            : testCase is being tested
                             (from rtps_test_suite_1)
        time_out            : time pexpect waits until it finds a pattern
        producedCode        : this variable will be overwritten with
                              the obtained ReturnCode
        samplesSent         : this variable contains the samples
                              the Publisher sends
        subscriber_finished : object event from multiprocessing that is set
                              when the subscriber is finished
        publisher_finished  : object event from multiprocessing that is set
                              when the publisher is finished
        file                : temporal file to save Shape Application output
        verbosity           : print debug information

        The function runs the Shape Application as a Subscriber
        with the parameters defined.
        The Subscriber Shape Application follows the next steps:
            * The topic is created
            * The Data Reader is created
            * The Data Reader matches with a Data Writer
            * The Data Reader detects the Data Writer as alive
            * The Data Reader receives data

        If the Shape Application achieves one step, it will print an specific string pattern.
        The function will recognize that pattern and it will continue also to the next step,
        waiting again for the next corresponding pattern to be recognized. If the Shape Application
        stops at some step, the function will not recognized the expected pattern (or it will
        recognized an error pattern), it will save the obtained ReturnCode and it will finish too.

    """
    # Step 1 : run the executable
    log_message('Running Shape Application Subscriber', verbosity)
    child_sub = pexpect.spawnu(f'{name_executable} {parameters}')
    child_sub.logfile =  file

    # Step 2 : Check if the topic is created
    log_message('Subscriber: Waiting for topic creation', verbosity)
    index = child_sub.expect(
        [
            'Create topic:',                                              # index = 0
            pexpect.TIMEOUT,                                              # index = 1
            'please specify topic name',                                  # index = 2
            'unrecognized value',                                         # index = 3
            pexpect.EOF                                                   # index = 4
        ],
        time_out
    )

    if index == 1 or index == 2 or index == 4:
        producedCode[0] = ReturnCode.TOPIC_NOT_CREATED
    elif index == 3:
        producedCode[0] = ReturnCode.UNRECOGNIZED_VALUE
    elif index == 0:
        # Step 3 : Check if the reader is created
        log_message('Subscriber: Waiting for Data Reader creation', verbosity)
        index = child_sub.expect(
            [
                'Create reader for topic:',                               # index = 0
                pexpect.TIMEOUT,                                          # index = 1
                'failed to create content filtered topic'                 # index = 2
            ],
            time_out
        )

        if index == 1:
            producedCode[0] = ReturnCode.READER_NOT_CREATED
        elif index == 2:
            producedCode[0] = ReturnCode.FILTER_NOT_CREATED
        elif index == 0:
            # Step 4 : Check if the reader matches the writer
            log_message('Subscriber: Waiting for Data Writer matching', verbosity)
            index = child_sub.expect(
                [
                    'on_subscription_matched()',                          # index = 0
                    pexpect.TIMEOUT,                                      # index = 1
                    'on_requested_incompatible_qos()'                     # index = 2
                ],
                time_out
            )

            if index == 1:
                producedCode[0] = ReturnCode.WRITER_NOT_MATCHED
            elif index == 2:
                producedCode[0] = ReturnCode.INCOMPATIBLE_QOS
            elif index == 0:
                # Step 5: Check if the reader detects the writer as alive
                log_message('Subscriber: Waiting for detecting Data Writer alive', verbosity)
                index = child_sub.expect(
                    [
                        'on_liveliness_changed()',                        # index = 0
                        pexpect.TIMEOUT                                   # index = 1
                    ],
                    time_out
                )

                if index == 1:
                    producedCode[0] = ReturnCode.WRITER_NOT_ALIVE
                elif index == 0:
                    #Step 6 : Check if the reader receives the samples
                    log_message('Subscriber: Waiting for receiving samples', verbosity)
                    index = child_sub.expect(
                            [
                                '\[[0-9][0-9]\]',                         # index = 0
                                pexpect.TIMEOUT                           # index = 1
                            ],
                            time_out
                        )

                    if index == 1:
                        producedCode[0] = ReturnCode.DATA_NOT_RECEIVED

                    elif index == 0:
                        # This test checks that data is received in the right order
                        if testCase == 'Test_Reliability_4':
                            for x in range(0, 3, 1):
                                sub_string = re.search('[0-9]{3} [0-9]{3}',
                                                        child_sub.before)
                                if samplesSent.get() == sub_string.group(0):
                                    producedCode[0] = ReturnCode.OK
                                else:
                                    producedCode[0] = ReturnCode.DATA_NOT_CORRECT
                                    break
                                log_message('Subscriber: Waiting for receiving samples', verbosity)
                                child_sub.expect(
                                            [
                                            '\[[0-9][0-9]\]',             # index = 0
                                            pexpect.TIMEOUT               # index = 1
                                            ],
                                            time_out
                                )
                        # Two Publishers and One Subscriber to test that if each one has a different color, the ownership strength does not matter
                        elif testCase == 'Test_Ownership_3':
                            red_received = False
                            blue_received = False
                            producedCode[0] = ReturnCode.RECEIVING_FROM_ONE
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
                                    producedCode[0] = ReturnCode.RECEIVING_FROM_BOTH
                                    break
                                log_message('Subscriber: Waiting for receiving samples', verbosity)
                                child_sub.expect(
                                            [
                                            '\[[0-9][0-9]\]',             # index = 0
                                            pexpect.TIMEOUT               # index = 1
                                            ],
                                            time_out
                                )
                        # Two Publishers and One Subscriber to test that the Subscriber only receives samples from the Publisher with the greatest ownership
                        elif testCase == 'Test_Ownership_4':

                            second_received = False
                            list_data_received_second = []
                            for x in range(0,40,1):
                                sub_string = re.search('[0-9]{3} [0-9]{3}',
                                                        child_sub.before)

                                try:
                                    list_data_received_second.append(samplesSent.get(True, 5))
                                except:
                                    break;

                                if sub_string.group(0) in list_data_received_second:
                                    second_received = True
                                    producedCode[0] = ReturnCode.RECEIVING_FROM_BOTH
                                log_message('Subscriber: Waiting for receiving samples', verbosity)
                                child_sub.expect(
                                            [
                                            '\[[0-9][0-9]\]',             # index = 0
                                            pexpect.TIMEOUT               # index = 1
                                            ],
                                            time_out
                                )

                            if second_received == False:
                                producedCode[0] = ReturnCode.RECEIVING_FROM_ONE

                        else:
                            producedCode[0] = ReturnCode.OK

    subscriber_finished.set()   # set subscriber as finished
    log_message('Subscriber: Waiting for Publisher to finish', verbosity)
    publisher_finished.wait()   # wait for publisher to finish
    return


def publisher(name_executable, parameters, testCase, time_out, producedCode, samplesSent,
                id_pub, subscriber_finished, publisher_finished, file, verbosity):
    """ Run the executable with the parameters and save
        the error code obtained

        name_executable     : name of the ShapeApplication to run
                              as a Publisher
        parameters          : QOS to use with the Shape Application
        testCase            : testCase is being tested
                             (from rtps_test_suite_1)
        time_out            : time pexpect waits until it finds a pattern
        producedCode                : this variable will be overwritten with
                              the obtained ReturnCode
        samplesSent                : this variable contains the samples
                              the Publisher sends
        id_pub              : Publisher's id (1|2)
        subscriber_finished : object event from multiprocessing that is set
                              when the subscriber is finished
        publisher_finished  : object event from multiprocessing that is set
                              when the publisher is finished
        file                : temporal file to save Shape Application output
        verbosity           : print debug information

        The function runs the Shape Application as a Publisher
        with the parameters defined.
        The Publisher Shape Application follows the next steps:
            * The topic is created
            * The Data Writer is created
            * The Data Writer matches with a Data Reader
            * The Data Writer sends data

        If the Shape Application achieves one step, it will print an specific string pattern.
        The function will recognize that pattern and it will continue also to the next step,
        waiting again for the next corresponding pattern to be recognized. If the Shape Application
        stops at some step, the function will not recognized the expected pattern (or it will
        recognized an error pattern), it will save the obtained ReturnCode and it will finish too.
    """

    # Step 1 : run the executable
    log_message('Running Shape Application Publisher', verbosity)
    child_pub = pexpect.spawnu(f'{name_executable} {parameters}')
    child_pub.logfile = file

    # Step 2 : Check if the topic is created
    log_message('Publisher: Waiting for topic creation', verbosity)
    index = child_pub.expect(
        [
            'Create topic:',                                              # index == 0
            pexpect.TIMEOUT,                                              # index == 1
            'please specify topic name',                                  # index == 2
            'unrecognized value',                                         # index == 3
            pexpect.EOF                                                   # index == 4
        ],
        time_out
    )

    if index == 1 or index == 2 or index == 4:
        producedCode[id_pub] = ReturnCode.TOPIC_NOT_CREATED
    elif index == 3:
        producedCode[id_pub] = ReturnCode.UNRECOGNIZED_VALUE
    elif index == 0:
        # Step 3 : Check if the writer is created
        log_message('Publisher: Waiting for Data Writer creation', verbosity)
        index = child_pub.expect(
            [
                'Create writer for topic',                                # index = 0
                pexpect.TIMEOUT                                           # index = 1
            ],
            time_out
        )
        if index == 1:
            producedCode[id_pub] = ReturnCode.WRITER_NOT_CREATED
        elif index == 0:
            # Step 4 : Check if the writer matches the reader
            log_message('Publisher: Waiting for Data Reader matching', verbosity)
            index = child_pub.expect(
                [
                    'on_publication_matched()',                           # index = 0
                    pexpect.TIMEOUT,                                      # index = 1
                    'on_offered_incompatible_qos'                         # index = 2
                ],
                time_out
            )
            if index == 1:
                producedCode[id_pub] = ReturnCode.READER_NOT_MATCHED
            elif index == 2:
                producedCode[id_pub] = ReturnCode.INCOMPATIBLE_QOS
            elif index == 0:
                if '-v' in parameters:
                    #Step  5: Check if the writer sends the samples
                    log_message('Publisher: Waiting for sending samples', verbosity)
                    index = child_pub.expect(
                            [
                                '\[[0-9][0-9]\]',                         # index = 0
                                pexpect.TIMEOUT                           # index = 1
                            ],
                            time_out
                        )
                    if index == 0:
                        producedCode[id_pub] = ReturnCode.OK
                        # With these tests we check if we receive the data correctly, in order to do it we are saving the samples sent
                        if testCase == 'Test_Reliability_4' or testCase == 'Test_Ownership_4':
                            for x in range(0, 40 ,1):
                                pub_string = re.search('[0-9]{3} [0-9]{3}',
                                                            child_pub.before )
                                samplesSent.put(pub_string.group(0))
                                log_message('Publisher: Waiting for sending samples', verbosity)
                                child_pub.expect([
                                            '\[[0-9][0-9]\]',             # index = 0
                                            pexpect.TIMEOUT               # index = 1
                                                ],
                                            time_out
                                )

                    elif index == 1:
                        producedCode[id_pub] = ReturnCode.DATA_NOT_SENT
                else:
                    producedCode[id_pub] = ReturnCode.OK

    log_message('Publisher: Waiting for Subscriber to finish', verbosity)
    subscriber_finished.wait() # wait for subscriber to finish
    publisher_finished.set()   # set publisher as finished
    return


def run_test(name_pub, name_sub, testCase, param_pub, param_sub,
                expected_code_pub, expected_code_sub, verbosity,
                time_out):
    """ Run the Publisher and the Subscriber and check the ReturnCode

        name_pub          : name of the Shape Application to run
                            as a Publisher
        name_sub          : name of the Shape Application to run
                            as a Subscriber
        testCase          : testCase is being tested
                            (from rtps_test_suite_1)
        param_pub         : QoS for the Publisher
        param_sub         : QoS for the Subscriber
        expected_code_pub : ReturnCode the Publisher would obtain
                            in a non error situation
        expected_code_sub : ReturnCode the Subscriber would obtain
                            in a non error situation
        verbosity         : print debug information
        time_out          : timeout for pexpect.

        The function runs in two different Processes
        the Publisher and the Subscriber.
        Then it checks that the code obtained is the one
        we expected.
    """
    log_message(f'run_test parameters: \
                    name_pub: {name_pub}\
                    name_sub: {name_sub}\
                    testCase: {testCase.name}\
                    param_pub: {param_pub}\
                    param_sub: {param_sub}\
                    expected_code_pub: {expected_code_pub}\
                    expected_code_sub: {expected_code_sub}\
                    verbosity: {verbosity}\
                    time_out: {time_out}',
                    verbosity)

    manager = multiprocessing.Manager()
     # used for storing the obtained ReturnCode
     # (from Publisher and Subscriber)
    code = manager.list(range(2))
    data = Queue() # used for storing the samples

    subscriber_finished = multiprocessing.Event()
    publisher_finished = multiprocessing.Event()


    file_publisher = tempfile.TemporaryFile(mode='w+t')
    file_subscriber = tempfile.TemporaryFile(mode='w+t')

    log_message('Assigning tasks to processes', verbosity)
    pub = Process(target=publisher,
                    kwargs={
                        'name_executable':path_executables[name_pub],
                        'parameters':param_pub,
                        'testCase':testCase.name,
                        'time_out':time_out,
                        'producedCode':code,
                        'samplesSent':data,
                        'id_pub':1,
                        'subscriber_finished':subscriber_finished,
                        'publisher_finished':publisher_finished,
                        'file':file_publisher,
                        'verbosity':verbosity
                    })

    sub = Process(target=subscriber,
                    kwargs={
                        'name_executable':path_executables[name_sub],
                        'parameters':param_sub,
                        'testCase':testCase.name,
                        'time_out':time_out,
                        'producedCode':code,
                        'samplesSent':data,
                        'subscriber_finished':subscriber_finished,
                        'publisher_finished':publisher_finished,
                        'file':file_subscriber,
                        'verbosity':verbosity
                    })
    log_message('Running Subscriber process', verbosity)
    sub.start()
    log_message('Running Publisher process', verbosity)
    pub.start()
    sub.join()
    pub.join()

    log_message('Reading information from temporary files', verbosity)
    file_publisher.seek(0)
    file_subscriber.seek(0)
    information_publisher = file_publisher.read()
    information_subscriber = file_subscriber.read()

    TestCase.param = Attr('Parameters_Publisher')
    TestCase.id = Attr('Parameters_Subscriber')
    testCase.param = param_pub
    testCase.id = param_sub

    if expected_code_pub ==  code[1] and expected_code_sub == code[0]:
        print (f'{testCase.name} : Ok')

    else:
        print(f'Error in : {testCase.name}')
        print(f'Publisher expected code: {expected_code_pub}; \
                Code found: {code[1].name}')
        print(f'Subscriber expected code: {expected_code_sub}; \
                Code found: {code[0].name}')
        log_message(f'\nInformation about the Publisher:\n\
                      {information_publisher} \
                      \nInformation about the Subscriber:\n\
                      {information_subscriber}', verbosity)

        additional_info_pub = information_publisher.replace('\n', '<br>')
        additional_info_sub = information_subscriber.replace('\n', '<br>')
        testCase.result = [Failure(f'<table> \
                                    <tr> \
                                        <th></th> \
                                        <th>Expected Code</th> \
                                        <th>Code Produced</th> \
                                    </tr> \
                                    <tr> \
                                        <th>Publisher</th> \
                                        <th>{expected_code_pub.name}</th> \
                                        <th>{code[1].name}</th> \
                                    </tr> \
                                    <tr> \
                                        <th>Subscriber</th> \
                                        <th>{expected_code_sub.name}</th> \
                                        <th>{code[0].name}</th> \
                                    </tr> \
                                </table> \
                               <strong> Information Publisher: </strong>  <br> {additional_info_pub} <br>\
                               <strong> Information Subscriber: </strong>  <br> {additional_info_sub}')]

    file_publisher.close()
    file_subscriber.close()


def run_test_pub_pub_sub(name_pub, name_sub, testCase, param_pub1, param_pub2, param_sub,
                         expected_code_pub1, expected_code_pub2, expected_code_sub,
                         verbosity, time_out):
    """ Run two Publisher and one Subscriber and check the ReturnCode

        name_pub           : name of the Shape Application to run
                             as a Publisher
        name_sub           : name of the Shape Application to run
                             as a Subscriber
        testCase           : testCase that is being tested
                            (from rtps_test_suite_1)
        param_pub1         : QoS for the Publisher 1
        param_pub2         : QoS for the Publisher 2
        param_sub          : QoS for the Subscriber
        expected_code_pub1 : ReturnCode the Publisher 1 would obtain
                             in a non error situation
        expected_code_pub2 : ReturnCode the Publisher 2 would obtain
                             in a non error situation
        expected_code_sub  : ReturnCode the Subscriber would obtain
                             in a non error situation
        verbosity            : boolean. True means the Publisher and Subscriber's
                             output will be shown on the console if there is
                             an error.
        time_out           : timeout for pexpect.

        The function runs in three different Processes
        the first Publisher, the second Publisher and the Subscriber.
        Then it checks that the code obtained is the one
        we expected.
    """
    log_message(f'run_test parameters: \
                    name_pub: {name_pub}\
                    name_sub: {name_sub}\
                    testCase: {testCase.name}\
                    param_pub1: {param_pub1}\
                    param_pub2: {param_pub2}\
                    param_sub: {param_sub}\
                    expected_code_pub1: {expected_code_pub1}\
                    expected_code_pub2: {expected_code_pub2}\
                    expected_code_sub: {expected_code_sub}\
                    verbosity: {verbosity}\
                    time_out: {time_out}',
                    verbosity)
    manager = multiprocessing.Manager()
    # used for storing the obtained ReturnCode
    # (from Publisher 1, Publisher 2 and Subscriber)
    code = manager.list(range(3))
    data = Queue() # used for storing the samples
    subscriber_finished = multiprocessing.Event()
    publisher_finished = multiprocessing.Event()

    log_message('Creating temporary files', verbosity)
    file_subscriber = tempfile.TemporaryFile(mode='w+t')
    file_publisher1 = tempfile.TemporaryFile(mode='w+t')
    file_publisher2 = tempfile.TemporaryFile(mode='w+t')

    if testCase.name == 'Test_Ownership_3':
        pub1 = Process(target=publisher,
                        kwargs={
                            'name_executable':path_executables[name_pub],
                            'parameters':param_pub1,
                            'testCase':testCase.name,
                            'time_out':time_out,
                            'producedCode':code,
                            'samplesSent':data,
                            'id_pub':1,
                            'subscriber_finished':subscriber_finished,
                            'publisher_finished':publisher_finished,
                            'file':file_publisher1,
                            'verbosity':verbosity
                        })
        pub2 = Process(target=publisher,
                        kwargs={
                            'name_executable':path_executables[name_pub],
                            'parameters':param_pub2,
                            'testCase':testCase.name,
                            'time_out':time_out,
                            'producedCode':code,
                            'samplesSent':data,
                            'id_pub':2,
                            'subscriber_finished':subscriber_finished,
                            'publisher_finished':publisher_finished,
                            'file':file_publisher2,
                            'verbosity':verbosity
                        })
        sub = Process(target=subscriber,
                        kwargs={
                            'name_executable':path_executables[name_sub],
                            'parameters':param_sub,
                            'testCase':testCase.name,
                            'time_out':time_out,
                            'producedCode':code,
                            'samplesSent':data,
                            'subscriber_finished':subscriber_finished,
                            'publisher_finished':publisher_finished,
                            'file':file_subscriber,
                            'verbosity':verbosity
                        })

    if testCase.name == 'Test_Ownership_4':
        pub1 = Process(target=publisher,
                        kwargs={
                            'name_executable':path_executables[name_pub],
                            'parameters':param_pub1,
                            'testCase':testCase.name,
                            'time_out':time_out,
                            'producedCode':code,
                            'samplesSent':Queue(),
                            'id_pub':1,
                            'subscriber_finished':subscriber_finished,
                            'publisher_finished':publisher_finished,
                            'file':file_publisher1,
                            'verbosity':verbosity
                        })
        pub2 = Process(target=publisher,
                        kwargs={
                            'name_executable':path_executables[name_pub],
                            'parameters':param_pub2,
                            'testCase':testCase.name,
                            'time_out':time_out,
                            'producedCode':code,
                            'samplesSent':data,
                            'id_pub':2,
                            'subscriber_finished':subscriber_finished,
                            'publisher_finished':publisher_finished,
                            'file':file_publisher2,
                            'verbosity':verbosity
                        })
        sub = Process(target=subscriber,
                        kwargs={
                            'name_executable':path_executables[name_sub],
                            'parameters':param_sub,
                            'testCase':testCase.name,
                            'time_out':time_out,
                            'producedCode':code,
                            'samplesSent':data,
                            'subscriber_finished':subscriber_finished,
                            'publisher_finished':publisher_finished,
                            'file':file_subscriber,
                            'verbosity':verbosity
                        })

    log_message('Running Subscriber process', verbosity)
    sub.start()
    log_message('Running Publisher 1 process', verbosity)
    pub1.start()
    time.sleep(1) # used to make the two Publishers have different seeds
                  # to generate the samples
    log_message('Running Publisher 2 process', verbosity)
    pub2.start()

    sub.join()
    pub1.join()
    pub2.join()

    log_message('Reading information from temporary files', verbosity)
    file_publisher1.seek(0)
    file_publisher2.seek(0)
    file_subscriber.seek(0)
    information_publisher1 = file_publisher1.read()
    information_publisher2 = file_publisher2.read()
    information_subscriber = file_subscriber.read()

    TestCase.custom = Attr('Parameters')
    testCase.custom = (f'\
                        {name_pub} {param_pub1} \
                        | {name_pub} {param_pub2} \
                        | {name_sub} {param_sub}'
                      )
    if expected_code_pub1 ==  code[1] and expected_code_sub == code[0] \
        and expected_code_pub2 == code[2]:
        print (f'{testCase.name} : Ok')

    else:
        print(f'Error in : {testCase.name}')
        print(f'Publisher 1 expected code: {expected_code_pub1}; \
                Code found: {code[1]}')
        print(f'Publisher 2 expected code: {expected_code_pub2}; \
                Code found: {code[2]}')
        print(f'Subscriber expected code: {expected_code_sub}; \
                Code found: {code[0]}')
        log_message(f'\nInformation about the Publisher 1:\n\
                      {information_publisher1} \
                      \nInformation about the Publisher 2:\n\
                      {information_publisher2} \
                      \nInformation about the Subscriber:\n\
                      {information_subscriber}', verbosity)

        additional_info_pub1 = information_publisher1.replace('\n', '<br>')
        additional_info_pub2 = information_publisher2.replace('\n', '<br>')
        additional_info_sub = information_subscriber.replace('\n', '<br>')

        testCase.result = [Error(f'<strong> Publisher 1 expected code: </strong> {expected_code_pub1}; \
                                   <strong> Code found: </strong> {code[1]} <br> \
                                   <strong> Publisher 2 expected code: </strong> {expected_code_pub2}: \
                                   <strong> Code found: </strong> {code[2]} <br> \
                                   <strong> Subscriber expected code: </strong> {expected_code_sub}; \
                                   <strong> Code found: </strong> {code[0]} <br>\
                                   <strong> Information Publisher 1: </strong>  <br> {additional_info_pub1} <br>\
                                   <strong> Information Publisher 2: </strong>  <br> {additional_info_pub2} <br>\
                                   <strong> Information Subscriber: </strong>  <br> {additional_info_sub}'
                          )
                      ]

    file_subscriber.close()
    file_publisher1.close()
    file_publisher2.close()

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
            choices=['connext611', 'opendds321'],
            metavar='publisher_name',
            help='Publisher Shape Application')
        gen_opts.add_argument('-S', '--subscriber',
            default=None,
            required=True,
            type=str,
            choices=['connext611', 'opendds321'],
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
        out_opts.add_argument('-o', '--output-name',
            required=False,
            metavar='filename',
            type=str,
            help='Report filename.')

        return parser

def main():

    parser = Arguments.parser()
    args = parser.parse_args()

    options = {
        'publisher': args.publisher,
        'subscriber': args.subscriber,
        'verbosity' : args.verbose,
    }


    if args.output_format is None:
        options['output_format'] = 'junit'
    else:
        options['output_format'] = args.output_format
    if args.output_name is None:
        now = datetime.now()
        date_time = now.strftime('%Y%m%d-%H_%M_%S')
        options['filename_report'] = options['publisher']+'-'+options['subscriber']+'-'+date_time+'.xml'
        xml = JUnitXml()

    else:
        options['filename_report'] = args.output_name
        file_exists = exists(options['filename_report'])
        if file_exists:
            xml = JUnitXml.fromfile(options['filename_report'])
        else:
            xml = JUnitXml()

    suite = TestSuite(f"{options['publisher']}---{options['subscriber']}")

    timeout = 10 # see if i should put it in another place
    for k, v in rtps_test_suite_1.items():

        case = TestCase(f'{k}')
        if k ==  'Test_Ownership_3' or k == 'Test_Ownership_4':
            run_test_pub_pub_sub(name_pub=options['publisher'],
                                 name_sub=options['subscriber'],
                                 testCase=case,
                                 param_pub1=v[0],
                                 param_pub2=v[1],
                                 param_sub=v[2],
                                 expected_code_pub1=v[3],
                                 expected_code_pub2=v[4],
                                 expected_code_sub=v[5],
                                 verbosity=options['verbosity'],
                                 time_out=timeout
            )

        else:
            run_test(name_pub=options['publisher'],
                     name_sub=options['subscriber'],
                     testCase=case,
                     param_pub=v[0],
                     param_sub=v[1],
                     expected_code_pub=v[2],
                     expected_code_sub=v[3],
                     verbosity=options['verbosity'],
                     time_out=timeout
            )

        suite.add_testcase(case)


    xml.add_testsuite(suite)

    xml.write(options['filename_report'])

if __name__ == '__main__':
    main()
