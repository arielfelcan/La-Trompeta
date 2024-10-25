from machine import Pin
from time import sleep

class StepperMotor:
    def __init__(self, in1_pin, in2_pin, in3_pin, in4_pin, steps_per_rev=50):
        # Initialize GPIO pins for the motor
        self.IN1 = Pin(in1_pin, Pin.OUT)
        self.IN2 = Pin(in2_pin, Pin.OUT)
        self.IN3 = Pin(in3_pin, Pin.OUT)
        self.IN4 = Pin(in4_pin, Pin.OUT)
        
        # Define the step sequence for the motor clockwise
        self.step_sequence_cw = [
            [1, 0, 0, 0],
            [1, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 1],
            [0, 0, 0, 1],
            [1, 0, 0, 1]
        ]

        # Define the step sequence for counterclockwise rotation
        self.step_sequence_ccw = [
            [1, 0, 0, 1],
            [0, 0, 0, 1],
            [0, 0, 1, 1],
            [0, 0, 1, 0],
            [0, 1, 1, 0],
            [0, 1, 0, 0],
            [1, 1, 0, 0],
            [1, 0, 0, 0]
        ]
        
        # Steps per full revolution
        self.steps_per_rev = steps_per_rev
        
        # Define step positions for open and closed
        self.open_position = 360  # Degrees for the open position
        self.closed_position = 0   # Degrees for the closed position

    # Move the stepper motor by a certain number of steps
    def step_motor(self, steps, delay, dir='cw'):
        if dir == 'cw':
            self.step_sequence = self.step_sequence_cw
        else:
            self.step_sequence = self.step_sequence_ccw
            
        for _ in range(steps):
            for step in self.step_sequence:
                self.IN1.value(step[0])
                self.IN2.value(step[1])
                self.IN3.value(step[2])
                self.IN4.value(step[3])
                sleep(delay)

    # Convert degrees to steps
    def deg_to_step(self, deg):
        return int(deg * self.steps_per_rev / 360)

    # Rotate motor by degrees
    def rotate_by_degrees(self, degrees, delay=0.005):
        steps = self.deg_to_step(abs(degrees))  # Use absolute value for steps
        direction = 'cw' if degrees > 0 else 'ccw'  # Determine direction
        print(f'Rotating {degrees} degrees ({steps} steps) in {direction} direction')
        self.step_motor(steps, delay, dir=direction)

    def open_mute(self):
        # Move to the open position
        self.rotate_by_degrees(self.open_position)

    def close_mute(self):
        # Move to the closed position
        self.rotate_by_degrees(self.closed_position - self.open_position)  # Adjust to closed position

'''
def main():
    motor = StepperMotor(0, 1, 2, 3)
    motor.open_mute()  # Move to the open position
    sleep(1)              # Wait for a second
    motor.close_mute() # Move to the closed position
    
if __name__ == "__main__":
    main()
'''
