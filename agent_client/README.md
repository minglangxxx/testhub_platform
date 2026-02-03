# TestHub Agent

This is the client-side agent for the TestHub platform. It runs on your test servers, polls for tasks, executes them, and reports back the results.

## Features

- **Heartbeat:** Keeps the platform updated on the agent's status and resource usage.
- **Task Polling:** Fetches new tasks from the platform.
- **Isolated Workspaces:** Each task runs in its own directory.
- **Command Execution:** Can run any shell script.
- **Real-time Logging:** Streams `stdout` and `stderr` back to the platform.
- **Git Integration:** Can clone repositories for a task.
- **Allure Reports:** Automatically generates and uploads Allure reports if `allure-results` are found.
- **Configurable:** All settings are managed via a `config.yaml` file.

## Setup and Installation

1.  **Clone the repository or download the `agent_client` directory.**

2.  **Install dependencies:**

    It is highly recommended to use a virtual environment.

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Configure the Agent:**

    The first time you run the agent, it will generate a `config.yaml` file if one doesn't exist.

    ```yaml
    platform:
      url: 'http://127.0.0.1:8000'  # URL of your TestHub platform
    agent:
      id: 'agent-hostname-abcdef'   # A unique ID for the agent (auto-generated)
      workspace: '/path/to/your/workspace' # Directory to store task files
      tags:
        - default
        - windows
    heartbeat:
      interval: 30 # Seconds
    task_polling:
      interval: 5  # Seconds
    logging:
      level: 'INFO'
      path: '/path/to/your/logs'
      filename: 'agent.log'
    git:
      token: '' # Optional: GitHub/GitLab personal access token for private repos
    ```

    **Important:** You must update `platform.url` to point to your running TestHub server.

4.  **Ensure `allure` is in your system's PATH (Optional):**

    If you want the agent to generate Allure reports, the `allure` command-line tool must be installed and accessible in the environment where the agent is running.

## Running the Agent

To start the agent, simply run the `main.py` script:

```bash
python main.py
```

The agent will start, register itself with the platform, and begin polling for tasks. You can stop it by pressing `Ctrl+C`.

## Building the Agent into an Executable

To make deployment easier, you can package the agent into a single binary file using PyInstaller. A build script is provided.

1.  **Install PyInstaller:**

    ```bash
    pip install pyinstaller
    ```

2.  **Run the build script:**

    ```bash
    python build.py
    ```

    This script will:
    - Clean up old build files.
    - Run PyInstaller to create a single executable file in the `dist` directory.
    - Copy a default `config.yaml` next to the executable.
    - Create a zip archive of the `dist` folder for easy distribution.

    The final executable will be located at `dist/testhub_agent` (or `dist/testhub_agent.exe` on Windows).

## Running as a Service (Linux - systemd/supervisor)

To run the agent as a background service on Linux, you can use `systemd` or `supervisor`.

### Using systemd

1.  Create a file named `testhub-agent.service` in `/etc/systemd/system/`:

    ```ini
    [Unit]
    Description=TestHub Agent
    After=network.target

    [Service]
    User=your_user # Replace with the user you want to run the agent as
    Group=your_group # Replace with the group
    # The directory where you placed the built agent and config.yaml
    WorkingDirectory=/opt/testhub-agent 
    # The command to run the executable
    ExecStart=/opt/testhub-agent/testhub_agent
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```

2.  Reload systemd, enable, and start the service:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable testhub-agent.service
    sudo systemctl start testhub-agent.service
    ```

### Using Supervisor

1.  Install Supervisor:
    ```bash
    sudo apt-get install supervisor # On Debian/Ubuntu
    ```

2.  Create a configuration file for the agent, e.g., `/etc/supervisor/conf.d/testhub-agent.conf`:

    ```ini
    [program:testhub-agent]
    command=/opt/testhub-agent/testhub_agent
    directory=/opt/testhub-agent
    autostart=true
    autorestart=true
    user=your_user
    stdout_logfile=/var/log/supervisor/testhub-agent.log
    stderr_logfile=/var/log/supervisor/testhub-agent.err.log
    ```

3.  Tell Supervisor to read the new config and start the process:
    ```bash
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl start testhub-agent
    ```

4.  You can check the status with:
    ```bash
    sudo supervisorctl status testhub-agent
    ```

