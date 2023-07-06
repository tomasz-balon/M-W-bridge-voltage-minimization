import math
import cmath
import struct
import sys

import serial

from config import BridgeConstants, ReaderConstants


class MaxwellWienBridge:
    C: float
    R3: float
    R4: float
    L: float
    frequency: float
    omega: float
    Z1: complex
    Z2: complex
    Z_R2: complex
    Z_C: complex
    Z3: complex
    Z4: complex

    def __init__(self, capacitance, resistance3, resistance4, inductance, frequency):
        self.C = capacitance
        self.R3 = resistance3
        self.R4 = resistance4
        self.L = inductance
        self.frequency = frequency
        self.potentiometer1 = Potentiometer()
        self.potentiometer2 = Potentiometer()

    def calculate_impedance(self) -> None:
        """
        Recalculate impedance
        (Algorithm based on one given during lecture)
        :return: None
        """
        self.omega = 2 * math.pi * self.frequency
        self.Z1 = complex(self.potentiometer1.resistance, 0)
        self.Z2 = complex(self.R3, self.omega * self.L)
        Z_R2 = complex(self.potentiometer2.resistance, 0)
        Z_C = complex(0, (-1 / (self.omega * self.C)))
        self.Z3 = ((Z_R2 * Z_C) / (Z_R2 + Z_C))
        self.Z4 = complex(self.R4, 0)

    def get_voltage(self) -> float:
        """
        Get current input offset voltage of chosen MW Bridge
        :return: input offset voltage
        :rtype: float
        """
        self.calculate_impedance()
        v1 = (BridgeConstants.VOLTAGE * self.Z4) / (self.Z2 + self.Z4)
        v2 = (BridgeConstants.VOLTAGE * self.Z3) / (self.Z1 + self.Z3)
        return cmath.polar(v2 - v1)[0]


class Potentiometer:
    position: int
    resistance: int

    def __init__(self) -> None:
        self.set_position(50)

    def set_position(self, pos: int) -> None:
        """
        Set position of potentiometer given in percents
        :param: pos (int) position to be set
        :return: None
        """
        if pos < 0:
            raise ValueError('Position value too low! Should be in range 0-100')

        elif pos > 100:
            raise ValueError('Position value too high! Should be in range 0-100')
        
        self.position = pos
        self.resistance = ((BridgeConstants.MAX_RESISTANCE - BridgeConstants.MIN_RESISTANCE)
                           * self.position / 100) + BridgeConstants.MIN_RESISTANCE
        
    def get_resistance(self) -> int:
        """
        Get current resistance
        :return: resistance
        :rtype: int
        """
        return self.resistance


class PWM:
    """
    Class to handle PWM of chosen channel
    """
    def __init__(self, bridge: MaxwellWienBridge):
        self.pwm1 = 0
        self.pwm2 = 0
        self.bridge = bridge

    @staticmethod
    def check_pwm(current_pwm: int) -> int:
        """
        Check if pwm is between limits
        :param: current_pwm (int) current PWM value read from channel
        :return: correct PWM value
        :rtype: int
        """
        if current_pwm < BridgeConstants.PWM_MIN:
            new_pwm = BridgeConstants.PWM_MIN
        elif current_pwm > BridgeConstants.PWM_MAX:
            new_pwm = BridgeConstants.PWM_MAX
        else:
            new_pwm = current_pwm
        return new_pwm

    def set_pwm(self, pwm_name: str, pwm_value: int) -> None:
        """
        Set PWM value for chosen channel
        :param: pwm_name (str)
        :param: pwm_value (int)
        :return: None
        """
        new_pwm = self.check_pwm(pwm_value)
        if pwm_name in ReaderConstants.LEFT_PWMS:
            self.pwm1 = new_pwm
            self.bridge.potentiometer1.set_position(self.map_pwm(new_pwm))
        elif pwm_name in ReaderConstants.RIGHT_PWMS:
            self.pwm2 = new_pwm
            self.bridge.potentiometer2.set_position(self.map_pwm(new_pwm))

    @staticmethod
    def map_pwm(pwm_i: int) -> int:
        """
        Map PWM into scale 0-100 for potentiometer
        :param: pwm_i (int)
        :return: pwm in scale 0-100
        :rtype: int
        """
        if pwm_i <= BridgeConstants.PWM_MIN:
            res = 0
        elif pwm_i >= BridgeConstants.PWM_MAX:
            res = 100
        else:
            res = 100 * (pwm_i - BridgeConstants.PWM_MIN) / (BridgeConstants.PWM_MAX - BridgeConstants.PWM_MIN)
        return res


