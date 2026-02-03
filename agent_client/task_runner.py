import os
import subprocess
import logging
import shutil
import time
import threading
from contextlib import contextmanager

logger = logging.getLogger("AgentClient")

class WorkspaceManager:
    def __init__(self, base_path):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    @contextmanager
    def task_workspace(self, task_id, clean_before=False):
        workspace_path = os.path.join(self.base_path, task_id)
        
        if clean_before and os.path.exists(workspace_path):
            logger.info(f"Cleaning up workspace for task {task_id}")
            shutil.rmtree(workspace_path)
            
        os.makedirs(workspace_path, exist_ok=True)
        
        try:
            yield workspace_path
        finally:
            # Cleanup logic can be added here if needed, e.g., based on task config
            pass

class CommandExecutor:
    def __init__(self, api_client):
        self.api_client = api_client
        self.process = None
        self.is_timed_out = False

    def _stream_output(self, stream, log_type, task_id):
        try:
            for line in iter(stream.readline, ''):
                line = line.strip()
                if line:
                    logger.info(f"[{task_id}-{log_type}] {line}")
                    self.api_client.send_task_log(task_id, log_type, line)
        except Exception as e:
            logger.error(f"Error streaming {log_type} for task {task_id}: {e}")
        finally:
            stream.close()

    def execute(self, command, workspace, task_id, env_vars=None, timeout=1800):
        self.is_timed_out = False
        
        full_env = os.environ.copy()
        if env_vars:
            full_env.update(env_vars)
            
        try:
            self.process = subprocess.Popen(
                command,
                cwd=workspace,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                env=full_env
            )

            stdout_thread = threading.Thread(target=self._stream_output, args=(self.process.stdout, 'stdout', task_id))
            stderr_thread = threading.Thread(target=self._stream_output, args=(self.process.stderr, 'stderr', task_id))
            
            stdout_thread.start()
            stderr_thread.start()

            # Wait for the process to complete or timeout
            self.process.wait(timeout=timeout)

            stdout_thread.join()
            stderr_thread.join()

            return self.process.returncode
        
        except subprocess.TimeoutExpired:
            logger.warning(f"Task {task_id} timed out after {timeout} seconds. Terminating process.")
            self.is_timed_out = True
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.error(f"Failed to terminate process for task {task_id}. Killing it.")
                self.process.kill()
            return -1 # Indicate timeout
        except Exception as e:
            logger.error(f"An error occurred while executing command for task {task_id}: {e}")
            return 1 # Indicate general error

class GitManager:
    def __init__(self, token=None):
        self.token = token

    def clone(self, repo_url, workspace_path, branch='main'):
        logger.info(f"Cloning repository {repo_url} (branch: {branch}) into {workspace_path}")
        
        if self.token:
            # Inject token into URL for HTTPS cloning
            if "https://" in repo_url:
                repo_url = repo_url.replace("https://", f"https://oauth2:{self.token}@")

        command = ['git', 'clone', '--branch', branch, repo_url, '.'] # Clone into current dir
        
        try:
            result = subprocess.run(
                command,
                cwd=workspace_path,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Git clone successful.")
            logger.debug(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed: {e.stderr}")
            return False
