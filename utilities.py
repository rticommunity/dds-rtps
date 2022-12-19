from enum import Enum

class ReturnCode(Enum):
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

    @classmethod
    def export_to(cls, namespace):
        namespace.update(cls.__members__)


path_executables = {
    'connext611' : '/home/carias/dds-rtps/srcCxx/objs/x64Linux4gcc7.3.0/rti_connext_dds-6.1.1_shape_main_linux',
    'opendds321' : '/home/carias/dds-rtps/srcCxx/objs/x64Linux4gcc7.3.0/shape_main_opendds'
}