class CompensationHandler:
    """
    Class to handle Compensation algorithm
    """
    def __init__(self, pwm_handle: PWM):
        self.pwm = pwm_handle

    def compensate_voltage(self, channel_name: str) -> None:
        """
        Compensate voltage of chosen channel
        :param: channel_name (str)
        :return: None
        """
        pwm_left = ReaderConstants.CHANNEL_PWM_DICT[channel_name][0]
        pwm_right = ReaderConstants.CHANNEL_PWM_DICT[channel_name][1]
        voltage = self.pwm.bridge.get_voltage()
        while voltage < BridgeConstants.PREV_VOLTAGE:
            BridgeConstants.PREV_VOLTAGE = self.pwm.bridge.get_voltage()

            prev_pwm1 = self.pwm.pwm1
            self.pwm.set_pwm(pwm_left, prev_pwm1)
            mid = self.pwm.bridge.get_voltage()
            self.pwm.set_pwm(pwm_left, prev_pwm1 - ReaderConstants.STEP)
            low = self.pwm.bridge.get_voltage()
            self.pwm.set_pwm(pwm_left, prev_pwm1 + ReaderConstants.STEP)
            high = self.pwm.bridge.get_voltage()
            tmp = (low, mid, high)
            if min(tmp) == low:
                self.pwm.set_pwm(pwm_left, prev_pwm1 - ReaderConstants.STEP)
            elif min(tmp) == mid:
                self.pwm.set_pwm(pwm_left, prev_pwm1)
            else:
                self.pwm.set_pwm(pwm_left, prev_pwm1 + ReaderConstants.STEP)

            prev_pwm2 = self.pwm.pwm2
            self.pwm.set_pwm(pwm_right, prev_pwm2)
            mid = self.pwm.bridge.get_voltage()
            self.pwm.set_pwm(pwm_right, prev_pwm2 - ReaderConstants.STEP)
            low = self.pwm.bridge.get_voltage()
            self.pwm.set_pwm(pwm_right, prev_pwm2 + ReaderConstants.STEP)
            high = self.pwm.bridge.get_voltage()
            tmp = (low, mid, high)
            if min(tmp) == low:
                self.pwm.set_pwm(pwm_right, prev_pwm2 - ReaderConstants.STEP)
            elif min(tmp) == mid:
                self.pwm.set_pwm(pwm_right, prev_pwm2)
            else:
                self.pwm.set_pwm(pwm_right, prev_pwm2 + ReaderConstants.STEP)

            voltage = self.pwm.bridge.get_voltage()


def display_results(channel: str, pwm1: int, pwm1_name: str, pwm2: int, pwm2_name: str, resistance1: int,
                    resistance2: int, voltage: float) -> None:
    print(f'Channel number: [{channel}]')
    print(f'PWM channel {pwm1_name}: [{pwm1}]')
    print(f'PWM channel {pwm2_name}: [{pwm2}]')
    print(f'Resistance channel 1: [{resistance1}]')
    print(f'Resistance channel 2: [{resistance2}]')
    print(f'Voltage: [{voltage}]')


if __name__ == '__main__':
    serial_port = serial.Serial(port=BridgeConstants.COM_PORT, baudrate=BridgeConstants.BAUD_RATE)
    maxwell_bridge = MaxwellWienBridge(
                BridgeConstants.CAPACITANCE,
                BridgeConstants.RESISTANCE3,
                BridgeConstants.RESISTANCE4,
                BridgeConstants.INDUCTANCE,
                BridgeConstants.FREQUENCY)
    pwm_handler = PWM(maxwell_bridge)
    initial_pwm = int((BridgeConstants.PWM_MIN + BridgeConstants.PWM_MAX) / 2)
    chosen_pwms = ReaderConstants.CHANNEL_PWM_DICT[ReaderConstants.CHOSEN_CHANNEL]
    for pwm in chosen_pwms:
        pwm_handler.set_pwm(pwm, initial_pwm)

    while True:
        serial_port.reset_input_buffer()
        while serial_port.in_waiting == 0:
            pass

        response = serial_port.read_until().decode('utf-8')
        if response == 'v\n':
            voltage = maxwell_bridge.get_voltage()
            serial_port.reset_output_buffer()
            serial_port.write(struct.pack('!f', voltage))
        elif response != 'q\n':
            tmp_msg = [*response]
            if 'v' not in tmp_msg:
                channel = tmp_msg[0]
                pwm_value = int(''.join(tmp_msg[1:5]))
            else:
                channel = tmp_msg[1]
                pwm_value = int(''.join(tmp_msg[2:6]))
            pwm_handler.set_pwm(channel, pwm_value)
            voltage = maxwell_bridge.get_voltage()
            serial_port.reset_output_buffer()
            serial_port.write(struct.pack('!f', voltage))
        else:
            serial_port.close()
            sys.exit()
