import time
import logging
import threading
from config import load_config
from logger import setup_logging
from api_client import APIClient
from task_runner import WorkspaceManager, CommandExecutor, GitManager
from report_processor import ReportProcessor

class Agent:
    def __init__(self, config):
        self.config = config
        self.logger = setup_logging(config)
        self.agent_id = config['agent']['id']
        self.api_client = APIClient(config['platform']['url'], self.agent_id)
        self.workspace_manager = WorkspaceManager(config['agent']['workspace'])
        self.command_executor = CommandExecutor(self.api_client)
        self.report_processor = ReportProcessor(self.api_client)
        self.git_manager = GitManager(config.get('git', {}).get('token'))
        
        self.status = "idle"
        self.is_running = True
        self.heartbeat_thread = None
        self.task_polling_thread = None

    def start(self):
        self.logger.info(f"Starting TestHub Agent (ID: {self.agent_id})")
        if not self.api_client.register():
            self.logger.error("Agent registration failed. Please check platform URL and network. Exiting.")
            return

        self.is_running = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.task_polling_thread = threading.Thread(target=self._task_polling_loop)
        
        self.heartbeat_thread.start()
        self.task_polling_thread.start()

        self.logger.info("Agent started and is running.")

    def stop(self):
        self.logger.info("Stopping agent...")
        self.is_running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join()
        if self.task_polling_thread:
            self.task_polling_thread.join()
        self.logger.info("Agent stopped.")

    def _heartbeat_loop(self):
        interval = self.config['heartbeat']['interval']
        while self.is_running:
            self.api_client.send_heartbeat(self.status)
            time.sleep(interval)

    def _task_polling_loop(self):
        interval = self.config['task_polling']['interval']
        while self.is_running:
            if self.status == "idle":
                task_data = self.api_client.poll_task()
                if task_data:
                    self.status = "busy"
                    self.api_client.send_heartbeat(self.status) # Immediately update status
                    self.execute_task(task_data)
                    self.status = "idle"
            time.sleep(interval)

    def execute_task(self, task_data):
        task_id = task_data['id']
        self.logger.info(f"Starting execution for task: {task_data['name']} ({task_id})")
        self.api_client.update_task_status(task_id, "running")

        clean_workspace = task_data.get('workspace_clean', True)
        
        with self.workspace_manager.task_workspace(task_id, clean_before=clean_workspace) as workspace:
            # Git clone if repo is specified
            git_info = task_data.get('git_repo')
            if git_info and git_info.get('url'):
                if not self.git_manager.clone(git_info['url'], workspace, git_info.get('branch', 'main')):
                    self.logger.error(f"Failed to clone repository for task {task_id}.")
                    self.api_client.update_task_status(task_id, "failed", "Git clone failed")
                    return

            # Execute script
            script = task_data['script']
            env_vars = task_data.get('env_vars')
            timeout = task_data.get('timeout', 1800)
            
            return_code = self.command_executor.execute(script, workspace, task_id, env_vars, timeout)

            # Process reports
            self.report_processor.process_and_upload(task_id, workspace)

            # Final status update
            if self.command_executor.is_timed_out:
                self.api_client.update_task_status(task_id, "timeout")
            elif return_code == 0:
                self.api_client.update_task_status(task_id, "success")
            else:
                self.api_client.update_task_status(task_id, "failed", f"Script exited with code {return_code}")
        
        self.logger.info(f"Finished execution for task {task_id}")


def main():
    config = load_config()
    agent = Agent(config)
    
    try:
        agent.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()

if __name__ == '__main__':
    main()
