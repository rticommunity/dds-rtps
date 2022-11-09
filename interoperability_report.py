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


def subscriber(name_executable, parameters, time_out, code, data, event,
                check_order=False, check_color=False, check_strength=False):
    """ Run the executable with the parameters and save the error code obtained

        name_executable : name of the executable to run as a Subscriber
        parameters : QOS to use
        time_out : time pexpect will wait until it finds a pattern
        code : this variable will be overwritten with the obtained ErrorCode
        data : this variable will be overwritten with the obtained data

        The function will run the executable with the Qos as a Subscriber.
        It will follow the next steps until it does not find the pattern 
        and it will save the ErrorCode found:
            * Wait until the topic is created
            * Wait until the reader is created
            * Wait until the reader matchs with a writer
            * Wait until the reader detects the writer as alive
            * Wait until the reader receives data

        If at a each point the step is not achieved succesfully, 
        the function will stop and the ErrorCode will be saved.
    
    """

    # Step 1 : run the executable
    child_sub = pexpect.spawn('%s -S %s' % (name_executable, parameters))

    #child_sub.logfile = sys.stdout

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
            # Step 4 : Check if the reader matchs the writer
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
                        
                        if check_color:
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


#opcion -debug a un fichero de texto o -verbose
def publisher(name_executable, parameters, time_out, code, data, id_pub, event,
                check_order=False, check_color=False, check_strength=False):
    """ Run the executable with the parameters and save the error code obtained

        name_executable : name of the executable to run as a Publisher
        parameters : QOS to use
        time_out : time pexpect will wait until it finds a pattern
        code : this variable will be overwritten with the obtained ErrorCode
        data : this variable will be overwritten with the obtained data

        The function will run the executable with the Qos as a Publisher.
        It will follow the next steps until it does not find the pattern 
        and it will save the ErrorCode found:
            * Wait until the topic is created
            * Wait until the writer is created
            * Wait until the writer matchs with a reader
            * Wait until the writer sends data

        If at a each point the step is not achieved succesfully, 
        the function will stop and the ErrorCode will be saved.
    
    """
    
    # Step 1 : run the executable
    child_pub = pexpect.spawn('%s -P %s'% (name_executable, parameters))
    #child_pub.logfile = sys.stdout

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
            # Step 4 : Check if the writer matchs the readers
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

# mirar si poner las descripciones con will o con que

