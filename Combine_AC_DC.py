import time
import csv

# Header for the final combined CSV
combine_header = ['Date', 'Time', 'V1 (V)', 'A1 (A)', 'P1 (kW)', 'V2 (V)', 'A2 (A)', 'P2 (kW)', 'V3 (V)', 'A3 (A)', 'P3 (kW)', 'Total Power (kW)', 'DC Volt (V)', 'DC Current (A)', 'DC Power (W)', 'Efficiency']

# Dictionaries to hold data from CSV files
pm_data = {}
com_data = {}

# Generate timestamp for the output filenames
timestamp = time.strftime('%m%d%Y-%H%M%S')

print('Enter name of Power Meter CSV (without .csv extension):')
pm_csv_in = input().strip()  # Get user input and remove any leading/trailing whitespace

# Validate input
if not pm_csv_in:
    print("Error: Power Meter CSV name cannot be empty.")
    exit()
pm_csv = f'{pm_csv_in}.csv'

# Prompt the user for the name of the Multimeter CSV
print('Enter name of Multimeter CSV (without .csv extension):')
combined_csv_in = input().strip()  # Get user input and remove any leading/trailing whitespace

# Validate input
if not combined_csv_in:
    print("Error: Multimeter CSV name cannot be empty.")
    exit()
combined_csv = f'{combined_csv_in}.csv'

print('Enter a name for the output CSV (without .csv extension):')
output_filename_in = input().strip()  # Get user input and remove any leading/trailing whitespace

# Validate input
if not output_filename_in:
    print("Error: Output file CSV name cannot be empty.")
    exit()
output_filename = f'{output_filename_in}.csv'

#output_filename = f'{timestamp}_combined_ACDC.csv' #default timestamp output filename

def convert_time(time_str):
    """
    Convert a time string from 12-hour format with AM/PM to 24-hour format.
    """
    try:
        if 'AM' in time_str or 'PM' in time_str:
            time_part, period = time_str.split()
            hours, minutes, seconds = map(int, time_part.split(':'))

            if period.upper() == 'PM' and hours != 12:
                hours += 12
            elif period.upper() == 'AM' and hours == 12:
                hours = 0

            return f'{hours:02}:{minutes:02}:{seconds:02}'
        else:
            return time_str
    except ValueError:
        raise ValueError(f"Invalid time format: {time_str}")

# Read Power Meter data
with open(pm_csv, 'r') as file:
    pm_csvreader = csv.reader(file)
    for _ in range(11):  # Skip the first 11 rows
        next(pm_csvreader)
    for value in pm_csvreader:
        if len(value) > 26:
            time_val = convert_time(value[2])
            pm_data[time_val] = {
                'date': value[1],
                'v1': float(value[3]),
                'a1': float(value[4]),
                'p1': float(value[5]),
                'v2': float(value[9]),
                'a2': float(value[10]),
                'p2': float(value[11]),
                'v3': float(value[15]),
                'a3': float(value[16]),
                'p3': float(value[17]),
                'total_power': float(value[24])
            }

# Read Combined DMM data
with open(combined_csv, 'r') as file:
    com_csvreader = csv.reader(file)
    next(com_csvreader)  # Skip the header row
    for value in com_csvreader:
        if len(value) > 5:
            time_val = convert_time(value[1])
            com_data[time_val] = {
                'date': value[0],
                'volt': f"{float(value[2]):.3f}",
                'current': f"{float(value[3]):.3f}",
                'power': float(value[5])
            }

# Process and write combined data to the final CSV file
with open(output_filename, 'w', newline='') as file:
    csvwriter = csv.writer(file)
    csvwriter.writerow(combine_header)  # Write header row

    for com_time_val, com_info in com_data.items():
        if com_time_val in pm_data:
            pm_info = pm_data[com_time_val]
            efficiency = com_info['power'] / pm_info['total_power'] if pm_info['total_power'] != 0 else 0

            outrow = [
                com_info['date'],  # Date
                com_time_val,  # Time
                pm_info['v1'],  # V1
                pm_info['a1'],  # A1
                pm_info['p1'],  # Power 1
                pm_info['v2'],  # V2
                pm_info['a2'],  # A2
                pm_info['p2'],  # Power 2
                pm_info['v3'],  # V3
                pm_info['a3'],  # A3
                pm_info['p3'],  # Power 3
                pm_info['total_power'],  # Total power
                com_info['volt'],  # DC Voltage
                com_info['current'],  # DC Current
                com_info['power'],  # DC Power
                f"{efficiency:.4f}"  # Efficiency, formatted to 4 decimal places
            ]
            csvwriter.writerow(outrow)
        else:
            print(f"No matching time found for Time: {com_time_val}")

print('')
print(f'Processed combined data written to {output_filename}')
print('')
print('Press Enter to close')
input()