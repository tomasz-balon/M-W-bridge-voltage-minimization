# Config file containing all constants
# Preferably use classes/dataclasses

class BridgeConstants:
    """
    Constant values for bridge_simulator 
    """
    # Serial port settings
    COM_PORT = 'COM3'
    BAUD_RATE = 9600

    # Potentiometer constants
    MIN_RESISTANCE = 100
    MAX_RESISTANCE = 2000

    # Bridge simulator constants
    VOLTAGE = 5
    CAPACITANCE = 1e-9  # 1e-7
    RESISTANCE3 = 50  # 1e2
    RESISTANCE4 = 1.8e2
    INDUCTANCE = 100e-6  # 1e-2
    FREQUENCY = 10e3  # 1.3e4

    # PWM constants
    PWM_MIN = 2000
    PWM_MAX = 7000

    PREV_PWM1 = 0
    PREV_PWM2 = 0
    PREV_VOLTAGE = 10


class ReaderConstants:
    """
    Constant values for reader
    """
    # Serial port settings
    COM_PORT = 'COM3'
    BAUD_RATE = 9600

    # Communication constants
    GET_VOLTAGE_MSG = b'v\n'
    NEWLINE_B = b'\n'
    CHANNELS_LIST = ['1', '2', '3', '4']
    PWMS_LIST = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    LEFT_PWMS = ['A', 'C', 'E', 'G']
    RIGHT_PWMS = ['B', 'D', 'F', 'G']
    CHANNEL_PWM_DICT = {
        '1': ['A', 'B'],
        '2': ['C', 'D'],
        '3': ['E', 'F'],
        '4': ['G', 'H']
    }
    CHOSEN_CHANNEL = '1'

    # Other
    SEC = 1
    MIN = 60 * SEC
    DIVIDER = 5
    STEP = 10  # 50
    STEP1 = 500  # 10
    STEP2 = 500  # 10
    IF_START = True
    WELCOME_MESSAGE = 'This script runs regularly every 5 minutes\n' \
                      'You can however run it manually without resetting the timer' \
                      'Possible options:\n' \
                      'vX - get the current voltage for chosen channel and run compensation algorithm\n' \
                      '     (X stands for channel in range 1-4)\n' \
                      'q - quit the program\n'
    VOLTAGE = 10


class Results:
    """
    Class to store results globally
    """
    PWM_VALUES = {
        'A': None,
        'B': None,
        'C': None,
        'D': None,
        'E': None,
        'F': None,
        'G': None,
        'H': None
    }

    RESULTS = {
        'A': None,
        'B': None,
        'C': None,
        'D': None,
        'E': None,
        'F': None,
        'G': None,
        'H': None
    }

    VOLTAGE_VALUES = {
        '1': None,
        '2': None,
        '3': None,
        '4': None
    }

    RESULT_VOLTAGE = {
        '1': None,
        '2': None,
        '3': None,
        '4': None
    }
