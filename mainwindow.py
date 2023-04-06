#Nick Cejka
#Senior Design Ground Station Application

import os
from pathlib import Path
import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QTextBrowser
from PySide6.QtCore import QFile, Qt, Slot
from PySide6.QtGui import QImage

# Important:
# You need to run the command to generate the ui_form.py file FIRST!!
from ui_form import Ui_MainWindow

# dictionary with bytes to send for each robot control input
control_map = {
    "ledOn" : "a100",
    "ledOff" : "a111",
    "forward" : "^",
    "backward" : "v",
    "right" : ">",
    "left" : "<",
    "camDeploy" : "camdeploy",
    "camRetract" : "camretract",
    "screenDeploy" : "screendeploy",
    "screenRetract" : "screenretract"}

status_screen = None
status_source = None
status_movement = None
status_camera = None




class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.load_ui()
        
        # Identify global variables for class use
        global camera_timer
        global server_connection
        

    def load_ui(self):
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Project J.A.V.E.L.I.N. Ground Control Station")
        # Set initial camera feed background
        #self.ui.label_camera.setStyleSheet("border-image:url(\"background.png\"); background-position: center;" )
        image = QImage("camerabackground.png")
        self.ui.label_camera.setPixmap(QPixmap.fromImage(image))
        
        self.ui.label_fps.setStyleSheet("font-size: 20px; color: white; background-color: black; padding: 5px;")
        
        # Setup logger and console display
        self.logger = ConsoleLogger(self.ui.textBrowser_log)
        
        
    # @Slot()
    # def on_pushButton_2_clicked(self): # SCREEN BUTTON
    #     if self.ui.pushButton_2.text()[:6] == "DEPLOY":
    #         if self.client.send(codeScreenDeploy):
    #             self.ui.pushButton_2.setText("RETRACT SCREEN")
    #     else:
    #         if self.client.send(codeScreenRetract):
    #             self.ui.pushButton_2.setText("DEPLOY SCREEN")
            
    # @Slot()
    # def on_pushButton_4_clicked(self): # SOURCE BUTTON
    #     if self.ui.pushButton_4.text()[:6] == "DEPLOY":
    #         if self.client.send(codeCameraDeploy):
    #             self.ui.pushButton_4.setText("RETRACT SOURCE")
    #     else:
    #         if self.client.send(codeCameraRetract):
    #             self.ui.pushButton_4.setText("DEPLOY SOURCE")

    @Slot()
    def on_pushButton_3_clicked(self): # XBOX BUTTON
        if self.ui.pushButton_3.text()[:8] == "ACTIVATE":
            controllerXbox.running.set()
            inputHandlerThread.running.set()
            
            self.ui.pushButton_3.setText("DE-ACTIVATE XBOX CONTROLLER")
            
        else:
            #https://stackoverflow.com/questions/7680589/python-threading-thread-can-be-stopped-only-with-private-method-self-thread-st
            # controller.stop() # This should stop infinite execution
            # controller._monitor_thread.join(2) # May need to specify timeout or double check for errors
            # if controller._monitor_thread.is_alive():
            #     controller._monitor_thread.__Thread_stop()
            inputHandlerThread.running.clear()
            controllerXbox.running.clear()
            
            self.ui.pushButton_3.setText("ACTIVATE XBOX CONTROLLER")
    
    @Slot()
    def on_pushButton_5_clicked(self): # KEYBOARD BUTTON
        if self.ui.pushButton_5.text()[:8] == "ACTIVATE":
            controllerKeyboard.running.set()
            inputHandlerThread.running.set()
            
            self.ui.pushButton_5.setText("DE-ACTIVATE KEYBOARD CONTROLLER")
            
        else:
            inputHandlerThread.running.clear()
            controllerKeyboard.running.clear()
            
            self.ui.pushButton_5.setText("ACTIVATE KEYBOARD CONTROLLER")

    @Slot()
    def on_pushButton_clicked(self): # ROBOT MOVE BUTTON
        if self.ui.pushButton_6.text()[:4] == "LOCK":
            return # Refactor this to have the button disabled instead
        
        if self.ui.pushButton.text()[:4] == "MOVE":
            
            self.ui.pushButton.setText("LOCK ROBOT")
            
        else:
            
            self.ui.pushButton.setText("MOVE ROBOT")
            
    # @Slot()
    # def on_pushButton_6_clicked(self): # CAMERA MOVE BUTTON
    #     if self.ui.pushButton.text()[:4] == "LOCK":
    #         return
    #     if self.ui.pushButton_6.text()[:4] == "MOVE":
    #         self.ui.pushButton_6.setText("LOCK CAMERA")
    #     else:
    #         self.ui.pushButton_6.setText("MOVE CAMERA")
            
    @Slot()
    def on_pushButton_9_clicked(self): # CONNECT BUTTON
        connecting = False # Use this when connecting to prevent button spam
        if connecting:
            return
        
        if self.ui.pushButton_9.text()[:7] == "CONNECT":
            # perform connection here
            connecting = True
            self.ui.pushButton_9.setText("...")
            
            try:
                server_connect_disconnect()
                # Successful
                self.ui.pushButton_9.setText("DISCONNECT")
                self.ui.groupBox.setTitle("Server Status: CONNECTED")
            except Exception as ex:
                # Failed
                print(ex) # Should print to console logger
                self.ui.pushButton_9.setText("CONNECT")
                
            connecting = False
            
        else:
            # perform disconnection here
            connecting = True
            self.ui.pushButton_9.setText("...")
            
            try:
                server_connect_disconnect()
                # Successful
                self.ui.pushButton_9.setText("CONNECT")
                self.ui.groupBox.setTitle("Server Status: DISCONNECTED")
            except Exception as ex:
                print(ex) # Should print to console logger
                self.ui.pushButton_9.setText("DISCONNECT")
            
            connecting =  False

    
    @Slot()
    def on_pushButtonPing_clicked(self): # PING TEST BUTTON
        #outgoing_queue.put('PING')
        global server_socket
        global ping_time
        # # Test client sending
        ping_time = time()
        packet = bytes.fromhex('01a4') # 0x01a4 -> #420
        server_socket.sendall(packet)
        print(f"sending {packet} and looking for ping-back...")
        
        # Test logger
        # self.logger.write("testing logger...")
    
    @Slot()
    def on_pushButtonTest1_clicked(self): # TEST 1 BUTTON
        outgoing_queue.put('a100') #right now 0x a1 11 turns on an LED and 0x a1 00 turns off that led
        sleep(1)
        outgoing_queue.put('a111')
    
    @Slot()
    def on_actionOpen_log_file_triggered(self):
        print("Opening log file...")
        os.startfile("log.txt")
    
    
    @Slot()
    def on_pushButton_open_clicked(self): # Camera open feed button
        # if not server_connection:
        #     print("No server connection!")
        #     return
        
        if self.ui.pushButton_open.text()[:4] == "Open":
            camera_timer.start(1000/40)  # 30 fps = (1000/30)   /40 gives ~32fps
            self.ui.pushButton_open.setText("Close Feed")
        else:
            camera_timer.stop()
            self.ui.label_fps.setText("0 FPS")
            image = QImage("camerabackground.png")
            self.ui.label_camera.setPixmap(QPixmap.fromImage(image))
            self.ui.pushButton_open.setText("Open Feed")
    
    @Slot()
    def on_pushButtonClearConsole_clicked(self):
        self.logger.textBrowser.clear()
        self.logger.onNewText(f"Project J.A.V.E.L.I.N. Ground Control Station - {str(datetime.now())[:-10]}\n")
    
    # @Slot(QImage) # Slot to update camera feed label when called with new frame
    # def update_label(self, frame):
    #     if self.ui.pushButton_open.text()[:4] == "Open":
    #         return
    #     else:
    #         self.ui.label_camera.setPixmap(QPixmap.fromImage(frame))
    

