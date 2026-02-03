import logging
import os
import zipfile
import subprocess

logger = logging.getLogger("AgentClient")

class ReportProcessor:
    def __init__(self, api_client):
        self.api_client = api_client

    def process_and_upload(self, task_id, workspace_path):
        allure_results_dir = os.path.join(workspace_path, 'allure-results')
        allure_report_dir = os.path.join(workspace_path, 'allure-report')
        
        if not os.path.exists(allure_results_dir) or not os.listdir(allure_results_dir):
            logger.info(f"No Allure results found in {allure_results_dir} for task {task_id}. Skipping report generation.")
            return

        logger.info(f"Generating Allure report for task {task_id}")
        try:
            # Ensure allure command is available in PATH or provide full path
            subprocess.run(
                ['allure', 'generate', allure_results_dir, '-o', allure_report_dir, '--clean'],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Allure report generated successfully.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Failed to generate Allure report: {e}")
            if isinstance(e, subprocess.CalledProcessError):
                logger.error(f"Allure command output: {e.stderr}")
            return

        # Compress the report for upload
        report_zip_path = os.path.join(workspace_path, f"allure-report-{task_id}.zip")
        logger.info(f"Compressing report to {report_zip_path}")
        try:
            with zipfile.ZipFile(report_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(allure_report_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, allure_report_dir)
                        zipf.write(file_path, arcname)
        except Exception as e:
            logger.error(f"Failed to compress report: {e}")
            return

        # Find other attachments (e.g., logs, screenshots)
        # This is a simple example; can be extended based on conventions
        attachments = []
        for root, _, files in os.walk(workspace_path):
            if 'allure-report' in root or 'allure-results' in root:
                continue
            for file in files:
                if file.endswith(('.log', '.png', '.jpg')):
                    attachments.append(os.path.join(root, file))

        # Upload the report
        self.api_client.upload_report(task_id, report_zip_path, attachments)
