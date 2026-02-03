import os
import yaml
import uuid
import socket

def get_mac_address():
    mac = uuid.getnode()
    return ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))

def get_hostname():
    return socket.gethostname()

def generate_default_config():
    mac_address = get_mac_address()
    hostname = get_hostname()
    
    # Generate a unique ID based on hostname and MAC address
    agent_id = f"agent-{hostname}-{mac_address.replace(':', '')[-6:]}"

    config = {
        'platform': {
            'url': 'http://127.0.0.1:8000'
        },
        'agent': {
            'id': agent_id,
            'workspace': os.path.join(os.path.expanduser('~'), 'testhub_agent', 'workspace'),
            'tags': ['default']
        },
        'heartbeat': {
            'interval': 30
        },
        'task_polling': {
            'interval': 5
        },
        'logging': {
            'level': 'INFO',
            'path': os.path.join(os.path.expanduser('~'), 'testhub_agent', 'logs'),
            'filename': 'agent.log'
        },
        'git': {
            'token': '' # Optional: for private repositories
        }
    }
    return config

def load_config(config_path='config.yaml'):
    if not os.path.exists(config_path):
        print("Config file not found. Generating a default config.yaml...")
        default_config = generate_default_config()
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        print(f"Default config file created at {config_path}. Please review and edit it.")
        return default_config
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

if __name__ == '__main__':
    config = load_config()
    print("Current Configuration:")
    print(yaml.dump(config, default_flow_style=False))