#self.ui.pushButton_2.setStyleSheet('QPushButton {color: red;}')
#self.ui.pushButton_2.setStyleSheet('QPushButton {color: green;}')








from PySide6.QtCore import QObject, Signal, QUrl
from PySide6 import QtGui
from time import time
from datetime import datetime

class ConsoleLogger(QObject):
    newText = Signal(str)

    def __init__(self, textBrowser):
        super().__init__()
        self.textBrowser = textBrowser # <- self.ui.textBrowser_log
        sys.stdout = self # comment out to use console
        #sys.stderr = self # comment out to use console
        self.newText.connect(self.onNewText)
        
        self.start_time = time()
        self.filepath = "log.txt"
        # Initialize logfile with heading
            # Probably better to create a log folder with new txt files for every session...?
        with open(self.filepath, "a") as logfile:
            logfile.write(f"\n####################[new log output - {str(datetime.now())[:-10]}]####################\n")
        # Initialize console display with heading
        self.newText.emit(f"Project J.A.V.E.L.I.N. Ground Control Station - {str(datetime.now())[:-10]}\n")
        
        # self.textBrowser.setSource(QUrl.fromLocalFile(self.filepath)) # Display entire log on startup

    def write(self, text):
        # Filter BS out
        filters = ["\n", "Exception ignored", '    ']
        for filter in filters:
            if text[:len(filter)] == filter:
                return
        
        # Format text
        text = f"[{round(time() - self.start_time, 3)}]" + text + "\n"
        
        with open(self.filepath, "a") as logfile:
            logfile.write(text)
        self.newText.emit(text)

    def onNewText(self, text):
        cursor = self.textBrowser.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.textBrowser.setTextCursor(cursor)
        self.textBrowser.ensureCursorVisible()
    
    




