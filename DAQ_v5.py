import pyvisa
import time
import csv
import threading
import matplotlib.pyplot as plt

print('DAQ Datalogger: type "stop" to end the datalogging at anytime')
print('')

# Resource manager setup
rm = pyvisa.ResourceManager()

channels = ['105', '102', '119', '112', '111', '113','114','104','115', '103', '117', '101']
name = ['HS2', 'T3', 'L10', 'Output Fuse', 'L11', 'J23','Solder Side','HS1','Negative Busbar', 'L2','Top', 'Exhaust Fan']
header = ['Date', 'Time'] + name + ['Avg Temp (C)', 'Avg Temp (F)']

print('Enter output file name (without .csv extension):')
name_input = input().strip()
if not name_input:
    print("Error: CSV name cannot be empty.")
    exit()
csv_filename = f'{name_input}.csv'
png_filename = f'{name_input}.png'

stop_logging = False

def check_for_stop():
    global stop_logging
    while not stop_logging:
        user_input = input().strip().lower()
        if user_input == 'stop':
            stop_logging = True

# Create and start the thread for checking the stop command
input_thread = threading.Thread(target=check_for_stop)
input_thread.daemon = True
input_thread.start()

# Lists to store timestamps and temperature data for each channel
timestamps = []
channel_name_temps = {name[i]: [] for i in range(len(name))}
avg_temps_c = []

# Initialize the plot
plt.ion()  # Turn on interactive mode
fig, ax = plt.subplots(figsize=(12, 8))
lines = {channel: ax.plot([], [], label=f'Channel {channel}')[0] for channel in name}

# Set initial plot settings
ax.set_ylim(20, 100)
ax.set_xlim(0, 10)  # Initial xlim, will be updated dynamically
ax.set_xticks(range(0, 100, 5))
ax.set_yticks(range(20, 101, 5))
ax.minorticks_on()
ax.grid(which='both', axis='y')
ax.grid(which='minor', axis='y', linestyle=':', linewidth=0.5)
ax.set_xlabel('Time (min)', fontsize=20)
ax.set_ylabel('Temperature (°C)', fontsize=20)
ax.set_title('Temperature vs Time', fontsize=26)
ax.legend(loc='upper right', bbox_to_anchor=(1.27, 1), borderaxespad=0.)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.subplots_adjust(right=0.8)

try:
    # Open the CSV file for writing
    with open(csv_filename, 'w', newline='') as file:
        csvwriter = csv.writer(file)
        csvwriter.writerow(header)

        resources = rm.list_resources()
        print("Available resources:", resources)

        daq_resource_string = 'USB0::10893::34305::MY59007195::0::INSTR'
        daq = rm.open_resource(daq_resource_string)
        daq.timeout = 10000
        print("Connected to:", daq.query('*IDN?').strip())

        thermocouple_type = 'J'
        for channel in channels:
            daq.write(f'CONF:TEMP TC,{thermocouple_type},(@{channel})')
            daq.write(f'UNIT:TEMP C,(@{channel})')

        daq.write('INIT')
        time.sleep(0.5)

        time_start_h = int(time.strftime('%H'))
        time_start_m = int(time.strftime('%M'))
        time_start_s = int(time.strftime('%S'))
        time_start = (time_start_h * 60) + time_start_m + (time_start_s / 60)
        
        reading_count = 0
        while not stop_logging:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"\nReading {reading_count + 1} at {timestamp}:")
            sum_measurements = [0.0] * len(channels)
            
            date1 = time.strftime('%m/%d/%Y')
            time1 = time.strftime('%H:%M:%S')
            current_h = int(time.strftime('%H'))
            current_m = int(time.strftime('%M'))
            current_s = int(time.strftime('%S'))
            time_current = (current_h * 60) + current_m + (current_s / 60)
            delta_time = time_current - time_start
            csv_out = [date1, time1]

            for j, channel in enumerate(channels):
                measurement = daq.query(f'MEAS:TEMP? TC,{thermocouple_type},(@{channel})')
                measurement_value_c = float(measurement)
                print(f'{name[j]}: {measurement_value_c:.6f} °C')
                csv_out.append(f'{measurement_value_c:.6f}')

                sum_measurements[j] += measurement_value_c
                channel_name_temps[name[j]].append(measurement_value_c)

            total_temp = sum(sum_measurements)
            temp_average_c = total_temp / len(sum_measurements)
            temp_average_f = (temp_average_c * 1.8) + 32

            print(f'Average Temp: {temp_average_c:.6f} °C')
            print(f'Average Temp: {temp_average_f:.6f} °F')

            csv_out.append(f'{temp_average_c:.6f}')
            csv_out.append(f'{temp_average_f:.6f}')
                
            csvwriter.writerow(csv_out)

            timestamps.append(delta_time)
            avg_temps_c.append(temp_average_c)

            # Update plot
            for channel in name:
                lines[channel].set_data(timestamps, channel_name_temps[channel])
            
            # Update xlim to accommodate new data
            ax.set_xlim(0, max(timestamps) if timestamps else 10)
            ax.relim()
            ax.autoscale_view()
            
            plt.draw()
            plt.pause(0.1)  # Pause to update the plot

            time.sleep(0.5)
            reading_count += 1

except pyvisa.VisaIOError as e:
    print(f"VISA IO Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

finally:
    if 'daq' in locals():
        daq.close()
        print("Connection closed.")

    plt.ioff()  # Turn off interactive mode
    if timestamps and any(channel_name_temps.values()):
        plt.savefig(png_filename, format='png', bbox_inches='tight')
        plt.show()
        print(f'Plot saved as {png_filename}')
    else:
        print("No data available for plotting.")

print('Press Enter to close')
input()
