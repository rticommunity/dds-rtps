#!/usr/bin/python

import importlib
import time
import re
import pexpect
import argparse
import junitparser
import multiprocessing
from datetime import datetime
import tempfile
from os.path import exists
import inspect

from rtps_test_utilities import ReturnCode, log_message, no_check
MAX_SAMPLES_SAVED = 100 # used to save the samples the Publisher sends.
                        # MAX_SAMPLES_SAVED is the maximum number of samples
                        # saved.
SLEEP_TIME = 1          # used to generate different seeds for the Publisher's
                        # samples. The Publisher sleeps <SLEEP_TIME> before
                        # sending the samples.

def run_subscriber_shape_main(
        name_executable: str,
        parameters: str,
        produced_code: "list[int]",
        produced_code_index: int,
        samples_sent: "list[multiprocessing.Queue]",
        verbosity: bool,
        timeout: int,
        file: tempfile.TemporaryFile,
        subscriber_finished: multiprocessing.Event,
        publishers_finished: "list[multiprocessing.Event]",
        check_function: "function"):

    """ This function runs the subscriber shape_main application with
        the specified parameters. Then it saves the
        return code in the variable produced_code.

        name_executable <<in>>: name of the shape_main application to run
                as a Subscriber.
        parameters <<in>>: shape_main application parameter list.
        produced_code <<out>>: this variable will be overwritten with
                the obtained ReturnCode.
        produced_code_index <<in>>: index of the produced_code list
                where the ReturnCode is saved.
        samples_sent <<in>>: list of multiprocessing Queues with the samples
                the Publishers send. Element 1 of the list is for
                Publisher 1, etc.
        verbosity <<in>>: print debug information.
        timeout <<in>>: time pexpect waits until it matches a pattern.
        file <<inout>>: temporal file to save shape_main application output.
        subscriber_finished <<inout>>: object event from multiprocessing
                that is set when the subscriber is finished.
        publishers_finished <<inout>>: list of events from multiprocessing
                that are set when the publishers are finished.
                Element 1 of the list is for Publisher 1, etc.
        check_function <<in>>: function to check how the samples are received
                by the Subscriber. By default it does not check anything.

        The function runs the shape_main application as a Subscriber
        with the parameters defined.
        The Subscriber shape_main application follows the next steps:
            * The topic is created.
            * The Data Reader is created.
            * The Data Reader matches with a Data Writer.
            * The Data Reader detects the Data Writer as alive.
            * The Data Reader receives data.

        If the shape_main application passes one step, it prints a specific
        string pattern. This function matches that pattern and and waits
        for the next input string from the shape_main application. If the
        shape_main application stops at some step, it prints an error message.
        When this function matches an error string (or doesn't match
        an expected pattern in the specified timeout),
        the corresponding ReturnCode is saved in
        produced_code[produced_code_index] and the process finishes.

    """
    # Step 1 : run the executable
    log_message('Running shape_main application Subscriber', verbosity)
    child_sub = pexpect.spawnu(f'{name_executable} {parameters}')
    child_sub.logfile = file

    # Step 2 : Check if the topic is created
    log_message('S: Waiting for topic creation', verbosity)
    index = child_sub.expect(
        [
            'Create topic:', # index = 0
            pexpect.TIMEOUT, # index = 1
            'please specify topic name', # index = 2
            'unrecognized value', # index = 3
            pexpect.EOF # index = 4
        ],
        timeout
    )

    if index == 1 or index == 2 or index == 4:
        produced_code[produced_code_index] = ReturnCode.TOPIC_NOT_CREATED
    elif index == 3:
        produced_code[produced_code_index] = ReturnCode.UNRECOGNIZED_VALUE
    elif index == 0:
        # Step 3 : Check if the reader is created
        log_message('S: Waiting for DR creation', verbosity)
        index = child_sub.expect(
            [
                'Create reader for topic:', # index = 0
                pexpect.TIMEOUT, # index = 1
                'failed to create content filtered topic' # index = 2
            ],
            timeout
        )

        if index == 1:
            produced_code[produced_code_index] = ReturnCode.READER_NOT_CREATED
        elif index == 2:
            produced_code[produced_code_index] = ReturnCode.FILTER_NOT_CREATED
        elif index == 0:
            # Step 4 : Check if the reader matches the writer
            log_message('S: Waiting for DW matching', verbosity)
            index = child_sub.expect(
                [
                    'on_subscription_matched()', # index = 0
                    pexpect.TIMEOUT, # index = 1
                    'on_requested_incompatible_qos()' # index = 2
                ],
                timeout
            )

            if index == 1:
                produced_code[produced_code_index] = ReturnCode.WRITER_NOT_MATCHED
            elif index == 2:
                produced_code[produced_code_index] = ReturnCode.INCOMPATIBLE_QOS
            elif index == 0:
                # Step 5: Check if the reader detects the writer as alive
                log_message('S: Waiting for detecting DW alive', verbosity)
                index = child_sub.expect(
                    [
                        'on_liveliness_changed()', # index = 0
                        pexpect.TIMEOUT # index = 1
                    ],
                    timeout
                )

                if index == 1:
                    produced_code[produced_code_index] = ReturnCode.WRITER_NOT_ALIVE
                elif index == 0:
                    #Step 6 : Check if the reader receives the samples
                    log_message('S: Waiting for receiving samples', verbosity)
                    index = child_sub.expect(
                            [
                                '\[[0-9][0-9]\]', # index = 0
                                pexpect.TIMEOUT # index = 1
                            ],
                            timeout
                        )

                    if index == 1:
                        produced_code[produced_code_index] = ReturnCode.DATA_NOT_RECEIVED
                    elif index == 0:
                        # this is used to check how the samples are arriving
                        # to the Subscriber. By default it does not check
                        # anything and returns ReturnCode.OK.
                        produced_code[produced_code_index] = check_function(
                                                                child_sub,
                                                                samples_sent,
                                                                timeout,
                                                                verbosity)

    subscriber_finished.set()   # set subscriber as finished
    log_message('S: Waiting for PublisherS to finish', verbosity)
    for element in publishers_finished:
        element.wait()   # wait for all publishers to finish
    return


