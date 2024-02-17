import subprocess
import time
import csv
import sys

def format_time(seconds):
    # Format time as ss.msms where msms is in milliseconds
    return "{:.4f}".format(seconds)

def time_commands(shell_script_path):
    # Read the shell script
    with open(shell_script_path, 'r') as file:
        commands = file.readlines()
    
    # Prepare the CSV output
    csv_filename = shell_script_path + "_timing.csv"
    with open(csv_filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["Command", "Time (seconds)"])
        
        # Initialize total time
        total_time = 0.0
        
        # Execute each command and time it
        for command in commands:
            command = command.strip()
            if command and not command.startswith('#'):  # Ignore empty lines and comments
                start_time = time.time()
                try:
                    # Run the command
                    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    execution_time = time.time() - start_time
                    # Write the result to the CSV with formatted time
                    csvwriter.writerow([command, format_time(execution_time)])
                    total_time += execution_time
                except subprocess.CalledProcessError as e:
                    print(f"An error occurred while executing the command: {command}")
                    print(e.output.decode())
                    sys.exit(1)
        
        # Write the total time with formatted time
        csvwriter.writerow(["Total", format_time(total_time)])

    print(f"Timing results written to {csv_filename}")

# Usage: python time_script.py /path/to/your/script.sh
if len(sys.argv) > 1:
    time_commands(sys.argv[1])
else:
    print("Please provide the path to the shell script as an argument.")
