import re
import serial
import time
from threading import Thread

class ArduinoController:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)
        self.buffer = ""
        self.stop_flag = False  

    def send_command(self, command):
        if self.ser.is_open:
            self.ser.write(f"{command}\n".encode('utf-8'))
            print(f"[INFO] [RPI] Command sent: {command}")
        else:
            print("[ERROR] [RPI] Serial port is not open.")

    def read_message(self):
        if self.ser.in_waiting > 0:
            data = self.ser.read(self.ser.in_waiting).decode('utf-8')
            self.buffer += data
            self.buffer = self.remove_ansi_codes(self.buffer)
            return self.buffer.strip()
        return None

    @staticmethod
    def remove_ansi_codes(text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def waiting_for_completion(self, keyword=""):
        while not self.stop_flag:
            message = self.read_message()
            if message and keyword in message:
                print(f"{message}")
                self.buffer = ""
                return True
        return False
    
    def move_drawer_out(self, drawer_number):
        command = f"L{drawer_number}_OUT"
        self.send_command(command)
        
        if self.waiting_for_completion(keyword="successfully"):
            print(f"[INFO] [RPI] Drawer {drawer_number} Slide out complete")
            
        else:
            print(f"[ERROR] [RPI] Drawer {drawer_number} Not at start point")

    def move_drawer_in(self, drawer_number):
        command = f"L{drawer_number}_INIT"
        self.send_command(command)
        if self.waiting_for_completion(keyword="successfully"):
            print(f"[INFO] [RPI] Drawer {drawer_number} Slide in complete")
        else:
            print(f"[ERROR] [RPI] Drawer {drawer_number} not at end point")
    
    def check_distance(self):
        self.send_command("CHECK_DISTANCE")
        if self.waiting_for_completion(keyword="Object Detected"):
            print("1")
            return True
        if self.waiting_for_completion(keyword="No Object Detected"):
            print("2")
            return False

    def test_ee(self):
        try:
            self.send_command("TEST_EE")  
            print("[INFO] [RPI] Waiting for data from Arduino...")
            time.sleep(0.5)
            while not self.stop_flag:  
                message = self.read_message()
                if message:
                    print(f"{message}")
        except KeyboardInterrupt:
            print("[INFO] [RPI] Ctrl+C detected. Stopping...")
            self.send_command("CC")
    
    def test_ul(self):
        try:
            self.send_command("TEST_ul")  
            print("[INFO] [RPI] Waiting for data from Arduino...")
            time.sleep(0.5)
            while not self.stop_flag:  
                message = self.read_message()
                if message:
                    print(f"{message}")
        except KeyboardInterrupt:
            print("[INFO] [RPI] Ctrl+C detected. Stopping...")
            self.send_command("CC")  
    
    def monitor_keyboard(self):
        pass

        
def drawer_controller(port, baudrate, d_status, d_number):
    arduino =ArduinoController(port, baudrate)
    # if arduino.check_distance() and d_status == 0:
    if  d_status == 0:
        arduino.move_drawer_out(d_number)
    elif d_status == 1:
        arduino.move_drawer_in(d_number)