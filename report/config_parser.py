import json
import os


class BenchmarkConfig:
    
    def __init__(self, name, env, pre_execution_commands, post_bash_commands, post_hs_commands, custom_diff_script, command_working_dir, command, cleanup_commands, orch_args):
        self.name = name
        self.env = [self.replace_env_var(e) for e in env]
        self.pre_execution_commands = [self.replace_env_var(script) for script in pre_execution_commands]
        self.post_bash_commands = [self.replace_env_var(script) for script in post_bash_commands]
        self.post_hs_commands = [self.replace_env_var(script) for script in post_hs_commands]
        self.custom_diff_script = self.replace_env_var(custom_diff_script)
        self.command_working_dir = self.replace_env_var(command_working_dir)
        self.command = self.replace_env_var(command)
        self.cleanup_commands = self.replace_env_var(cleanup_commands)
        self.orch_args = self.replace_env_var(orch_args)
        
    def __repr__(self):
        return (f"BenchmarkConfig(name={self.name!r}, env={self.env!r}, "
                f"pre_execution_commands={self.pre_execution_commands!r}, "
                f"post_bash_commands={self.post_bash_commands!r}, "
                f"post_hs_commands={self.post_hs_commands!r}, "
                f"custom_diff_script={self.custom_diff_script!r}, "
                f"command_working_dir={self.command_working_dir!r}, "
                f"command={self.command!r}, orch_args={self.orch_args!r}, "
                f"cleanup_commands={self.cleanup_commands!r}, "
                f"orch_args={self.orch_args!r})")

    def __str__(self):
        env_str = ', '.join(self.env) if self.env else 'None'
        pre_exec_str = ', '.join(self.pre_execution_commands) if self.pre_execution_commands else 'None'
        return (f"Benchmark '{self.name}':\n"
                f"  > Environment Variables: {env_str}\n"
                f"  > Pre-execution Commands: {pre_exec_str}\n"
                f"  > Post-bash-execution Commands: {self.post_bash_commands}\n"
                f"  > Post-hs-execution Commands: {self.post_hs_commands}\n"
                f"  > Custom-diff Script: {self.custom_diff_script}\n"
                f"  > Command Working Directory: {self.command_working_dir}\n"
                f"  > Command: {self.command}\n"
                f"  > Cleanup Script: {self.cleanup_commands}\n"
                f"  > Orchestrator Arguments: {self.orch_args}")

    def setup_environment(self):
        for env_var in self.env:
            lhs, rhs = env_var.split("=")
            rhs = self.replace_env_var(rhs)
            os.environ[lhs] = rhs

    # Replaces placeholders in the string with environment variable values.
    def replace_env_var(self, string):
        if r'{{' in string and r'}}' in string:
            start = string.find(r'{{')
            end = string.find(r'}}')
            env_var = string[start + 2:end]
            return string[:start] + os.environ.get(env_var, '') + string[end + 2:]
        return string

class ConfigParser:
    def __init__(self, config_file):
        self.config_file = config_file
        self.benchmarks = []
        
    def __repr__(self):
        return f"ConfigParser(benchmarks={self.benchmarks!r})"

    def __str__(self):
        benchmark_details = '\n'.join(str(benchmark) for benchmark in self.benchmarks)
        return f"Configured Benchmarks:\n{benchmark_details}"
    
    def parse_config(self):
        with open(self.config_file, 'r') as file:
            configs = json.load(file)
            for config in configs:
                
                # Check if any expected list fields are actually strings 
                # and convert them if so
                env = config.get('env', [])
                pre_execution_commands = config.get('pre_execution_commands', [])
                post_bash_commands = config.get('post_bash_commands', [])
                post_hs_commands = config.get('post_hs_commands', [])
                cleanup_commands = config.get('cleanup_commands', [])
                
                env = [env] if isinstance(env, str) else env
                pre_execution_commands = [pre_execution_commands] if isinstance(pre_execution_commands, str) else pre_execution_commands
                post_bash_commands = [post_bash_commands] if isinstance(post_bash_commands, str) else post_bash_commands
                post_hs_commands = [post_hs_commands] if isinstance(post_hs_commands, str) else post_hs_commands
                cleanup_commands = [cleanup_commands] if isinstance(cleanup_commands, str) else cleanup_commands
                
                benchmark = BenchmarkConfig(
                    name=config.get('name'),
                    env=env,
                    pre_execution_commands=pre_execution_commands,
                    post_bash_commands=post_bash_commands,
                    post_hs_commands=post_hs_commands,
                    custom_diff_script=config.get('custom_diff_script', ""),
                    command_working_dir=config.get('working_dir', ""),
                    command=config.get('command'),
                    cleanup_commands=config.get('cleanup_commands', ""),
                    orch_args=config.get('orch_args', "")
                )
                self.benchmarks.append(benchmark)

    def get_benchmarks(self):
        return self.benchmarks
    