import math
import threading
import socket
import sys
from time import sleep
import queue

# Setup universal variables
# https://superfastpython.com/thread-share-variables/

# TO TEST
# server_ip = "127.0.0.1"
server_port = 65432

server_ip = "192.168.0.110"

# TO RUN ON ROBOT
# set my IPv4 static to 192.168.0.98
# server_ip = "192.168.0.123"
# server_port = 10

server_socket = None
server_connection = False

PACKET_SIZE = 64 # 8 byte packets

outgoing_queue = queue.Queue() #FIFO queue with infinite size; send packets in order of received
incoming_queue = queue.Queue()

#incoming_frame_queue = queue.Queue() # for camera stream frames


# site to connect queue thread size to GUI progressbar
# https://stackoverflow.com/questions/12138954/pyside-and-qprogressbar-update-in-a-different-thread

def thread_send_data(pause):
    global server_socket # Tell thread to use global variable
    global server_connection
    global window
    
    # Continuously send data from queue to server
    while True: #server_connection:
        window.ui.lcdNumberOutQue.display(outgoing_queue.qsize())
        #window.ui.lcdNumberOutQue.display(outgoing_queue.unfinished_tasks)
        pause.wait()
        
        # Get the next packet from the outgoing packet queue
        data = outgoing_queue.get()
        
        #print(f"sending {data}")
        
        # Encode packet
        try:
            packet = bytes.fromhex(data)
        except Exception as ex:
            try:
                packet = data.encode()
            except Exception as ex2:
                print(f"Send Encode Errors: {ex} and {ex2}")
        
        # send encoded packet
        try:
            
            
            # NEED TO SLICE INTO MULTIPLE PACKETS???
            
            #server_socket.send(packet)
            server_socket.sendall(packet)
            #print('sent')
            
            # log traffic if enabled
            if window.ui.checkBoxLogTraffic.isChecked():
                print(f"sent {packet}")
        except Exception as ex:
            print(f"Error: {ex}")
        
        

# import pickle # used for encoding objects!
from numpy import array

