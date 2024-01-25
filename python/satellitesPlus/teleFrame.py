import numpy
from gnuradio import gr
import pmt
import array
from construct import *

PrimaryHeader = BitStruct('fsw' / BitsInteger(24),
			  'transfer_frame_version_number' / BitsInteger(2),
                          'spacecraft_id' / BitsInteger(10),
                          'virtual_channel_id' / BitsInteger(3),
                          'ocf_flag' / Flag,
                          'master_channel_frame_count' / BitsInteger(8),
                          'virtual_channel_frame_count' / BitsInteger(8),
                          'transfer_frame_secondary_header_flag' / Flag,
                          'synch_flag' / Flag,
                          'packet_order_flag' / Flag,
                          'segment_length_id' / BitsInteger(2),
                          'first_header_pointer' / BitsInteger(11),
                          'secondary_header_versio_no' / BitsInteger(2),
                          'secondary_header_length' / BitsInteger(6),
                          'secondary_header_data' / BitsInteger(8),
                          'spacecraft_application_data' / BitsInteger(8),
                          'ocf_data' / BitsInteger(32),
                          'frame_error_control_field_data' / BitsInteger(16))

PrimaryHeader_asm = BitStruct('asm' / BitsInteger(32),
			  'transfer_frame_version_number' / BitsInteger(2),
                          'spacecraft_id' / BitsInteger(10),
                          'virtual_channel_id' / BitsInteger(3),
                          'ocf_flag' / Flag,
                          'master_channel_frame_count' / BitsInteger(8),
                          'virtual_channel_frame_count' / BitsInteger(8),
                          'transfer_frame_secondary_header_flag' / Flag,
                          'synch_flag' / Flag,
                          'packet_order_flag' / Flag,
                          'segment_length_id' / BitsInteger(2),
                          'first_header_pointer' / BitsInteger(11),
                          'secondary_header_versio_no' / BitsInteger(2),
                          'secondary_header_length' / BitsInteger(6),
                          'secondary_header_data' / BitsInteger(8),
                          'spacecraft_application_data' / BitsInteger(8),
                          'ocf_data' / BitsInteger(32),
                          'frame_error_control_field_data' / BitsInteger(16))
OCFTrailer = BitStruct('control_word_type' / Flag,
                       'clcw_version_number' / BitsInteger(2),
                       'status_field' / BitsInteger(3),
                       'cop_in_effect' / BitsInteger(2),
                       'virtual_channel_identification' / BitsInteger(6),
                       'rsvd_spare1' / BitsInteger(2),
                       'no_rf_avail' / Flag,
                       'no_bit_lock' / Flag,
                       'lockout' / Flag,
                       'wait' / Flag,
                       'retransmit' / Flag,
                       'farmb_counter' / BitsInteger(2),
                       'rsvd_spare2' / Flag,
                       'report_value' / BitsInteger(8))

FullPacket = Struct('primary' / PrimaryHeader,
                    'payload' / Byte[this._.size],
                    'ocftrailer' / If(this.primary.ocf_flag == 1, OCFTrailer))


