import subprocess
import time
import os

class CommandExecutor:
    
    @staticmethod
    def run_setup_script(script_path, working_dir=os.getcwd(), verbose=False):
        if verbose:
            print("Running benchmark setup script:", )
            process = subprocess.Popen(f"bash {script_path}", cwd=working_dir, shell=True, env=os.environ)
        else:
            process = subprocess.Popen(f"bash {script_path}", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=working_dir, shell=True, env=os.environ)
        process.wait()
        return process.returncode
    
    @staticmethod
    def run_pre_execution_command(command, working_dir=os.getcwd(), verbose=False):
        if verbose:
            print("Running pre-execution command:", command)
            process = subprocess.Popen(command, cwd=working_dir, shell=True)
        else:
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=working_dir, shell=True)
        process.wait()
        return process.returncode

    @staticmethod
    def run_command(command, working_dir=os.getcwd(), verbose=False):
        if verbose:
            print("Running (and timing) command: ", " ".join(command))
        start_time = time.time()
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_dir, shell=True, env=os.environ)
        stdout, stderr = process.communicate()
        end_time = time.time()
        return end_time - start_time, stdout.decode('utf-8'), stderr.decode('utf-8')

    @staticmethod
    def run_command_with_orch(command, orch_args, working_dir=os.getcwd(), orch_command=None, verbose=False):
        if orch_command is None:
            raise ValueError("Orchestrator command (ORCH_COMMAND) is not set.")

        orch_args = orch_args.split(" ")
        full_command = [orch_command] + orch_args + command
        if verbose:
            print("Running (and timing) command with orch: ", " ".join(full_command))
        start_time = time.time()
        process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_dir, env=os.environ)
        stdout, stderr = process.communicate()
        end_time = time.time()
        return end_time - start_time, stdout.decode('utf-8'), stderr.decode('utf-8')
    
    @staticmethod
    def run_post_execution_diff_script(script_path, working_dir=os.getcwd(), verbose=False):
        if verbose:
            print("Running custom diff script:", script_path)
        process = subprocess.Popen(f"bash {script_path}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_dir, shell=True, env=os.environ)
        stdout, stderr = process.communicate()
        return process.returncode, stdout.decode('utf-8').split('\n'), stderr.decode('utf-8').split('\n')
    
    @staticmethod
    def run_post_execution_command(command, working_dir=os.getcwd(), verbose=False):
        if verbose:
            print("Running post-execution command:", command)
            process = subprocess.Popen(command, cwd=working_dir, shell=True)
        else:
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=working_dir, shell=True)
        process.wait()
        return process.returncode
    

