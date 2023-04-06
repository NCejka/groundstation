from inputs import get_gamepad
import math
import threading
from time import sleep

class XboxController(object):
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self):
        self.running = threading.Event() # Used to pause thread execution
        
        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0
        self.LeftTrigger = 0
        self.RightTrigger = 0
        self.LeftBumper = 0
        self.RightBumper = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.B = 0
        self.LeftThumb = 0
        self.RightThumb = 0
        self.Back = 0
        self.Start = 0
        self.LeftDPad = 0
        self.RightDPad = 0
        self.UpDPad = 0
        self.DownDPad = 0

        self._monitor_thread = threading.Thread(target=self._monitor_controller, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start() # Starts new thread for object execution
    
    def read(self): # return the buttons/triggers that you care about in this method
        x = round(self.LeftJoystickX, 2)
        y = round(self.LeftJoystickY, 2)
        a = self.A
        b = self.X # b=1, x=2
        rb = self.RightBumper
        #print([x, y, a, b, rb])
        return [x, y, a, b, rb]
    
    def _monitor_controller(self):
        while True:
            self.running.wait() # Waits here if running event not set; other threads will then trigger to run again
            #print("Xbox Controller running")
            
            try:
                events = get_gamepad()
                for event in events:
                    if event.code == 'ABS_Y':
                        self.LeftJoystickY = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                    elif event.code == 'ABS_X':
                        self.LeftJoystickX = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                    elif event.code == 'ABS_RY':
                        self.RightJoystickY = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                    elif event.code == 'ABS_RX':
                        self.RightJoystickX = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                    elif event.code == 'ABS_Z':
                        self.LeftTrigger = event.state / XboxController.MAX_TRIG_VAL # normalize between 0 and 1
                    elif event.code == 'ABS_RZ':
                        self.RightTrigger = event.state / XboxController.MAX_TRIG_VAL # normalize between 0 and 1
                    elif event.code == 'BTN_TL':
                        self.LeftBumper = event.state
                    elif event.code == 'BTN_TR':
                        self.RightBumper = event.state
                    elif event.code == 'BTN_SOUTH':
                        self.A = event.state
                    elif event.code == 'BTN_NORTH':
                        self.Y = event.state #previously switched with X
                    elif event.code == 'BTN_WEST':
                        self.X = event.state #previously switched with Y
                    elif event.code == 'BTN_EAST':
                        self.B = event.state
                    elif event.code == 'BTN_THUMBL':
                        self.LeftThumb = event.state
                    elif event.code == 'BTN_THUMBR':
                        self.RightThumb = event.state
                    elif event.code == 'BTN_SELECT':
                        self.Back = event.state
                    elif event.code == 'BTN_START':
                        self.Start = event.state
                    elif event.code == 'BTN_TRIGGER_HAPPY1':
                        self.LeftDPad = event.state
                    elif event.code == 'BTN_TRIGGER_HAPPY2':
                        self.RightDPad = event.state
                    elif event.code == 'BTN_TRIGGER_HAPPY3':
                        self.UpDPad = event.state
                    elif event.code == 'BTN_TRIGGER_HAPPY4':
                        self.DownDPad = event.state
                    
                    sleep(0.016) # Slow poll rate to 60 hz
                    
            except Exception as ex:
                print(ex)
                print(f"Need to restart {self}")
                # print("Deleting self")
                # del self # doesnt work like that b :(

from threading import Thread

class controllerHandler(Thread):
    def __init__(self, server_queue_out, xbox, keyboard):
        Thread.__init__(self)
        self.daemon = True
        
        self.running = threading.Event() # Used to pause thread execution
        self.server_queue_out = server_queue_out
        self.xbox = xbox
        self.keyboard = keyboard
    
    def run(self):
        # init input conditions
        a = 0
        b = 0
        x = 0
        y = 0
        aOld = 0
        bOld = 0
        xOld = 0
        yOld = 0
        while True:
            self.running.wait()
            if self.xbox.running.is_set():
                #xboxInput = self.xbox.read()
                #### ROBOT CODE CONDITIONS ####
                LJX = int((self.xbox.LeftJoystickX+1) *65535/2)
                RJX = int((self.xbox.RightJoystickX+1) *65535/2)
                RT  = int((self.xbox.RightTrigger) *255 +1)
                LT  = int((self.xbox.LeftTrigger) *255 +1)
                
                a = self.xbox.A
                b = self.xbox.B
                y = self.xbox.Y
                
                if(a == 1 and aOld == 0):
                    self.server_queue_out.put('a100')
                elif(b == 1 and bOld == 0):
                    self.server_queue_out.put('a111')

                if(LJX > -1 and LJX<65535):
                    self.server_queue_out.put('a3'+ f'{LJX:04x}'+f'{RJX:04x}')
                if(-1 < RT and RT < 65535):
                    self.server_queue_out.put('a4'+ f'{RT:02x}'+f'{LT:02x}')
                #### ROBOT CODE CONDITIONS ####
                
                aOld = a
                bOld = b
                yOld = y
                
                # # Send commands to TCP queue
                # if xboxInput[2] == 1:
                #     ('a1')
            
            
            sleep(0.1) # Slow poll rate




from pynput import keyboard

# THIS MAY WORK BETTER IN THE FUTURE???
class KeyboardController(threading.Thread):
    def __init__(self):
        #self.input_queue = input_queue
        
        super().__init__()
        self.running = threading.Event() # Used to pause thread execution
        self.daemon = True # Allows python to exit if only daemon threads remain (non-essential)
        self.start() # Starts new thread for object execution

    def run(self):
        while True:
            self.running.wait() # Waits here if running event not set
            print("Keyboard input running")
            
            #key = input()
            #print(key)
            #self.input_queue.put(key)
            
            def on_press(key):
                try:
                    print('alphanumeric key {0} pressed'.format(key.char))
                except AttributeError:
                    print('special key {0} pressed'.format(key))
                
                self.running.wait() # Waits here if running event not set

            def on_release(key):
                # print('{0} released'.format(key))
                # if key == keyboard.Key.esc:
                #     # Stop listener
                #     return False
                return
            
            # # Attempt 1
            # listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            # listener.start()
            
            # # Attempt 2
            # with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            #     listener.join()
            
            # Attempt 3
            event = keyboard.read_event()
            print(event)
            # https://pynput.readthedocs.io/en/latest/keyboard.html
            
            sleep(0.016) # Slow poll rate to 60 hz




# class KeyboardHandler(object):
#     def __init__(self, input_queue):
#         self.input_queue = input_queue
        
#     #     self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
#     #     #listener.start() # Handled by ui
    
#     # def on_press(key, dogshit):
#     #     try:
#     #         print('alphanumeric key {0} pressed'.format(key.char))
#     #     except AttributeError:
#     #         print('special key {0} pressed'.format(key))

#     # def on_release(key, dogshit):
#     #     print('{0} released'.format(key))
#     #     if key == keyboard.Key.esc:
#     #         # Stop listener
#     #         return False
#     def on_press(key):
#         try:
#             print('alphanumeric key {0} pressed'.format(
#                 key.char))
#         except AttributeError:
#             print('special key {0} pressed'.format(
#                 key))

#     def on_release(key):
#         print('{0} released'.format(
#             key))
#         if key == keyboard.Key.esc:
#             # Stop listener
#             return False

#     # # Collect events until released
#     # with keyboard.Listener(
#     #         on_press=on_press,
#     #         on_release=on_release) as listener:
#     #     listener.join()

#     # ...or, in a non-blocking fashion:
#     listener = keyboard.Listener(
#         on_press=on_press,
#         on_release=on_release)
        