def run_publisher_shape_main(
        name_executable: str,
        parameters: str,
        produced_code: "list[int]",
        produced_code_index: int,
        samples_sent: multiprocessing.Queue,
        verbosity: bool,
        timeout: int,
        file: tempfile.TemporaryFile,
        subscribers_finished: "list[multiprocessing.Event]",
        publisher_finished: multiprocessing.Event):

    """ This function runs the publisher shape_main application with
        the specified parameters. Then it saves the
        return code in the variable produced_code.

        name_executable: <<in>> name of the shape_main application to run
                as a Publisher.
        parameters <<in>>: shape_main application parameter list.
        produced_code <<out>>: this variable will be overwritten with
                the obtained ReturnCode.
        produced_code_index <<in>>: index of the produced_code list
                where the ReturnCode is saved.
        samples_sent <<out>>: this variable contains the samples
                the Publisher sends.
        verbosity <<in>>: print debug information.
        timeout <<in>>: time pexpect waits until it matches a pattern.
        file <<inout>>: temporal file to save shape_main application output.
        subscribers_finished <<inout>>: list of events from multiprocessing
                that are set when the subscribers are finished.
                Element 1 of the list is for Subscriber 1, etc.
        publisher_finished <<inout>>: object event from multiprocessing
                that is set when the publisher is finished.

        The function runs the shape_main application as a Publisher
        with the parameters defined.
        The Publisher shape_main application follows the next steps:
            * The topic is created.
            * The Data Writer is created.
            * The Data Writer matches with a Data Reader.
            * The Data Writer sends data.

        If the shape_main application passes one step, it prints a specific
        string pattern. This function matches that pattern and and waits
        for the next input string from the shape_main application. If the
        shape_main application stops at some step, it prints an error message.
        When this function matches an error string (or doesn't match
        an expected pattern in the specified timeout),
        the corresponding ReturnCode is saved in
        produced_code[produced_code_index] and the process finishes.
    """

    # Step 1 : run the executable
    log_message('Running shape_main application Publisher', verbosity)
    child_pub = pexpect.spawnu(f'{name_executable} {parameters}')
    child_pub.logfile = file

    # Step 2 : Check if the topic is created
    log_message('P: Waiting for topic creation', verbosity)
    index = child_pub.expect(
        [
            'Create topic:', # index == 0
            pexpect.TIMEOUT, # index == 1
            'please specify topic name', # index == 2
            'unrecognized value', # index == 3
            pexpect.EOF # index == 4
        ],
        timeout
    )

    if index == 1 or index == 2 or index == 4:
        produced_code[produced_code_index] = ReturnCode.TOPIC_NOT_CREATED
    elif index == 3:
        produced_code[produced_code_index] = ReturnCode.UNRECOGNIZED_VALUE
    elif index == 0:
        # Step 3 : Check if the writer is created
        log_message('P: Waiting for DW creation', verbosity)
        index = child_pub.expect(
            [
                'Create writer for topic', # index = 0
                pexpect.TIMEOUT # index = 1
            ],
            timeout
        )
        if index == 1:
            produced_code[produced_code_index] = ReturnCode.WRITER_NOT_CREATED
        elif index == 0:
            # Step 4 : Check if the writer matches the reader
            log_message('P: Waiting for DR matching', verbosity)
            index = child_pub.expect(
                [
                    'on_publication_matched()', # index = 0
                    pexpect.TIMEOUT, # index = 1
                    'on_offered_incompatible_qos' # index = 2
                ],
                timeout
            )
            if index == 1:
                produced_code[produced_code_index] = ReturnCode.READER_NOT_MATCHED
            elif index == 2:
                produced_code[produced_code_index] = ReturnCode.INCOMPATIBLE_QOS
            elif index == 0:
                # In the case that the option -w is selected, the Publisher
                # saves the samples sent in order, so the Subscriber can check
                # them. In this way, the script can check the functionality of
                # reliability (all the samples are received and in the same
                # order).
                # In the case that the option -w is not selected, the Publisher
                # will only save the ReturnCode OK.
                if '-w' in parameters:
                    #Step  5: Check if the writer sends the samples
                    log_message('P: Waiting for sending samples', verbosity)
                    index = child_pub.expect(
                            [
                                '\[[0-9][0-9]\]', # index = 0
                                pexpect.TIMEOUT # index = 1
                            ],
                            timeout
                        )
                    if index == 0:
                        produced_code[produced_code_index] = ReturnCode.OK
                        for x in range(0, MAX_SAMPLES_SAVED, 1):
                            # We select the numbers that identify the samples
                            # and we add them to samples_sent.
                            pub_string = re.search('[0-9]{3} [0-9]{3}',
                                    child_pub.before)
                            samples_sent.put(pub_string.group(0))
                            log_message('P: Waiting for sending samples',
                                            verbosity)
                            child_pub.expect([
                                            '\[[0-9][0-9]\]', # index = 0
                                            pexpect.TIMEOUT # index = 1
                                                ],
                                            timeout
                            )

                    elif index == 1:
                        produced_code[produced_code_index] = ReturnCode.DATA_NOT_SENT
                else:
                    produced_code[produced_code_index] = ReturnCode.OK

    log_message('P: Waiting for Subscriber to finish', verbosity)
    for element in subscribers_finished:
        element.wait() # wait for all subscribers to finish
    publisher_finished.set()   # set publisher as finished
    return