def run_test(key, param_pub, param_sub, 
                expected_code_pub, expected_code_sub, 
                time_out=20, check_order=False, check_color=False, 
                check_strength=False):
    """ Run the Publisher and the Subscriber and check the ErrorCode

        expected_code_pub : Errorcode the Publisher will obtain if 
                        everything goes as expected
        expected_code_sub : Errorcode the Subscriber will obtain if 
                        everything goes as expected
        param_pub : qos for the Publisher
        param_sub : qos for the Subscriber
        time_out : timeout for pexpect # should be optional

        The funcion will run in two different Processes
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
                    args=[name_executable, param_pub, time_out, code, data,1, event,
                    check_order])
    sub = Process(target=subscriber, 
                    args=[name_executable, param_sub, time_out, code, data, event,
                    check_order])
    sub.start()
    pub.start()
    sub.join()
    pub.join()

    if expected_code_pub ==  code[1] and expected_code_sub == code[0]:
        print ('ok')
    else:
        print('Pub expected code: %s; Code found: %s' % (expected_code_pub, code[1]))
        print('Sub expected code: %s; Code found: %s' % (expected_code_sub, code[0]))
    print('Test: %s' % (key))



def run_test_pub_pub_sub(key, param_pub1, param_pub2, param_sub, expected_code_pub1, 
                        expected_code_pub2, expected_code_sub, time_out, 
                        check_order=False, check_color=False, check_strength=False):
    name_executable = '/home/carias/shape_main/dds-rtps/srcCxx/objs/x64Linux4gcc7.3.0/rti_connext_dds-6.1.1_shape_main_linux '
    manager = multiprocessing.Manager()
    code = manager.list(range(3))
    data = Queue()
    event = multiprocessing.Event()
   
    if key == "Ownership_03":
        pub1 = Process(target=publisher, 
                        args=[name_executable, param_pub1, time_out, code, data,
                        1, event, False, True, False])
        pub2 = Process(target=publisher, 
                        args=[name_executable, param_pub2, time_out, code, data,
                        2, event, False, True, False])                
        sub = Process(target=subscriber, 
                        args=[name_executable, param_sub, time_out, code, data, event,
                        False, True, False])
    if key == "Ownership_04":
        pub1 = Process(target=publisher, 
                        args=[name_executable, param_pub1, time_out, code, Queue(),
                        1, event,False, False, True])
        pub2 = Process(target=publisher, 
                        args=[name_executable, param_pub2, time_out, code, data,
                        2, event, False, False, True])                
        sub = Process(target=subscriber, 
                        args=[name_executable, param_sub, time_out, code, data, event,
                        False, False, True])
    sub.start()
    pub1.start()
    time.sleep(1)
    pub2.start()
    
    
    sub.join()
    pub1.join()
    pub2.join()

    if expected_code_pub1 ==  code[1] and expected_code_sub == code[0] \
        and expected_code_pub2 == code[2]:
        print ('ok')
    else:
        print('Pub1 expected code: %s; Code found: %s' % (expected_code_pub1, code[1]))
        print('Pub2 expected code: %s; Code found: %s' % (expected_code_pub2, code[2]))
        print('Sub expected code: %s; Code found: %s' % (expected_code_sub, code[0]))
    print('Test: %s ' % (key))


short_timeout = 5
long_timeout = 20

#lista o fichero con parametros y codigo que esperamos (mirar struct)

# importar desde otro fichero
# anadir test antes de cada nombre
# quitar el primer cero
dict_param_expected_code_timeout = {
    # DOMAIN
    "Domain_00" :
        ['-t Square', '-t Square', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout], 
    "Domain_01" :
        ['-t Square', '-t Square -d 1', 
                ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED, 
                short_timeout],
    "Domain_02":
        ['-t Square -d 1', '-t Square', 
                ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED,  
                short_timeout],
    "Domain_03":
        ['-t Square -d 1', '-t Square -d 1', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],

    # RELIABILITY
    "Reliability_00":
        ['-t Square -b', '-t Square -b', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Reliability_01":
        ['-t Square -b', '-t Square -r', 
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS,  
                short_timeout],
    "Reliability_02":
        ['-t Square -r', '-t Square -b', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Reliability_03":
    # reliable, but we only check that they exchange data       
        ['-t Square -r -k 3', '-t Square -r', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],

    # DEADLINE
    "Deadline_00":
        ['-t Square -f 3', '-t Square -f 5', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Deadline_01":
        ['-t Square -f 5', '-t Square -f 5', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Deadline_02":
        ['-t Square -f 7', '-t Square -f 5', 
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS,  
                short_timeout],
    
    # OWNERSHIP
    "Ownership_00":
        ['-t Square -s -1', '-t Square -s -1', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Ownership_01":
        ['-t Square -s -1', '-t Square -s 3', 
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, 
                short_timeout],
    "Ownership_02":
        ['-t Square -s 3', '-t Square -s -1', 
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, 
                short_timeout],
    "Ownership_03":
        ['-t Square -s 3 -c BLUE', '-t Square -s 4 -c RED',
                    '-t Square -s 2 -r -k 3', 
                ErrorCode.OK, ErrorCode.OK, ErrorCode.RECEIVING_FROM_BOTH, 
                long_timeout],

    # TOPIC
    "Topic_00":
        ['-t Square', '-t Square', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Topic_01":
        ['-t Square', '-t Circle', 
                ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED,  
                short_timeout],
    "Topic_02":
        ['-t Circle', '-t Square', 
                ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED,
                short_timeout],
    "Topic_03":
        ['-t Circle', '-t Circle', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],

    # COLOR
    "Color_00":
        ['-t Square -c BLUE', '-t Square -c BLUE', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Color_01":
        ['-t Square -c BLUE', '-t Square -c RED', 
                ErrorCode.OK, ErrorCode.DATA_NOT_RECEIVED,  
                short_timeout],
    "Color_02":
        ['-t Square -c BLUE', '-t Square', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Color_03":
        ['-t Square -c RED', '-t Square -c BLUE', 
                ErrorCode.OK, ErrorCode.DATA_NOT_RECEIVED,  
                short_timeout],
    "Color_04":
        ['-t Square -c RED', '-t Square -c RED', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Color_05":
        ['-t Square -c RED', '-t Square', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Color_06":
        ['-t Square', '-t Square -c BLUE', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Color_07":
        ['-t Square', '-t Square -c RED', 
                ErrorCode.OK, ErrorCode.DATA_NOT_RECEIVED,  
                short_timeout],
    "Color_08":
        ['-t Square', '-t Square', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],

    # PARTITION
    "Partition_00":
        ['-t Square -p "p1"', '-t Square -p "p1"', 
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Partition_01":
        ['-t Square -p "p1"', '-t Square -p "p2"',  
                ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED, 
                short_timeout],
    "Partition_02":
        ['-t Square -p "p2"', '-t Square -p "p1"', 
                ErrorCode.READER_NOT_MATCHED, ErrorCode.WRITER_NOT_MATCHED,  
                short_timeout],
    "Partition_03":
        ['-t Square -p "p2"', '-t Square -p "p2"',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],

    # DURABILITY
    "Durability_00":
        [ '-t Square -D v', '-t Square -D v', 
                ErrorCode.OK, ErrorCode.OK, 
                long_timeout],
    "Durability_01":
        ['-t Square -D v', '-t Square -D l', 
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS,  
                short_timeout],
    "Durability_02":
        ['-t Square -D v', '-t Square -D t', 
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS,  
                short_timeout],
    "Durability_03":
        ['-t Square -D v', '-t Square -D p', 
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS,  
                short_timeout],

    "Durability_10":
        [ '-t Square -D l', '-t Square -D v',
                ErrorCode.OK, ErrorCode.OK, 
                long_timeout],
    "Durability_11":
        ['-t Square -D l', '-t Square -D l',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Durability_12":
        ['-t Square -D l', '-t Square -D t',
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS,  
                short_timeout],
    "Durability_13":
        ['-t Square -D l', '-t Square -D p',
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS,  
                short_timeout],

    "Durability_20":
        ['-t Square -D t', '-t Square -D v',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Durability_21":
        ['-t Square -D t', '-t Square -D l',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Durability_22":
        ['-t Square -D t', '-t Square -D t',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Durability_23":
        ['-t Square -D t', '-t Square -D p',
                ErrorCode.INCOMPATIBLE_QOS, ErrorCode.INCOMPATIBLE_QOS, 
                short_timeout],

    "Durability_30":
        ['-t Square -D p', '-t Square -D v',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Durability_31":
        ['-t Square -D p', '-t Square -D l',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Durability_32":
        ['-t Square -D p', '-t Square -D t',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],
    "Durability_33":
        ['-t Square -D p', '-t Square -D p',
                ErrorCode.OK, ErrorCode.OK,  
                long_timeout],

    # HISTORY
    "History_00":
    [ '-t Square -k 3', '-t Square -k 3',
            ErrorCode.OK, ErrorCode.OK, 
            long_timeout],
    "History_01":
    ['-t Square -k 3', '-t Square -k 0',
            ErrorCode.OK, ErrorCode.OK,  
            long_timeout],
    "History_02":
    ['-t Square -k 0', '-t Square -k 3',
            ErrorCode.OK, ErrorCode.OK,  
            long_timeout],
    "History_03":
    ['-t Square -k 0', '-t Square -k 0',
            ErrorCode.OK, ErrorCode.OK,  
            long_timeout],
}

def main():
    for k, v in dict_param_expected_code_timeout.items():
        # change this so time_out can be optional
        if k == "Ownership_03":
            run_test_pub_pub_sub(k, v[0], v[1], v[2],v[3], v[4], v[5], v[6], 
            check_color=True)
            continue

        else:
            run_test(k,v[0], v[1], v[2], v[3], v[4])

    

# poner el main en otro fichero (?)
if __name__ == '__main__':
    main()