class teleFrame(gr.basic_block):
    """ 
    This Telemetry primary header uses fsw (frame sync word)

    Note:
    num_of_octets => value can't exceed 109 

    if done , 
        the block assumes the de
fault value of 109 
    """ 
    # tag_selection => tag_selection[0] -> asm , tag_selection[1] -> fsw

    def __init__(self, choice=0, asm=0, fsw= 0, transfer_frame_version_number=0, spacecraft_id=0, virtual_channel_id=0, ocf_flag=0,  master_channel_frame_count=0,
                 virtual_channel_frame_count=0, transfer_frame_secondary_header_flag=0, synch_flag=0, packet_order_flag=0, segment_length_id=0,
                 first_header_pointer=0, secondary_header_versio_no =0,secondary_header_length=0,secondary_header_data=0, spacecraft_application_data=0,ocf_data=0,frame_error_control_field_data=0, num_of_octets=0):
        gr.basic_block.__init__(self,
            name="Transfer frame header",
            in_sig=[],
            out_sig=[])

        ##################################################
        # Parameters
        ##################################################
        num_of_octets += 1
        self.fsw= fsw 
        self.asm = asm
        self.transfer_frame_version_number = 0
        self.spacecraft_id = spacecraft_id
        self.virtual_channel_id = virtual_channel_id
        self.ocf_flag = ocf_flag
        self.master_channel_frame_count = master_channel_frame_count
        self.virtual_channel_frame_count = virtual_channel_frame_count
        self.transfer_frame_secondary_header_flag = transfer_frame_secondary_header_flag
        self.synch_flag = synch_flag
        self.packet_order_flag = packet_order_flag
        self.segment_length_id = segment_length_id
        self.first_header_pointer = 0

        self.secondary_header_versio_no = secondary_header_versio_no
        self.secondary_header_length = secondary_header_length
        self.secondary_header_data = secondary_header_data
        self.spacecraft_application_data = spacecraft_application_data
        self.ocf_data = ocf_data
        self.frame_error_control_field_data = frame_error_control_field_data

    
        self.choice= choice 
        self.num_of_octets = num_of_octets
        self.list = []
        # comment this if you use the 109 condition
        # self.size = self.num_of_octets
        ##################################################
        # Variables
        ##################################################
        #Logic for 128 bytes restriction (by controlling the value of size)
        if self.choice == 1:
            if self.num_of_octets > 109 :
                self.size = 110 
            else: 
                self.size = self.num_of_octets
        else :
            self.size = self.num_of_octets
        ##################################################
        # Blocks
        ##################################################
        self.message_port_register_in(pmt.intern('in'))
        self.set_msg_handler(pmt.intern('in'), self.handle_msg)
        self.message_port_register_out(pmt.intern('out'))

    def handle_msg(self, msg_pmt):
        msg = pmt.cdr(msg_pmt)
        if not pmt.is_u8vector(msg):
            print("[ERROR] Received invalid message type. Expected u8vector")
            return
        packet = pmt.u8vector_elements(msg)

        next_pointer = 0

        while len(packet) > 0:
            limit = self.size - len(self.list) 


            if len(packet) > limit:
                if len(packet) >= limit + self.size:
                    next_pointer = 0x7ff
                else:
                    next_pointer = len(packet) - limit
            elif len(packet) == limit:
                next_pointer = 0

            self.list.extend(packet[:limit])
            packet = packet[limit:]

            if len(self.list) == self.size:
                finalPacket = numpy.append(self.calculateFinalHeader(), self.list)
                self.sendPacket(finalPacket)
                self.list = []
                self.frame_error_control_field_data = next_pointer

    def sendPacket(self, packet):
        packet = array.array('B', packet[:])
        packet = pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(packet), packet))
        self.message_port_pub(pmt.intern('out'), packet)


    def calculateFinalHeader(self):

        if self.choice == 1 :
            finalHeader = array.array('B', PrimaryHeader.build(dict(fsw=self.fsw,

                                                                            transfer_frame_version_number = self.transfer_frame_version_number,
                                                                            spacecraft_id = self.spacecraft_id,
                                                                            virtual_channel_id = self.virtual_channel_id,
                                                                            ocf_flag = self.ocf_flag,
                                                                            master_channel_frame_count = self.master_channel_frame_count,
                                                                            virtual_channel_frame_count = self.virtual_channel_frame_count,
                                                                            transfer_frame_secondary_header_flag = self.transfer_frame_secondary_header_flag,
                                                                            synch_flag = self.synch_flag,
                                                                            packet_order_flag = self.packet_order_flag,
                                                                            segment_length_id = self.segment_length_id,
                                                                            first_header_pointer = self.first_header_pointer,
                                                                            secondary_header_versio_no = self.secondary_header_versio_no,
                                                                            secondary_header_length = self.secondary_header_length,
                                                                            secondary_header_data = self.secondary_header_data,
                                                                            spacecraft_application_data = self.spacecraft_application_data,
                                                                            ocf_data = self.ocf_data,
                                                                            frame_error_control_field_data = self.frame_error_control_field_data)))
            return finalHeader
        elif self.choice == 0 :
            finalHeader = array.array('B', PrimaryHeader_asm.build(dict(asm=self.asm,
                                                                            transfer_frame_version_number = self.transfer_frame_version_number,
                                                                            spacecraft_id = self.spacecraft_id,
                                                                            virtual_channel_id = self.virtual_channel_id,
                                                                            ocf_flag = self.ocf_flag,
                                                                            master_channel_frame_count = self.master_channel_frame_count,
                                                                            virtual_channel_frame_count = self.virtual_channel_frame_count,
                                                                            transfer_frame_secondary_header_flag = self.transfer_frame_secondary_header_flag,
                                                                            synch_flag = self.synch_flag,
                                                                            packet_order_flag = self.packet_order_flag,
                                                                            segment_length_id = self.segment_length_id,
                                                                            first_header_pointer = self.first_header_pointer,
                                                                            secondary_header_versio_no = self.secondary_header_versio_no,
                                                                            secondary_header_length = self.secondary_header_length,
                                                                            secondary_header_data = self.secondary_header_data,
                                                                            spacecraft_application_data = self.spacecraft_application_data,
                                                                            ocf_data = self.ocf_data,
                                                                            frame_error_control_field_data = self.frame_error_control_field_data)))
            return finalHeader
        else:
            print("\n Selet between FSW and ASM \n")
