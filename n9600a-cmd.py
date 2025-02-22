# n9600a-cmd
# Python3
# Send commands to n9600a connected by serial port.
# Nino Carrillo
# 24 Feb 2023
# Exit codes
# 1 Wrong python version
# 2 Not enough command line arguments
# 3 Unable to open serial port
# 4 Invalid command
# 5 Invalid value
# 6 Timeout waiting for response

import serial
import sys
import time

def GracefulExit(port, code):
	try:
		port.close()
	except:
		pass
	finally:
		#print('Closed port ', port.port)
		sys.exit(code)

def AssembleKISSFrame(input_array):
	FESC = int(0xDB).to_bytes(1,'big')
	FEND = int(0xC0).to_bytes(1,'big')
	TFESC = int(0xDD).to_bytes(1,'big')
	TFEND = int(0xDC).to_bytes(1,'big')
	frame_index = 0
	result = bytearray()
	while(frame_index < len(input_array)):
		kiss_byte = input_array[frame_index]
		if kiss_byte.to_bytes(1,'big') == FESC:
			result.extend(FESC)
			result.extend(TFESC)
		elif kiss_byte.to_bytes(1, 'big') == FEND:
			result.extend(FESC)
			result.extend(TFEND)
		else:
			result.extend(kiss_byte.to_bytes(1, 'big'))
		frame_index += 1
	result = bytearray(FEND) +  result + bytearray(FEND)
	return result

if sys.version_info < (3, 0):
	print("Python version should be 3.x, exiting")
	sys.exit(1)

if len(sys.argv) < 4:
	print(f'Not enough arguments. Usage prototype below.\r\npython3 n9600a-cmd.py <serial device> <baud> <command> <optional value>')
	print(f'Available commands:')
	print(f'CLRSERNO               : Erases the stored TNC serial number. Perform before SETSERNO.')
	print(f'SETSERNO xxxxxxxx      : Sets the TNC serial number, value is 8 ASCII characters.')
	print(f'GETSERNO               : Queries and displays the TNC serial number.')
	print(f'SETBCNINT nnn          : Sets the beacon interval, value is minutes 0 to 255. 0 disables.')
	print(f'GETVER                 : Queries and displays the TNC firmware version.')
	print(f'STOPTX                 : Stop the current transmission and flush queues.')
	print(f'GETALL                 : Dump diagnostic data.')
	print(f'SETPERSIST nnn         : Set CSMA persistance value, 0 to 255.')
	print(f'SETSLOT nnn            : Set CSMA slot time in 10mS units, 0 to 255.')
	print(f'SETTXD nnn             : Set TX_DELAY in 10mS units, 0 to 255, if TX_DELAY pot set to zero.')
	print(f'SETTXTAIL nnn          : Set TX_TAIL in 10mS units, 0 to 255. Not on NinoTNC.')
	print(f'SETHW nnn              : Issue SetHardware KISS command to the modem, passing one byte to it.')
	
	sys.exit(2)

command_string = sys.argv[3].upper()
command = bytearray()
value = bytearray()
get_response = 'no'
if command_string == 'SETSERNO':
	command.extend(int(0xA).to_bytes(1,'big'))
	get_response = 'no'
	# print(command)
	try:
		value_string = sys.argv[4]
	except:
		print('Not enough arguments for SETSERNO command.')
		sys.exit(2)
	value.extend(bytes(value_string, 'ascii'))
	if len(value) < 8:
		print('Invalid value for SETSERNO command. Must be 8 characters.')
		sys.exit(5)
	# print(value)
elif command_string == "CLRSERNO":
	command.extend(int(0xA).to_bytes(1,'big'))
	get_response = 'no'
	# print(command)
	value = bytearray([0,0,0,0,0,0,0,0])
	# print(value)
elif command_string == 'SETBCNINT':
	# print('set bcn int')
	command.extend(int(0x9).to_bytes(1,'big'))
	command.extend(int(0xF0).to_bytes(1,'big'))
	get_response = 'no'
	try:
		value_string = sys.argv[4]
	except:
		print('Not enough arguments for SETBCNINT command.')
		sys.exit(2)
	value_int = int(value_string)
	if value_int < 0 or value_int > 255:
		print('Invalid value for SETBCNINT command. Must be 0 to 255.')
		sys.exit(5)
	value.extend(value_int.to_bytes(1,'big'))
elif command_string == 'GETSERNO':
	print('get serial number')
	command.extend(int(0xE).to_bytes(1,'big'))
	value.extend(int(0).to_bytes(1,'big'))
	get_response = 'yes'
elif command_string == 'GETVER':
	print('get firmware version')
	command.extend(int(0x8).to_bytes(1,'big'))
	value.extend(int(0).to_bytes(1,'big'))
	get_response = 'yes'