def run_test(
    name_executable_pub:str,
    name_executable_sub:str,
    test_case: junitparser.TestCase,
    parameters: "list[str]",
    expected_codes: "list[str]",
    verbosity: bool,
    timeout: int,
    check_function: "function"):

    """ Run the Publisher and the Subscriber applications and check
        the actual and the expected ReturnCode.

        name_executable_pub <<in>>: name of the shape_main application to run
                as a Publisher.
        name_executable_sub <<in>>: name of the shape_main application to run
                as a Subscriber.
        test_case <<inout>>: testCase object to test.
        parameters <<in>>: list of shape_main application parameters.
        expected_codes <<in>>: list of ReturnCodes the Publishers and
                the Subscribers would obtain in a non error situation.
        verbosity <<in>>: print debug information.
        timeout <<in>>: time pexpect waits until it matches a pattern.
        check_function <<in>>: function to check how the samples are received
                by the Subscriber. By default it does not check anything.

        The function runs several different processes: one for each Publisher
        and one for each Subscriber shape_main application.
        The number of processes depends on how many elements are in
        the list of parameters.
        Then it checks that the codes obtained are the expected ones.
    """
    log_message(f'run_test parameters: \
                    name_executable_pub: {name_executable_pub} \
                    name_executable_sub: {name_executable_sub} \
                    test_case: {test_case.name} \
                    parameters: {parameters} \
                    expected_codes: {expected_codes} \
                    verbosity: {verbosity} \
                    timeout: {timeout} \
                    check_function: {check_function.__name__}',
                    verbosity)

    # numbers of publishers/subscriber we will have. It depends on how
    # many strings of parameters we have.
    num_entities = len(parameters)

    # Manager is a shared memory section where all processes can access.
    # 'return_code' is a list of elements where the different processes
    # (publishers and subscribers shape_main applications) copy their ReturnCode.
    # These ReturnCodes are identified by the index within the list,
    # every index identifies one shape_main application. Therefore, only one
    # shape_main application must modify one element of the list.
    # Once all processes are finished, the list 'return_code' contains
    # the ReturnCode in the corresponding index. This index is set manually
    # and we need it in order to use it later.
    # Example: (1 Publisher and 1 Subscriber)
    #   Processes:
    #     - Publisher Process (index = 0)
    #     - Subscriber Process (index = 1)
    #   Code contains:
    #     - return_code[0] contains Publisher shape_main application ReturnCode
    #     - return_code[1] contains Subscriber shape_main application ReturnCode
    manager = multiprocessing.Manager()
    return_code = manager.list(range(num_entities))
    samples_sent = [] # used for storing the samples the Publishers send.
                      # It is a list with one Queue for each Publisher.

    # list of multiprocessing Events used as semaphores to control the end of
    # the processes, one for each entity.
    subscribers_finished = []
    publishers_finished = []
    num_publishers = 0
    num_subscribers = 0
    # entity_type defines the name of the entity: Publisher/Subscriber_<number>.
    entity_type = []
    # list of files to save the shape_main output, one for each entity.
    temporary_file = []
    # list of shape_main application outputs, one for each entity.
    shape_main_application_output = []
    # list of processes, one for each entity
    entity_process = []
    # list of shape_main application outputs, edited to use in the html code.
    shape_main_application_output_edited = []
    # We will create these elements earlier because we need
    # them to define the processes.
    for element in parameters:
        temporary_file.append(tempfile.TemporaryFile(mode='w+t'))
        if ('-P ' in element or element.endswith('-P')):
            publishers_finished.append(multiprocessing.Event())
            samples_sent.append(multiprocessing.Queue())
        elif ('-S ' in element or element.endswith('-S')):
            subscribers_finished.append(multiprocessing.Event())
        else:
            print('Error in the definition of shape_main application parameters. \
                Neither Publisher or Subscriber defined.')
            return

    for i in range(0, num_entities):
        if ('-P ' in parameters[i] or parameters[i].endswith('-P')):
            entity_process.append(multiprocessing.Process(target=run_publisher_shape_main,
                            kwargs={
                                'name_executable':name_executable_pub,
                                'parameters':parameters[i],
                                'produced_code':return_code,
                                'produced_code_index':i,
                                'samples_sent':samples_sent[num_publishers],
                                'verbosity':verbosity,
                                'timeout':timeout,
                                'file':temporary_file[i],
                                'subscribers_finished':subscribers_finished,
                                'publisher_finished':publishers_finished[num_publishers]
            }))
            num_publishers += 1
            entity_type.append(f'Publisher_{num_publishers}')
            if num_publishers > 1:
                time.sleep(SLEEP_TIME) # used to generate different seeds for
                                       # each publisher's samples. Used only if
                                       # there is more than one publisher
        elif('-S ' in parameters[i] or parameters[i].endswith('-S')):
            entity_process.append(multiprocessing.Process(target=run_subscriber_shape_main,
                            kwargs={
                                'name_executable':name_executable_sub,
                                'parameters':parameters[i],
                                'produced_code':return_code,
                                'produced_code_index':i,
                                'samples_sent':samples_sent,
                                'verbosity':verbosity,
                                'timeout':timeout,
                                'file':temporary_file[i],
                                'subscriber_finished':subscribers_finished[num_subscribers],
                                'publishers_finished':publishers_finished,
                                'check_function':check_function
            }))
            num_subscribers += 1
            entity_type.append(f'Subscriber_{num_subscribers}')
        else:
            print('Error in the definition of shape_main application parameters. \
                Neither Publisher or Subscriber defined.')
            return

        entity_process[i].start()

    for element in entity_process:
        element.join()     # Wait until the processes finish

    log_message('Reading shape_main application console output from \
                temporary files',
                verbosity)
    for element in temporary_file:
        element.seek(0)
        shape_main_application_output.append(element.read())

    # create an attribute for each entity that will contain their parameters
    for i in range(0, num_entities):
        junitparser.TestCase.i = junitparser.Attr(entity_type[i])
        test_case.i = parameters[i]

    # code[i] contains publisher/subscriber i shape_main application ReturnCode,
    # If we have 1 Publisher (index 0) and 1 Subscriber (index 1):
    # code[0] will contain entity 0 ReturnCode -> Publisher Return Code
    # code[1] will contain entity 1 ReturnCode -> Subscriber Return Code
    # The order of the entities will depend on the definition of the parameters.
    test_result_correct = True
    for i in range(0, num_entities):
        if expected_codes[i] != return_code[i]: # if any of the ReturnCode does
                                         # not match with the expected
                                         # code there is an error.
            test_result_correct = False

    if test_result_correct:
        print (f'{test_case.name} : Ok')

    else:
        print(f'Error in : {test_case.name}')
        for i in range(0, num_entities):
            print(f'{entity_type[i]} expected code: {expected_codes[i]}; \
                Code found: {return_code[i].name}')

            log_message(f'\nInformation about {entity_type[i]}:\n \
                      {shape_main_application_output[i]} ', verbosity)

            shape_main_application_output_edited.append(
                        shape_main_application_output[i].replace('\n', '<br>'))

        # generate the table for the html code.
        message = '<table> \
                        <tr> \
                            <th/> \
                            <th> Expected Code </th> \
                            <th> Code Produced </th> \
                        </tr> '
        for i in range(num_entities):
            message += '<tr> \
                            <th> ' + entity_type[i] + ' </th> \
                            <th> ' + expected_codes[i].name + '</th>  \
                            <th> ' + return_code[i].name + '</th> \
                        </tr>'
        message += '</table>'
        for i in range(0, num_entities):
            message += '<strong> Information ' + entity_type[i] + ' </strong> \
                        <br> ' + shape_main_application_output_edited[i] + '<br>'
        test_case.result = [junitparser.Failure(message)]

    for element in temporary_file:
        element.close()

