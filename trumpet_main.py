from machine import Pin, ADC
import asyncio
import time
from BLE_CEEO import Yell
import network
import time
from StepperMotor import StepperMotor

# variable that updates based on the photoresistor

class TrumpetKey():
    def __init__(self, pin_num, key_num, LED):
        self.key = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self.key_num = key_num
        # if pressed var
        self.is_pressed = False
        
        # LED associated with that key
        self.LED = LED
    
    # check if the key is pressed
    async def check_state(self, pr):
        while True:
            if pr.active: # check if the pr is covered
                if not self.key.value():  # When limit switch is pressed, value is low (0)
                    # print("Key", self.key_num, "pressed!")
                    self.is_pressed = True
                    self.LED.turn_on()
                else:
                    # print("Key", self.key_num, "not pressed!")
                    self.is_pressed = False
                    self.LED.turn_off()
            await asyncio.sleep(0.05)

# LEDs
class LED():
    def __init__(self, pin_num, led_num):
        self.led = Pin(pin_num, Pin.OUT)
        self.led_num = led_num
        self.led.value(0)
        
    def turn_off(self):
        self.led.value(0)
    def turn_on(self):
        self.led.value(1)
        
# photoresistor
class PR():
    def __init__(self, pin_num):
        self.pr = pr = ADC(Pin(pin_num))
        self.active = False  # Manages active state locally
        
    def read_pr(self):
        self.pr_value = self.pr.read_u16()  # Reads a value between 0 and 65535
        print(self.pr_value)
        
        time.sleep(0.05)
        return self.pr_value
    
    # continuously check the photoresistor status
    async def check_pr(self):
        while True:
            self.pr_value = self.read_pr()
            
            if self.pr_value >= 64500:
                # not covered so activate the trumpet
                self.active = True
            else:
                # photoresistor is covered so deactivate trumpet
                self.active = False
                
            await asyncio.sleep(0.1)  # delay for readability
        
def connect_garageband():    
    p = Yell('Ari', verbose = True, type = 'midi')
    p.connect_up()
    
    return p

# plays the note for a moment
async def play_note(p, note):
    NoteOn = 0x90
    NoteOff = 0x80
    StopNotes = 123
    SetInstrument = 0xC0
    Reset = 0xFF

    velocity = {'off': 0, 'pppp': 8, 'ppp': 20, 'pp': 31, 'p': 42, 'mp': 53,
                'mf': 64, 'f': 80, 'ff': 96, 'fff': 112, 'ffff': 127}
            
    channel = 0
    cmd = NoteOn

    channel = 0x0F & channel
    timestamp_ms = time.ticks_ms()
    tsM = (timestamp_ms >> 7 & 0b111111) | 0x80
    tsL = 0x80 | (timestamp_ms & 0b1111111)

    c = cmd | channel     
    payload = bytes([tsM, tsL, c, note, velocity['f']])

    p.send(payload)
    await asyncio.sleep(0.2) # play note for a half second
    
    note_off(p, note)

# turns the note off
def note_off(p, note):
    NoteOff = 0x80
    velocity = {'f': 0}  # Optional: Set velocity for "Note Off", usually it's 0
    
    channel = 0
    cmd = NoteOff

    channel = 0x0F & channel
    timestamp_ms = time.ticks_ms()
    tsM = (timestamp_ms >> 7 & 0b111111) | 0x80
    tsL = 0x80 | (timestamp_ms & 0b1111111)

    c = cmd | channel     
    payload = bytes([tsM, tsL, c, note, velocity['f']])
    
    p.send(payload)

# checks fingerings and plays note accordingly
async def fingering_to_note(p, fingering, note_playing):
    curr_fing = tuple(fingering)
    
    # key is the fingering, value is the note
    fingering_to_note = {
        (False, False, False): None,  # No key pressed
        (True, False, False): 60,    # Only Key 1 pressed
        (False, True, False): 62,    # Only Key 2 pressed
        (False, False, True): 64,    # Only Key 3 pressed
        (True, True, False): 65,     # Keys 1 and 2 pressed
        (True, False, True): 67,     # Keys 1 and 3 pressed
        (False, True, True): 69,     # Keys 2 and 3 pressed
        (True, True, True): 71       # All keys pressed
    }
    
    # get the note corresponding to the current fingering
    note = fingering_to_note.get(curr_fing)
    if note != note_playing:
        if note is None:
        # stop playing whatever note was playing

            print("No note to play.")

        elif note_playing is None:

            # note was not playing and now it is

            asyncio.create_task(play_note(p, note))  # Send the note to play

            print("Playing MIDI note:", note)

        else:
            # change of note - stop playing the previous note and start playing the next one
            note_off(p, note_playing)
            play_note(p, note)

            print("Playing MIDI note:", note)
            
    await asyncio.sleep(0.1)

# continuously get the fingering
async def get_note(p, keys, pr, note_playing):
    while True:
        if pr.active:
            # get the current fingering
            fingering = [k.is_pressed for k in keys]
        
        await fingering_to_note(p, fingering, note_playing)
        
async def mute_control(mute, pr):
    mute_open = False  # track if the mute is currently open

    while True:
        if pr.active:
            if not mute_open:
                # open the mute to play
                mute.open_mute()
                mute_open = True  # Update the state to indicate the mute is open
                print('Mute is opened, photoresistor is active.')
        else:
            if mute_open:
                # close the mute to show that you can't play at the moment
                mute.close_mute()
                mute_open = False  # Update the state to indicate the mute is closed
                print("Mute is closed, photoresistor is covered.")

        await asyncio.sleep(0.05)  # Delay before checking again


async def main():
    p = connect_garageband()
    
    # LEDs
    l1 = LED(20, 3)
    l2 = LED(18, 2)
    l3 = LED(7, 1)
    
    # keys
    k1 = TrumpetKey(15, 1, l1)
    k2 = TrumpetKey(14, 2, l2)
    k3 = TrumpetKey(13, 3, l3)
    
    # store key values
    keys = [k1, k2, k3]
    
    # photoresistor
    pr = PR(26)
    
    # mute
    mute = StepperMotor(0, 1, 2, 3)
    
    # initialize starting note
    note_playing = None

    # start everything
    await asyncio.gather(pr.check_pr(),
                   k1.check_state(pr),
                   k2.check_state(pr),
                   k3.check_state(pr),
                   get_note(p, keys, pr, note_playing),
                mute_control(mute, pr)
                   )
        
    await asyncio.sleep(0.1)

asyncio.run(main())