elif command_string == 'GETALL':
	print('get all')
	command.extend(int(0xB).to_bytes(1,'big'))
	value.extend(int(0).to_bytes(1,'big'))
	get_response = 'yes'
elif command_string == 'STOPTX':
	print('stop tx')
	command.extend(int(0x9).to_bytes(1,'big'))
	command.extend(int(0x0).to_bytes(1,'big'))
	get_response = 'no'
elif command_string == 'SETPERSIST':
	print('set persist')
	command.extend(int(0x2).to_bytes(1,'big'))
	get_response = 'no'
	try:
		value_string = sys.argv[4]
	except:
		print('Not enough arguments for SETPERSIST command.')
		sys.exit(2)
	value_int = int(value_string)
	if value_int < 0 or value_int > 255:
		print('Invalid value for SETPERSIST command. Must be 0 to 255.')
		sys.exit(5)
	value.extend(int(value_int).to_bytes(1,'big'))
elif command_string == 'SETSLOT':
	print('set slot')
	command.extend(int(0x3).to_bytes(1,'big'))
	get_response = 'no'
	try:
		value_string = sys.argv[4]
	except:
		print('Not enough arguments for SETSLOT command.')
		sys.exit(2)
	value_int = int(value_string)
	if value_int < 0 or value_int > 255:
		print('Invalid value for SETSLOT command. Must be 0 to 255.')
		sys.exit(5)
	value.extend(int(value_int).to_bytes(1,'big'))
elif command_string == 'SETTXD':
	print('set tx delay')
	command.extend(int(0x1).to_bytes(1,'big'))
	get_response = 'no'
	try:
		value_string = sys.argv[4]
	except:
		print('Not enough arguments for SETTXD command.')
		sys.exit(2)
	value_int = int(value_string)
	if value_int < 0 or value_int > 255:
		print('Invalid value for SETTXD command. Must be 0 to 255.')
		sys.exit(5)
	value.extend(int(value_int).to_bytes(1,'big'))
elif command_string == 'SETTXTAIL':
	print('set tx tail')
	command.extend(int(0x4).to_bytes(1,'big'))
	get_response = 'no'
	try:
		value_string = sys.argv[4]
	except:
		print('Not enough arguments for SETTXTAIL command.')
		sys.exit(2)
	value_int = int(value_string)
	if value_int < 0 or value_int > 255:
		print('Invalid value for SETTXTAIL command. Must be 0 to 255.')
		sys.exit(5)
	value.extend(int(value_int).to_bytes(1,'big'))
elif command_string == 'SETHW':
	print('set hardware')
	command.extend(int(0x6).to_bytes(1,'big'))
	get_response = 'no'
	try:
		value_string = sys.argv[4]
	except:
		print('Not enough arguments for single byte SETHW command.')
		sys.exit(2)
	value_int = int(value_string)
	if value_int < 0 or value_int > 255:
		print('Invalid value for single byte SETHW command. Must be 0 to 255.')
		sys.exit(5)
	value.extend(int(value_int).to_bytes(1,'big'))
else:
	print('Unrecognized command.')
	sys.exit(4)

try:
	port = serial.Serial(sys.argv[1], baudrate=int(sys.argv[2]), bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, timeout=3)
except:
	print('Unable to open serial port.')
	sys.exit(3)

kiss_output_frame = AssembleKISSFrame(command + value)
print(" ".join(hex(b) for b in kiss_output_frame))

frame_time = len(kiss_output_frame) * 10.0 / float(sys.argv[2])
port.write(kiss_output_frame)

if get_response == 'yes':
	start_response_time = time.time()
	kiss_state = "non-escaped"
	kiss_frame = []
	FESC = 0xDB
	FEND = 0xC0
	TFESC = 0xDD
	TFEND = 0xDC
	frame_count = 0
	while frame_count < 1:
		elapsed_time = time.time() - start_response_time
		if (elapsed_time > 2):
			print('Timeout waiting for response.')
			GracefulExit(port, 6)
		input_data = port.read(1)
		if input_data:
	#		print(input_data)
			if kiss_state == "non-escaped":
				if ord(input_data) == FESC:
					kiss_state = "escaped"
				elif ord(input_data) == FEND:
					if len(kiss_frame) > 0:
						frame_count += 1
						kiss_frame_string = ""
						for character in kiss_frame[1:]:
							kiss_frame_string += chr(character)
						print(kiss_frame_string)
						# kiss_frame = []
					else:
						kiss_frame = []
				else:
					kiss_frame.append(ord(input_data))
			elif kiss_state == "escaped":
				if ord(input_data) == TFESC:
					kiss_frame.append(FESC)
					kiss_state = "non-escaped"
				elif ord(input_data) == TFEND:
					kiss_frame.append(FEND)
					kiss_state = "non-escaped"


time.sleep(frame_time * 1.5)

GracefulExit(port, 0)
