# build.py
import os
import shutil
import subprocess
import platform

# --- Configuration ---
APP_NAME = "testhub_agent"
ENTRY_POINT = "main.py"
CONFIG_FILE = "config.yaml"
DIST_DIR = "dist"
BUILD_DIR = "build"

def build():
    """
    Build the agent into a single executable using PyInstaller.
    """
    print("Starting the build process...")

    # 1. Clean up previous builds
    print("Cleaning up previous build artifacts...")
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    
    # 2. Run PyInstaller
    pyinstaller_command = [
        "pyinstaller",
        "--name", APP_NAME,
        "--onefile",
        "--clean",
        "--noconfirm",
        ENTRY_POINT,
    ]

    # Add platform-specific options if needed
    if platform.system() == "Windows":
        pyinstaller_command.append("--icon=assets/icon.ico") # Example for icon
    
    print(f"Running PyInstaller command: {' '.join(pyinstaller_command)}")
    
    try:
        subprocess.run(pyinstaller_command, check=True)
        print("PyInstaller build completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller build failed: {e}")
        return
    except FileNotFoundError:
        print("Error: pyinstaller command not found. Make sure PyInstaller is installed and in your PATH.")
        return

    # 3. Post-build steps: Copy config file
    print("Copying default configuration file...")
    dist_path = os.path.join(DIST_DIR)
    
    # Generate a default config to be placed alongside the executable
    if not os.path.exists(os.path.join(dist_path, CONFIG_FILE)):
        from config import generate_default_config, yaml
        default_config = generate_default_config()
        with open(os.path.join(dist_path, CONFIG_FILE), 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        print(f"Default '{CONFIG_FILE}' created in '{dist_path}'.")

    # 4. Create a simple distribution package (optional)
    print("Creating a distribution package...")
    package_name = f"{APP_NAME}-{platform.system().lower()}-{platform.machine()}"
    shutil.make_archive(os.path.join(DIST_DIR, package_name), 'zip', dist_path)
    
    print("\nBuild process finished!")
    print(f"Executable created at: {os.path.join(dist_path, APP_NAME)}")
    print(f"Distribution package: {os.path.join(DIST_DIR, package_name + '.zip')}")

if __name__ == "__main__":
    # Create dummy assets if they don't exist (for icon example)
    if not os.path.exists("assets"):
        os.makedirs("assets")
    if not os.path.exists("assets/icon.ico"):
        # Create a dummy file, replace with your actual icon
        with open("assets/icon.ico", "w") as f:
            pass

    build()
