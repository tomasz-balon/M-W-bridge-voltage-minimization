import serial
import struct
import sys
import threading
import time

from config import BridgeConstants, ReaderConstants, Results


class CommunicationHandler:
    """
    Class handling serial communication - reading and writing message
    """
    def __init__(self):
        self.serial_port = serial.Serial(port=ReaderConstants.COM_PORT,
                                         baudrate=ReaderConstants.BAUD_RATE)

    def send_message(self, message: bytes) -> None:
        """
        Send message compliant to the protocol
        :param: message (bytes) message to be sent
        :return: None
        """
        self.serial_port.write(message)

    def wait_for_message(self) -> None:
        """
        Wait for received information
        :return: None
        """
        while True:
            self.serial_port.reset_input_buffer()
            while self.serial_port.in_waiting == 0:
                pass
            else:
                break

    def handle_message(self, message: bytes) -> float:
        """
        Handle incoming message
        :param: message (bytes)
        :return: response from other module
        :rtype: float
        """
        self.serial_port.reset_output_buffer()
        self.send_message(message)
        self.wait_for_message()
        response = self.serial_port.read(size=4)
        return struct.unpack('!f', response)[0]

    def first_run(self, channel: str) -> str:
        """
        Function to check if algorithm should subtract or add step
        :param: channel (str) chosen channel
        :return: operation
        :rtype: str
        """
        pwm_name = ReaderConstants.CHANNEL_PWM_DICT[channel][0]
        position_low = Results.RESULTS[pwm_name] - ReaderConstants.STEP
        position_mid = Results.RESULTS[pwm_name]
        position_high = Results.RESULTS[pwm_name] + ReaderConstants.STEP
        message = self.create_message(pwm_name, position_low)
        self.send_message(message)
        self.wait_for_message()
        low = self.serial_port.read_until().decode('utf-8')
        message = self.create_message(pwm_name, position_mid)
        self.send_message(message)
        self.wait_for_message()
        mid = self.serial_port.read_until().decode('utf-8')
        message = self.create_message(pwm_name, position_high)
        self.send_message(message)
        self.wait_for_message()
        high = self.serial_port.read_until().decode('utf-8')
        if low < mid < high:
            operation = 'subtract'
        else:
            operation = 'add'
        return operation

    @staticmethod
    def create_message(pwm: str, position: int) -> bytes:
        """
        Create an output message from passed arguments
        :param: pwm (str) chosen channel from A to H (corresponding to 1-8 values)
        :param: position (int) position to be set
        :return: merged message
        :rtype: bytes
        """
        message = b'%s%d%s' % (pwm.encode('utf-8'), position, ReaderConstants.NEWLINE_B)
        return message

    @staticmethod
    def parse_message(message: bytes) -> int:
        """
        Read message and save PWM value to variable in dict
        :param: message (bytes)
        :return: parsed pwm value
        :rtype: int
        """
        tmp_msg = [*message]
        channel = tmp_msg[0]
        pwm_value = int(''.join(tmp_msg[1:5]))
        Results.PWM_VALUES[channel] = pwm_value
        return pwm_value

    def close_connection(self) -> None:
        """
        Close serial port connection
        :return: None
        """
        self.serial_port.close()


class ThreadHandler:
    """
    Class handling threads - creating and running them
    """
    def __init__(self):
        self.thread_comm = CommunicationHandler()
        t = threading.Thread(target=self.thread_function())
        t.start()

    def thread_function(self) -> None:
        """
        Compensate voltage on all channels every 2 minutes, run as a thread
        :return: None
        """
        for channel in ReaderConstants.CHANNELS_LIST:
            message = b'%s%s' % (ReaderConstants.GET_VOLTAGE_MSG, channel.encode('utf-8'))
            self.thread_comm.send_message(message)
            self.thread_comm.handle_message(channel)
        ReaderConstants.IF_START = False
        time.sleep(2 * ReaderConstants.MIN)


