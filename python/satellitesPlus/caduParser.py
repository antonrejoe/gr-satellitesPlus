import numpy
from gnuradio import gr
import pmt
from construct import *

PrimaryHeader = BitStruct('fsw' / BitsInteger(24) ,
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
                          'frame_error_control_field_data' / BitsInteger(16),
                          'ccsds_version' / BitsInteger(3),
                          'packet_type' / BitsInteger(1),
                          'secondary_header_flag' / Flag,
                          'AP_ID' / BitsInteger(11),
                          'grouping_flags' / BitsInteger(2),
                          'packet_sequence_count' / BitsInteger(14),
                          'packet_data_length' / BitsInteger(16),
                          'packet_sec_header' / BitsInteger(8))

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
                          'frame_error_control_field_data' / BitsInteger(16),
                          'ccsds_version' / BitsInteger(3),
                          'packet_type' / BitsInteger(1),
                          'secondary_header_flag' / Flag,
                          'AP_ID' / BitsInteger(11),
                          'grouping_flags' / BitsInteger(2),
                          'packet_sequence_count' / BitsInteger(14),
                          'packet_data_length' / BitsInteger(16),
                          'packet_sec_header' / BitsInteger(8))

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

FullPacket = Struct('primary' /  PrimaryHeader,
                    'payload' / Byte[this._.size],
                    'ocftrailer' / If(this.primary.ocf_flag == 1, OCFTrailer))

FullPacket_asm = Struct('primary' /  PrimaryHeader_asm,
                    'payload' / Byte[this._.size],
                    'ocftrailer' / If(this.primary.ocf_flag == 1, OCFTrailer))





class caduParser(gr.basic_block):
    """
    tag_selection = [ asm , fsw]

    1 => true 
    0 => false        

e
    """
    def __init__(self , tag_selection=None):
        gr.basic_block.__init__(self,
            name="CADU_Parser",
            in_sig=[],
            out_sig=[])

        self.tag_selection = tag_selection

        self.message_port_register_in(pmt.intern('in'))
        self.set_msg_handler(pmt.intern('in'), self.handle_msg)
        self.message_port_register_out(pmt.intern('out'))

    def handle_msg(self, msg_pmt):
        msg = pmt.cdr(msg_pmt)
        if not pmt.is_u8vector(msg):
            print("[ERROR] Received invalid message type. Expected u8vector")
            return
        packet = bytearray(pmt.u8vector_elements(msg))
        size = len(packet) - 26 

        if self.tag_selection == 0  :

            try:
                header = PrimaryHeader_asm.parse(packet[:])
                if header.ocf_flag == 1:
                    size -= 4
                data = FullPacket_asm.parse(packet[:], size=size)
            except:
                print("Could not decode telemetry packet")
                return
            print(data)
        elif self.tag_selection == 1 :
            try:
                header = PrimaryHeader.parse(packet[:])
                if header.ocf_flag == 1:
                    size -= 4
                data = FullPacket.parse(packet[:], size=size)
            except:
                print("Could not decode telemetry packet")
                return
            print(data)

        self.message_port_pub(pmt.intern('out'), msg_pmt)
