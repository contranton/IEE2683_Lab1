from collections import deque
import numpy as np

# TODO: Implement using only ndarrays
class PID:
    """PID controller with saturated output, a filtered derivative, and
    anti-windup logic

    Antiwindup is implemented with zero-crossing integral reset and saturation
    compensation (c.f. MIT 16.30/31 Feedback Systems. Topic #23, p. 8):
    <https://ocw.mit.edu/courses/aeronautics-and-astronautics/16-30-feedback-control-systems-fall-2010/lecture-notes/MIT16_30F10_lec23.pdf>

    Details:
    1. Zero-Crossing: When the error changes sign, the integral is reset.
        Otherwise,the controller has to "pull" in the other direction that made
        it move towards the reference so that the integral is made 0.

    2. Saturation compensation: When the output saturates, Ki is made 0. The
       integral will keep growing but it won't affect the system again until at
       least a zero crossing has happened, triggering the previous condition.

    """
    def __init__(self):
        # PID Parameters
        self.reference = 0
        
        self._Ki = 0
        self.Kd = 0
        self.Kp = 0

        self.integral = 0            # Accumulated error
        self.last_sign = 1           # Last error sign
        self.magnitude_last_out = 0  # Test for output saturation

        # Derivative filter
        self.N_filter = 2
        self.window = deque(maxlen=self.N_filter)

    @property
    def error(self):
        return self.reference - self.window[-1]

    @property
    def output(self):
        """Returns calculated control signal with PID control

        For the different PID term it uses:
        - Error for the proportional term
        - Filtered Error for the derivative term
        - Integrated Error for the integral term

        Returns:
            double: PID control signal
        """
        return self.Kp*self.error + self.Ki*self.integral + self.Kd*self.filtered_error

    def add_sample(self, value):
        """Adds new data point

        Updates the filtering window and integral

        Args:
            value (double/float): New data point
        """
        self.window.append(value)
        self.integral += self.error

        # Reset integral term if zero-crossing
        sign = np.sign(self.error)
        if sign != self.last_sign:
            self.last_sign = sign
            self.integral = 0

    def set_reference(self, value):
        """Set reference point for error calculation"""
        self.reference = value

    @property
    def Ki(self):
        """Gives Integral Gain conditional on output saturation

        Returns:
            double: Ki if output unsaturated, 0 otherwise
        """
        if self.magnitude_last_out < self.magnitude_saturation:
            return self._Ki
        else:
            return 0

    def set_Ki(self, value):
        """Set Integral Gain"""
        self._Ki = value

    def set_Kd(self, value):
        """Set Derivative Gain"""
        self.Kd = value

    def set_Kp(self, value):
        """Set Proportional Gain"""
        self.Kp = value

    def set_filter_length(self, value):
        """Modify the length of the error filter

        Args:
            value (int): New length of self.window
        """
        self.N_filter = int(value)
        self.window = deque(self.window, maxlen=self.N_filter)

    @property
    def filtered_error(self):
        """Returns running average of self.window

        Returns:
            double: the average of the samples in self.window
        """
        return np.convolve(self.window, np.ones(self.N_filter)/self.N_filter, mode='valid')[0]

    def activate_antiwindup(self, value):
        pass

    def antiwindup_gain(self, value):
        pass
