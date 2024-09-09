import pyvisa
import time
import csv

# Resource manager setup
rm = pyvisa.ResourceManager()

# CSV file setup
channels = ['101', '102', '103','104','105','111','115','116','117','118','119','120']  # Channels from 101 to 120
timestamp = time.strftime('%Y%m%d-%H%M%S')
filename = f'daq_measurements{timestamp}.csv'
header = ['Date'] + ['Time'] + [f'Channel {i}' for i in channels]

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

        # Example: Configure multiple channels and read measurements
        channels = ['101', '102', '103','104','105','111','115','116','117','118','119','120']  # Channels from 101 to 120
        #channels = ['101', '102', '103','104','105','106','107','108','109','110','111','112','113','114','115','116','117','118','119','120']  # Channels from 101 to 120
        thermocouple_type = 'J'

        # Configure channels for thermocouple temperature measurement in Fahrenheit
        for channel in channels:
            daq.write(f'CONF:TEMP TC,{thermocouple_type},(@{channel})')
            daq.write(f'UNIT:TEMP F,(@{channel})')  # Set unit to Fahrenheit


        # Perform multiple readings
        num_readings = 10  # Number of readings to take
        for i in range(num_readings):
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"\nReading {i + 1} at {timestamp}:")
            daq.write('INIT')
            time.sleep(0.5)

            date1 = time.strftime('%m/%d/%Y')
            time1 = time.strftime('%H:%M:%S')
            csv_out = [date1,time1]
            for channel in channels:
                measurement = daq.query(f'MEAS:TEMP? TC,{thermocouple_type},(@{channel})')
                measurement_value_c = float(measurement)
                measurement_value_f = float((measurement_value_c*(1.8))+32)
                print(f'Channel {channel}: {measurement_value_f:.6f} °F')
                csv_out.append(f'{measurement_value_f:.6f}')
            
            
            
            # Write the measurements to the CSV file
            csvwriter.writerow(csv_out)
            time.sleep(1)  # Wait 1 second between readings

except pyvisa.VisaIOError as e:
    print(f"VISA IO Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the connection
    if 'daq' in locals():
        daq.close()
        print("Connection closed.")

        