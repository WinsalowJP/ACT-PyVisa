import pyvisa
import time
import csv
 
# Resource manager setup
rm = pyvisa.ResourceManager()
 
resources = rm.list_resources()
print("Available resources:", resources)
print("Enter device id (e.g., USB0::0x2A8D::0x0101::MY1234567::INSTR):")
# dmm_id = input() #for general testing.
 
dmm_id1 = 'USB0::0x2A8D::0x0301::MY54507560::INSTR' #uncomment for multimeter 1 ACT0012
dmm_id2 = 'USB0::0x2A8D::0x0301::MY54505907::INSTR' #uncomment for multimeter 2 ACT0011
 
# CSV file setup
timestamp = time.strftime('%Y%m%d-%H%M%S')
filename = f'Dual_DMM_Datalogger_{timestamp}.csv'
header = ['Date'] + ['Time'] + ['Voltage (V)'] + ['Current (A)'] + ['Voltage of shunt (V)'] + ['Power (kW)']
 
try:
    # Open the CSV file for writing
    with open(filename, 'w', newline='') as file:
        csvwriter = csv.writer(file)
       
        # Write the header
        csvwriter.writerow(header)
 
        # List all connected VISA resources
        resources = rm.list_resources()
        print("Available resources:", resources)
 
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
        
        # Example: Configure the multimeter for voltage measurement
        dmm1.write('CONF:VOLT:DC 10,0.001')  # Configure for DC voltage, range 10V, resolution 1mV
 
        # Example: Configure the multimeter for voltage measurement
        dmm2.write('CONF:VOLT:DC 10,0.0001')  # Configure for DC voltage, range 10V, resolution 1mV
 
        # Perform multiple readings
        num_readings = 100000  # Number of readings to take
        for i in range(num_readings):
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"\nReading {i + 1} at {timestamp}:")

            date1 = time.strftime('%m/%d/%Y')
            time1 = time.strftime('%H:%M:%S')
            csv_out = [date1, time1]
           
            # Reading the voltage measurement
            measurement1 = dmm1.query('MEAS:VOLT:DC?')
            voltage = float(measurement1)
            print(f'Voltage: {voltage:.6f} V')
            csv_out.append(f'{voltage:.6f}')
           
            # Reading the current measurement
            measurement2 = dmm2.query('MEAS:VOLT:DC?')
            voltage2 = float(measurement2)
            current = 5000 * voltage2 #convert mV to A
            power = current * voltage #current * voltage to get power
            power_out = power / 1000 #change unit to kW from W
            print(f'Current: {current:.6f} A')
            print(f'Power: {power_out:.6f} kW')
            csv_out.append(f'{current:.6f}')
            csv_out.append(f'{voltage2:.6f}')
            csv_out.append(f'{power_out:.6f}')

            # Write the measurements to the CSV file
            csvwriter.writerow(csv_out)
            time.sleep(0.2)  # Wait 1 second between readings
 
except pyvisa.VisaIOError as e:
    print(f"VISA IO Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
 
finally:
    # Close the connection
    if 'dmm1' in locals():
        dmm1.close()
        print("Connection closed.")
 
    if 'dmm2' in locals():
        dmm2.close()
        print("Connection closed.")