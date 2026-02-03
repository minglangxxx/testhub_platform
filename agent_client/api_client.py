import requests
import logging
import time
from system_utils import get_system_info, get_resource_usage

logger = logging.getLogger("AgentClient")

class APIClient:
    def __init__(self, platform_url, agent_id, agent_version="1.0.0"):
        self.base_url = platform_url.rstrip('/')
        self.agent_id = agent_id
        self.agent_version = agent_version
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": f"TestHubAgent/{self.agent_version}"})

    def register(self):
        """Register the agent with the platform."""
        url = f"{self.base_url}/api/agents/register/"
        system_info = get_system_info()
        payload = {
            "agent_id": self.agent_id,
            "os_info": system_info.get('os_info'),
            "agent_version": self.agent_version,
            **get_resource_usage()
        }
        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Agent successfully registered/updated on the platform. Server response: {response.json()}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to register agent: {e}")
            return False

    def send_heartbeat(self, status="idle"):
        """Send a heartbeat to the platform."""
        url = f"{self.base_url}/api/agents/heartbeat/"
        payload = {
            "agent_id": self.agent_id,
            "status": status,
            "resources": get_resource_usage(),
            "agent_version": self.agent_version,
            "os_info": get_system_info().get('os_info')
        }
        try:
            response = self.session.post(url, json=payload, timeout=5)
            response.raise_for_status()
            logger.debug("Heartbeat sent successfully.")
            return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to send heartbeat: {e}")
            return False

    def poll_task(self):
        """Poll for a new task from the platform."""
        url = f"{self.base_url}/api/tasks/poll/"
        params = {"agent_id": self.agent_id}
        try:
            response = self.session.get(url, params=params, timeout=5)
            if response.status_code == 204:
                logger.debug("No pending tasks.")
                return None
            response.raise_for_status()
            task_data = response.json()
            logger.info(f"New task received: {task_data.get('name')} (ID: {task_data.get('id')})")
            return task_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to poll for tasks: {e}")
            return None

    def update_task_status(self, task_id, status, message=""):
        """Update the status of a task."""
        url = f"{self.base_url}/api/tasks/{task_id}/status/"
        payload = {"status": status, "message": message}
        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Updated status for task {task_id} to {status}.")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update status for task {task_id}: {e}")
            return False

    def send_task_log(self, task_id, log_type, content):
        """Send real-time logs for a task."""
        url = f"{self.base_url}/api/tasks/{task_id}/log/"
        payload = {
            "type": log_type,
            "content": content,
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S%z')
        }
        try:
            response = self.session.post(url, json=payload, timeout=5)
            response.raise_for_status()
            logger.debug(f"Log sent for task {task_id}.")
            return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to send log for task {task_id}: {e}")
            return False

    def upload_report(self, task_id, report_path, attachments=None):
        """Upload the report and attachments for a task."""
        url = f"{self.base_url}/api/reports/agent-reports/tasks/{task_id}/report/"
        files = {}
        try:
            files['report'] = open(report_path, 'rb')
            if attachments:
                files.update({f'attachments': open(att, 'rb') for att in attachments})

            response = self.session.post(url, files=files, timeout=300) # 5-minute timeout for upload
            response.raise_for_status()
            logger.info(f"Report for task {task_id} uploaded successfully.")
            return True
        except FileNotFoundError as e:
            logger.error(f"File not found for upload: {e}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload report for task {task_id}: {e}")
            return False
        finally:
            for f in files.values():
                if f:
                    f.close()
