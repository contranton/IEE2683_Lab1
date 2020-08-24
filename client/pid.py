from collections import deque
import numpy as np

class PID:

    def __init__(self):
        self.error = 0
        
        self.Ki = 0
        self.Kd = 0
        self.Kp = 0

        self.N_filter = 10
        self.window = deque(maxlen=self.N_filter)

    def set_Ki(self, value):
        self.Ki = value

    def set_Kd(self, value):
        self.Kd = value

    def set_Kp(self, value):
        self.Kp = value

    def set_filter_length(self, value):
        self.N_filter = int(value)
        self.window = deque(self.window, maxlen=self.N_filter)

    @property
    def filtered_error(self):
        """Returns running average of self.window

        Returns:
            double: the average of the samples in self.window
        """
        return np.convolve(self.window, np.ones(self.N_filter)/self.N_filter, mode='valid')[0]

    def activate_pid(self, value):
        pass

    def activate_antiwindup(self, value):
        pass

    def antiwindup_gain(self, value):
        pass