class Arguments:
    def parser():
        #TODO delete default
        parser = argparse.ArgumentParser(
            description='Validation of interoperability of products compliant \
                with OMG DDS-RTPS standard. This script generates automatically \
                the verification between two shape_main executables. \
                It will generate a xml report in a \
                junit format.',
            add_help=True,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        gen_opts = parser.add_argument_group(title='general options')
        gen_opts.add_argument('-P', '--publisher',
            default=None,
            required=True,
            type=str,
            metavar='publisher_name',
            help='Path to the Publisher shape_main application. \
                It may be absolute or relative path. Example: if the executable \
                is in the same folder as the script: \
                "-P ./rti_connext_dds-6.1.1_shape_main_linux"')
        gen_opts.add_argument('-S', '--subscriber',
            default=None,
            required=True,
            type=str,
            metavar='subscriber_name',
            help='Path to the Subscriber shape_main application. \
                It may be absolute or relative path. Example: if the executable \
                is in the same folder as the script: \
                "-P ./rti_connext_dds-6.1.1_shape_main_linux"')

        optional = parser.add_argument_group(title='optional parameters')
        optional.add_argument('-v','--verbose',
            default=False,
            required=False,
            action='store_true',
            help='Print debug information to stdout. This option also shows the \
                shape_main application output in case of error. \
                If this option is not used, only the test results is printed \
                in the stdout.')

        tests = parser.add_argument_group(title='Test Case and Test Suite')
        tests.add_argument('-s', '--suite',
            nargs='+',
            default=['test_suite'],
            required=False,
            metavar='test_suite_dictionary_file',
            type=str,
            help='Test Suite that is going to be tested. \
                Test Suite is a file with a Python dictionary defined. It should \
                be located on the same directory as interoperability_report. \
                This value should not contain the extension ".py", \
                only the name of the file. \
                It will run all the dictionaries defined in the file. \
                Multiple files can be passed.')

        enable_disable = tests.add_mutually_exclusive_group(required=False)
        enable_disable.add_argument('-t', '--test',
            nargs='+',
            default=None,
            required=False,
            type=str,
            metavar='test_cases',
            help='Test Case that the script will run. By default it will \
                run all the Test Cases contained in the Test Suite. \
                This options is not supported with --disable_test.')
        enable_disable.add_argument('-d', '--disable_test',
            nargs='+',
            default=None,
            required=False,
            type=str,
            metavar='test_cases_disabled',
            help='Test Case that the script will skip. By default it will \
                run all the Test Cases contained in the Test Suite. \
                This option is not supported with --test.')

        out_opts = parser.add_argument_group(title='output options')
        out_opts.add_argument('-o', '--output-name',
            required=False,
            metavar='filename',
            type=str,
            help='Name of the xml report that will be generated. \
                By default the report name will be: \
                    <publisher_name>-<subscriber_name>-date.xml \
                If the file passed already exists, it will add \
                the new results to it. In other case it will create \
                a new file.')

        return parser

# this function checks if the test cases exist in the test suite
def check_test_case_in_test_suite(test_suite, suite_name, test_cases):
    if test_cases != None:
        for i in test_cases:
            if i not in test_suite:
                print('Test Case <'+ i + '> not contained in Test Suite <'
                        +suite_name+'>.')

# this function checks if the test cases disabled exist in the test suite
# and prints a message to show that they are disabled.
def check_disable_test(test_suite, suite_name, test_cases):
    if test_cases != None:
        for i in test_cases:
            if i not in test_suite:
                print('Test Case <'+ i + '> not contained in Test Suite <'
                        +suite_name+'>.')
            else:
                print('Test Case <'+ suite_name + '_'+i + '> disabled.')
def main():
    parser = Arguments.parser()
    args = parser.parse_args()

    options = {
        'publisher': args.publisher,
        'subscriber': args.subscriber,
        'verbosity': args.verbose,
        'test_suite': args.suite,
        'test_cases': args.test,
        'test_cases_disabled': args.disable_test
    }

    # The executables's names are supposed to follow the pattern: name_shape_main
    # We will keep only the part of the name that is useful, deleting the path
    # and the substring '_shape_main'.
    # Example: if the shape_main application's name (including the path) is:
    #  ./srcCxx/objs/x64Linux4gcc7.3.0/rti_connext_dds-6.1.1_shape_main_linux
    # we will take the substring rti_connext_dds-6.1.1.
    # That will be the name that will appear in the report.
    name_publisher = (options['publisher'].split('_shape')[0]).split('/')[-1]
    name_subscriber = (options['subscriber'].split('_shape')[0]).split('/')[-1]

    if args.output_name is None:
        now = datetime.now()
        date_time = now.strftime('%Y%m%d-%H_%M_%S')
        options['filename_report'] = name_publisher+'-'+name_subscriber \
                                    +'-'+date_time+'.xml'
        xml = junitparser.JUnitXml()

    else:
        options['filename_report'] = args.output_name
        file_exists = exists(options['filename_report'])
        if file_exists:
            xml = junitparser.JUnitXml.fromfile(options['filename_report'])
        else:
            xml = junitparser.JUnitXml()

    # TestSuite is a class from junitparser that will contain the
    # results of running different TestCases between two shape_main
    # applications. A TestSuite contains a collection of TestCases.
    suite = junitparser.TestSuite(f"{name_publisher}---{name_subscriber}")

    timeout = 10
    now = datetime.now()

    for element in options['test_suite']:
        t_suite_module = importlib.import_module(element)
        for name, t_suite in inspect.getmembers(t_suite_module):
            # getmembers returns all the members in the t_suite_module.
            # Then, 'type(t_suite) is a dict' takes all the members that
            # are a dictionary. The only one that is not needed (it is not
            # a test_suite) is __builtins__, and it is skipped.
            if type(t_suite) is dict and name != '__builtins__':
                # check that the test_cases selected are in the test_suite and
                # print a message if there are disabled.
                check_test_case_in_test_suite(t_suite, name, options['test_cases'])
                check_disable_test(t_suite, name, options['test_cases_disabled'])

                for k, v in t_suite.items(): # In a dictionary (t_suite) k is
                                             # the key and v is the value
                    # TestCase is a class from junitparser whose attributes
                    # are: name and result (OK, Failure, Error or Skipped).
                    parameters = v[0]
                    expected_codes = v[1]
                    if len(v) == 3:
                        check_function = v[2]
                    elif len(v) == 2:
                        check_function = no_check
                    else:
                        print('Error in the definition of the Test Suite. \
                                Number of arguments incorrect.')
                        break
                    assert(len(parameters) == len(expected_codes))
                    if (options['test_cases'] == None or k in options['test_cases']) \
                        and \
                       (options['test_cases_disabled'] == None
                            or k not in options['test_cases_disabled']):
                        case = junitparser.TestCase(f'{name}_{k}')
                        now_test_case = datetime.now()
                        run_test(name_executable_pub=options['publisher'],
                                name_executable_sub=options['subscriber'],
                                test_case=case,
                                parameters=parameters,
                                expected_codes=expected_codes,
                                verbosity=options['verbosity'],
                                timeout=timeout,
                                check_function=check_function)
                        case.time = (datetime.now() - now_test_case).total_seconds()
                        suite.add_testcase(case)

    suite.time = (datetime.now() - now).total_seconds()
    xml.add_testsuite(suite)

    xml.write(options['filename_report'])

if __name__ == '__main__':
    main()