class CompensationHandler:
    """
    Class handling compensation of received voltage
    """
    def __init__(self, communication_handler: CommunicationHandler):
        self.comm = communication_handler
        self.pwm_left = ReaderConstants.CHANNEL_PWM_DICT[ReaderConstants.CHOSEN_CHANNEL][0]
        self.pwm_right = ReaderConstants.CHANNEL_PWM_DICT[ReaderConstants.CHOSEN_CHANNEL][1]

    def setup(self) -> float:
        """
        Set potentiometers in initial position and read voltage
        :return: voltage
        :rtype: float
        """
        initial_pwm = int((BridgeConstants.PWM_MIN + BridgeConstants.PWM_MAX) / 2)
        BridgeConstants.PREV_PWM1 = initial_pwm
        BridgeConstants.PREV_PWM2 = initial_pwm
        msg = self.comm.create_message(self.pwm_left, initial_pwm)
        self.comm.send_message(msg)
        self.comm.wait_for_message()
        msg = self.comm.create_message(self.pwm_right, initial_pwm)
        self.comm.send_message(msg)
        self.comm.wait_for_message()
        response = self.comm.serial_port.read(size=4)
        return struct.unpack('!f', response)[0]

    def compensate(self) -> None:
        """
        Compensate (find minimum) algorithm
        :return: None
        """
        voltage = self.setup()
        while True:
            while voltage < ReaderConstants.VOLTAGE:
                ReaderConstants.VOLTAGE = self.comm.handle_message(b'v\n')

                prev_pwm1 = BridgeConstants.PREV_PWM1
                msg = self.comm.create_message(self.pwm_left, prev_pwm1)
                mid1 = self.comm.handle_message(msg)

                low_pwm1 = prev_pwm1 - ReaderConstants.STEP1
                if low_pwm1 < BridgeConstants.PWM_MIN:
                    low_pwm1 = BridgeConstants.PWM_MIN
                msg = self.comm.create_message(self.pwm_left, low_pwm1)
                low1 = self.comm.handle_message(msg)

                high_pwm1 = prev_pwm1 + ReaderConstants.STEP1
                if high_pwm1 > BridgeConstants.PWM_MAX:
                    high_pwm1 = BridgeConstants.PWM_MAX
                msg = self.comm.create_message(self.pwm_left, high_pwm1)
                high1 = self.comm.handle_message(msg)

                tmp1 = (low1, mid1, high1)
                if min(tmp1) == low1:
                    BridgeConstants.PREV_PWM1 = low_pwm1
                elif min(tmp1) == mid1:
                    ReaderConstants.STEP1 = ReaderConstants.STEP1 / ReaderConstants.DIVIDER
                    if ReaderConstants.STEP1 < 1:
                        ReaderConstants.STEP1 = 1
                    BridgeConstants.PREV_PWM1 = prev_pwm1
                else:
                    BridgeConstants.PREV_PWM1 = high_pwm1
                msg = self.comm.create_message(self.pwm_left, BridgeConstants.PREV_PWM1)
                dummy = self.comm.handle_message(msg)

                prev_pwm2 = BridgeConstants.PREV_PWM2
                msg = self.comm.create_message(self.pwm_right, prev_pwm2)
                mid2 = self.comm.handle_message(msg)

                low_pwm2 = prev_pwm1 - ReaderConstants.STEP1
                if low_pwm2 < BridgeConstants.PWM_MIN:
                    low_pwm2 = BridgeConstants.PWM_MIN
                msg = self.comm.create_message(self.pwm_right, low_pwm2)
                low2 = self.comm.handle_message(msg)

                high_pwm2 = prev_pwm1 + ReaderConstants.STEP1
                if high_pwm2 > BridgeConstants.PWM_MAX:
                    high_pwm2 = BridgeConstants.PWM_MAX
                msg = self.comm.create_message(self.pwm_right, high_pwm2)
                high2 = self.comm.handle_message(msg)

                tmp2 = (low2, mid2, high2)
                if min(tmp2) == low2:
                    BridgeConstants.PREV_PWM2 = low_pwm2
                elif min(tmp2) == mid2:
                    ReaderConstants.STEP2 = ReaderConstants.STEP2 / ReaderConstants.DIVIDER
                    if ReaderConstants.STEP2 < 1:
                        ReaderConstants.STEP2 = 1
                    BridgeConstants.PREV_PWM2 = prev_pwm2
                else:
                    BridgeConstants.PREV_PWM2 = high_pwm2
                msg = self.comm.create_message(self.pwm_right, BridgeConstants.PREV_PWM2)
                dummy = self.comm.handle_message(msg)

                voltage = self.comm.handle_message(b'v\n')
                print(f'{voltage}')

            self.teardown(voltage, BridgeConstants.PREV_PWM1, BridgeConstants.PREV_PWM2)

    def teardown(self, voltage: float, pwm1: int, pwm2: int) -> None:
        """
        Print final values, close communication and exit script
        """
        print(f'Final voltage: [{voltage}][V]')
        print(f'PWM channel {self.pwm_left}: [{pwm1}]')
        print(f'PWM channel {self.pwm_right}: [{pwm2}]')
        self.comm.send_message(b'q\n')
        self.comm.close_connection()
        sys.exit()


if __name__ == '__main__':
    comm_handler = CommunicationHandler()
    comp_handler = CompensationHandler(comm_handler)
    comp_handler.compensate()