def thread_recv_data(pause):
    global server_socket
    global server_connection
    global window
    # Continuously receive data from server
    while True: #server_connection
        # all_packets = False
        # data = ''
        # receive complete data stream:
        # while not all_packets:
        window.ui.lcdNumberInQue.display(incoming_queue.qsize())
        pause.wait()
        
        try:
            packet = server_socket.recv(PACKET_SIZE) # blocks here
        except Exception as ex:
            print(f"Recv Error: {ex}")
            server_connect_disconnect()
        try:
            packet = packet.hex()
        except Exception as ex:
            try:
                packet = packet.decode()
            except Exception as ex2:
                print(f"Recv Decode Errors: {ex} and {ex2}")
                break
            
            
            # Raw packet should come in like: [f"{data_id}[:4]{packet}[:PACKET_SIZE]{/end}[:4]"]
            # "/end" signals end of complete data stream
            # data_id = packet[:4]
            
            # if packet[-4:] == "/end":
            #     all_packets = True
            #     packet = packet[4:-4]
            # else:
            #     packet = packet[4:]
            
            #data += packet
            
        # now we got the complete data stream!!
        
        #data = pickle.loads(serialized_data)
        if not packet:
            continue
        
        # check for ping-back packet
        if packet == '01a4':
            print(f"Ping latency: {round((time() - ping_time)*1000,2)}ms")
        
        
        
        # Check if server wants to disconnect
        if packet == "666":
            break
        
        
        # Add data to incoming packet queue
        # if data_id == "camf":
        #     data = array(data)
        #     incoming_frame_queue.put()
        # else:
        incoming_queue.put(packet)
        if window.ui.checkBoxLogTraffic.isChecked():
            print(f"recv {packet}")
        
    
    # The client will disconnect if broken out of loop??? noo>?
    # now done automatically? dont think so.....
    # window.ui.on_pushButton_9_clicked()
    
def server_connect_disconnect():
    global server_ip
    global server_port
    global server_socket
    global server_connection
    
    global send_pause
    global recv_pause
    
    if not server_connection:
        # Connect here
        if not server_socket:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_connection = False
        # Connect the socket to the port where the server is listening
        server_address = (server_ip, server_port)
        print('connecting to {}:{}...'.format(*server_address))
        try:
            server_socket.connect(server_address)
        except Exception as ex:
            print(f"Connection failed: {ex}")
            return
        
        # setup send and receive threads
        send_pause = threading.Event()
        send_pause.set()
        send_thread = threading.Thread(target=thread_send_data, name="Thread-Send", args=(send_pause, ), daemon=True)
        send_thread.start()
        recv_pause = threading.Event()
        recv_pause.set()
        recv_thread = threading.Thread(target=thread_recv_data, name="Thread-Recv", args=(recv_pause, ), daemon=True)
        recv_thread.start()
        
        server_connection = True
        print("Connection established")
    
    else:
        # Disconnect here
        print('closing socket')
        
        # Pause send and recv threads
        send_pause.clear()
        recv_pause.clear()
        
        # try:
        #     self.send("")
        server_socket.close()
        server_socket = None # need to clear [closed] socket object
        
        # Remove the incoming and outgoing packet queues
        with incoming_queue.mutex:
            incoming_queue.queue.clear()
        with outgoing_queue.mutex:
            outgoing_queue.queue.clear()
        # Might need to swap to this if thread gets dead-locked
        # while not q.empty():
        # try:
        #     q.get(block=False)
        # except Empty:
        #     continue
        # q.task_done()
        
        server_connection = False
        print("Connection closed")


# processEvents() can be used to help the UI update more seamlessly after an operation update (bad to use!)


#### Camera stream handling ####
import cv2
from PySide6.QtCore import QTimer, QDateTime, Signal
from PySide6.QtGui import QImage, QPixmap
from time import sleep

# class cameraFeedHandler(QObject):
#     frame_received = Signal(QImage)
    
