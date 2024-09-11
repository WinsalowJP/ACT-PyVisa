import pyvisa
import time
import csv
import threading


################PyVisa Setup##################################################################
# Resource manager setup
rm = pyvisa.ResourceManager()

resources = rm.list_resources() #checks available devices for VISA to connect to. 
#print("Available resources:", resources) #uncomment this to check devices

##############################################################################################

####################Device Setup##############################################################################
dmm_id1 = 'USB0::0x2A8D::0x0301::MY54507560::INSTR'  # multimeter 1 (ACT0012)
dmm_id2 = 'USB0::0x2A8D::0x0301::MY54505907::INSTR'  # multimeter 2 (ACT0011)

            ##CSV file setup##
timestamp = time.strftime('%Y%m%d-%H%M%S')
#filename = f'Dual_DMM_Datalogger_{timestamp}.csv'
header = ['Date'] + ['Time'] + ['Voltage (V)'] + ['Current (A)'] + ['Voltage of shunt (V)'] + ['Power (kW)']

print('Enter output file name (without .csv extension):')
name_input = input().strip()  # Get user input and remove any leading/trailing whitespace
# Validate input
if not name_input:
    print("Error: Power Meter CSV name cannot be empty.")
    exit()
filename = f'{name_input}.csv'
##############################################################################################################

##############################################################
# Global flag for stopping the loop.
# checks if user has input stop and end logging.
stop_logging = False

def check_for_stop():
    global stop_logging
    while not stop_logging:
        user_input = input().strip().lower()
        if user_input == 'stop':
            stop_logging = True
##############################################################

# Create and start the thread for checking the stop command
input_thread = threading.Thread(target=check_for_stop)
input_thread.daemon = True  # Set daemon to allow the program to exit even if the thread is still running
input_thread.start()


try:
    # Open the CSV file for writing
    with open(filename, 'w', newline='') as file:
        csvwriter = csv.writer(file)

        # Write the header
        csvwriter.writerow(header)

        # Connect to the Keysight 34465A
        dmm1 = rm.open_resource(dmm_id1)
        dmm1.timeout = 10000  # Set timeout to 10 seconds

        dmm2 = rm.open_resource(dmm_id2)
        dmm2.timeout = 10000  # Set timeout to 10 seconds

        # Print the IDN (Identification) string to verify connection of multimeter 1
        print("Connected to:", dmm1.query('*IDN?').strip())

        # Print the IDN (Identification) string to verify connection of multimeter 2
        print("Connected to:", dmm2.query('*IDN?').strip())

        dmm1.write('INIT')
        dmm2.write('INIT')
        time.sleep(0.5)

        # Configure the multimeter for voltage measurement
        dmm1.write('CONF:VOLT:DC 100,0.001')  # Configure for DC voltage, range 100V, resolution 1mV
        dmm2.write('CONF:VOLT:DC 10,0.0001')  # Configure for DC voltage, range 10V, resolution 0.1mV

        # Perform multiple readings until stopped
        reading_count = 0
        while not stop_logging:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"\nReading {reading_count + 1} at {timestamp}:")

            date1 = time.strftime('%m/%d/%Y')
            time1 = time.strftime('%H:%M:%S')
            csv_out = [date1, time1]

            # Reading the voltage measurement from multimeter 1
            measurement1 = dmm1.query('MEAS:VOLT:DC?')
            voltage = float(measurement1)
            print(f'Voltage: {voltage:.6f} V')
            csv_out.append(f'{voltage:.6f}')

            # Reading the shunt voltage measurement from multimeter 2
            measurement2 = dmm2.query('MEAS:VOLT:DC?')
            voltage2 = float(measurement2)

            current = 5000 * voltage2  # convert mV to A
            power = current * voltage  # current * voltage to get power
            power_out = power / 1000  # convert to kW

            print(f'Current: {current:.6f} A')  # print current
            print(f'Power: {power_out:.6f} kW')  # print power
            csv_out.append(f'{current:.6f}')  # add current to CSV
            csv_out.append(f'{voltage2:.6f}')  # add shunt voltage to CSV
            csv_out.append(f'{power_out:.6f}')  # add power to CSV

            # Write the measurements to the CSV file
            csvwriter.writerow(csv_out)  # write all data into CSV

            time.sleep(0.2)  # delay by 0.2 seconds

            reading_count += 1

except pyvisa.VisaIOError as e:
    print(f"VISA IO Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Close the connections
    if 'dmm1' in locals():
        dmm1.close()
        print("Connection closed.")

    if 'dmm2' in locals():
        dmm2.close()
        print("Connection closed.")

print('')
print('')
print('Press Enter to close')
input()