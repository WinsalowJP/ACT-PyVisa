import pyvisa
import time
import csv
import threading

print('DAQ Datalogger: type "stop" to end the datalogging at anytime')
print('')
print('')
print('')
# Resource manager setup
rm = pyvisa.ResourceManager()

# CSV file setup
# channels = ['101', '102', '103', '104', '105', '111','112','113','114', '115', '116', '117', '118', '119', '120']  # active channels in DAQ
# channels = ['101', '102', '103', '104', '105', '111','112','113','114', '115', '116', '117', '118', '119', '120']  # active channels in DAQ default
# channels = ['101', '102', '103', '104', '105', '111','112','113','114', '115', '117', '119']  # active channels in temp test
channels = ['105', '102', '119', '112', '111', '113','114','104','115', '103', '117', '101']  # active channels in temp test modified
timestamp = time.strftime('%Y%m%d-%H%M%S')

# name = ['101', '102', '103', '104', '105', '111','112','113','114', '115', '116', '117', '118', '119', '120'] #default
# name = ['H1','L8','Rema','GD L10','T1','H2','Interior Top','CT OW','Chamber In','Chamber Out'] #UL Test header
# name = ['Exhaust Fan', 'T3', 'L2', 'HS1', 'HS2', 'L11','Output Fuse','J23','Solder Side', 'Negative Busbar','Top', 'L10'] #thermal test name
name = ['HS2', 'T3', 'L10', 'Output Fuse', 'L11', 'J23','Solder Side','HS1','Negative Busbar', 'L2','Top', 'Exhaust Fan'] #thermal test name

#header = ['Date', 'Time'] + [f'Channel {i}' for i in channels] + ['Avg Temp (C)', 'Avg Temp (F)']
header = ['Date', 'Time'] + name + ['Avg Temp (C)', 'Avg Temp (F)'] #UL Test

####################################################################################
#filename = f'daq_measurements_{timestamp}.csv'
print('Enter output file name (without .csv extension):')
name_input = input().strip()  # Get user input and remove any leading/trailing whitespace
# Validate input
if not name_input:
    print("Error: Power Meter CSV name cannot be empty.")
    exit()
filename = f'{name_input}.csv'
###################################################################################

stop_logging = False

def check_for_stop():
    global stop_logging
    while not stop_logging:
        user_input = input().strip().lower()
        if user_input == 'stop':
            stop_logging = True
###############################################################

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

        # List all connected VISA resources
        resources = rm.list_resources()
        print("Available resources:", resources)

        # DAQ973A USB resource string
        daq_resource_string = 'USB0::10893::34305::MY59007195::0::INSTR'

        # Connect to the DAQ973A
        daq = rm.open_resource(daq_resource_string)
        daq.timeout = 10000  # Set timeout to 10 seconds

        # Print the IDN (Identification) string to verify connection
        print("Connected to:", daq.query('*IDN?').strip())

        # Configure channels for thermocouple temperature measurement in Fahrenheit
        thermocouple_type = 'J'
        for channel in channels:
            daq.write(f'CONF:TEMP TC,{thermocouple_type},(@{channel})')
            daq.write(f'UNIT:TEMP C,(@{channel})')  # Set unit to Celsius

        daq.write('INIT')
        time.sleep(0.5)
        

        # Perform multiple readings
        # Perform multiple readings
        reading_count = 0
        while not stop_logging:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"\nReading {reading_count + 1} at {timestamp}:")
            # Reset the sum_measurements for each reading cycle
            sum_measurements = [0.0] * len(channels)
            
            date1 = time.strftime('%m/%d/%Y')
            time1 = time.strftime('%H:%M:%S')
            csv_out = [date1, time1]

            for j, channel in enumerate(channels):
                measurement = daq.query(f'MEAS:TEMP? TC,{thermocouple_type},(@{channel})')
                measurement_value_c = float(measurement)
                #measurement_value_f = float((measurement_value_c * 1.8) + 32)
                #print(f'Channel {channel}: {measurement_value_f:.6f} °F')
                print(f'{name[j]}: {measurement_value_c:.6f} °C')
                csv_out.append(f'{measurement_value_c:.6f}')

                # Accumulate the sum for averaging
                sum_measurements[j] += measurement_value_c

            total_temp = sum(sum_measurements)

            temp_average_c = total_temp / len(sum_measurements)
            temp_average_f = (temp_average_c * 1.8) + 32

            print(f'Average Temp: {temp_average_c:.6f} °C')
            print(f'Average Temp: {temp_average_f:.6f} °F')

            csv_out.append(f'{temp_average_c:.6f}')
            csv_out.append(f'{temp_average_f:.6f}')
                
            # Write the measurements to the CSV file
            csvwriter.writerow(csv_out)
            time.sleep(2.5)  # Wait 2.5 seconds between readings
            reading_count += 1 #increase counter

except pyvisa.VisaIOError as e:
    print(f"VISA IO Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the connection
    if 'daq' in locals():
        daq.close()
        print("Connection closed.")

print('')
print('')
print('Press Enter to close')
input()