# Threaded camera feed handling - WE NEED >= 240p @ 25fps
def update_camera(label, fpsLabel, imageHub):
    global lastActive
    global lastActiveCheck
    global ACTIVE_CHECK_SECONDS
    global frames
    global frame_time
    # start looping over all the frames
    # https://stackoverflow.com/questions/48416936/pyqt5-update-labels-inrun-time
    while True:
        # receive RPi name and frame from the RPi and acknowledge the receipt
        (rpiName, frame) = imageHub.recv_image() # sits here till a frame sent
        imageHub.send_reply(b'OK')
        # if a device is not in the last active dictionary then it means that its a newly connected device
        if rpiName not in lastActive.keys():
            print("[INFO] receiving data from {}...".format(rpiName))
        # record the last active time for the device from which we just received a frame
        lastActive[rpiName] = datetime.now()
        
        # update the new frame in the frame dictionary
        frameDict[rpiName] = frame
        
        # # if current time - last time when the active device check was made is greater than the threshold set then do a check
        # if (datetime.now() - lastActiveCheck).seconds > ACTIVE_CHECK_SECONDS:
        #     # loop over all previously active devices
        #     for (rpiName, ts) in list(lastActive.items()):
        #         # remove the RPi from the last active and frame
        #         # dictionaries if the device hasn't been active recently
        #         if (datetime.now() - ts).seconds > ACTIVE_CHECK_SECONDS:
        #             print("[INFO] lost connection to {}".format(rpiName))
        #             lastActive.pop(rpiName)
        #             frameDict.pop(rpiName)
        #     # set the last active check time as current time
        #     lastActiveCheck = datetime.now()
    
        # # ret, frame = cam.read()
        # # if ret:
        # #     # Convert the frame to a QImage
        # #     frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # #     image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        # #     label.setPixmap(QPixmap.fromImage(image))
        # #     # Increment fps counter when successful
        # #     frames += 1
        # # else:
        # #     print("error reading frame")
        
        # #### TESTING #### ^ old working code
        # frame = incoming_frame_queue.get()
        
        
        image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(image))
        
        # Increment fps counter when successful
        frames += 1
        ####
        
        # Update FPS counter
        current_time = QDateTime.currentDateTime()
        elapsed_time = frame_time.msecsTo(QDateTime.currentDateTime())/1000.0
        if elapsed_time >= 1.0:
            fps = round(frames /elapsed_time, 1)
            fpsLabel.setText(f"{frame.shape[1]}x{frame.shape[0]} @ {fps} FPS")
            frames = 0
            frame_time = current_time
        
        thingthatfixescamera += 1 # this will fail but causes UI to not lock up... why idk but it works
        #app.processEvents()

import imagezmq

if __name__ == "__main__":
    # Start independent client handler
    #self._monitor_thread = threading.Thread(target=self._monitor_controller, args=())
    #self._monitor_thread.daemon = True
    #self._monitor_thread.start()
    
    from controllers import XboxController, KeyboardController, controllerHandler
    controllerXbox = XboxController()
    controllerKeyboard = KeyboardController()
    # Need to create another thread that processes continuous inputs for sending if activated
    
    inputHandlerThread = controllerHandler(outgoing_queue, controllerXbox, controllerKeyboard)
    inputHandlerThread.start()

    
    
    # Start GUI
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # initialize the ImageHub object
    imageHub = imagezmq.ImageHub()
    
    hostname = socket.gethostname()
    print(f"imagezmq.ImageHub() initialized on {socket.gethostbyname(hostname)}")
    
    frameDict = {} # hostname key and the associated latest frame value
    
    lastActive = {}
    lastActiveCheck = datetime.now()
    ACTIVE_CHECK_PERIOD = 10
    ACTIVE_CHECK_SECONDS = 10
    
    # Start camera handler
    #cameraHandler = cameraFeedHandler()
    #cameraHandler.frame_received.connect(update_label)
    
    frames = 0
    frame_time = QDateTime.currentDateTime()
    thingthatfixescamera = 0 # do not declare this as global in update_camera otherwise it freezes for some reason
    #camera = cv2.VideoCapture(0) # 0 opens default camera
    camera_timer = QTimer()
    camera_timer.timeout.connect(lambda: update_camera(window.ui.label_camera, window.ui.label_fps, imageHub))
    
    
    sys.exit(app.exec())




