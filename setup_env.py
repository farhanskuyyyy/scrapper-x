import os
import sys
import subprocess
import shutil

def run_command(command):
    print(f"Running: {command}")
    try:
        subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False

def main():
    print("==================================================")
    print("PIPELINE SETUP & DEPENDENCIES INSTALLER")
    print("==================================================")
    
    # 1. Create virtual environment if it does not exist
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        if not run_command(f'"{sys.executable}" -m venv venv'):
            print("Failed to create virtual environment. Exiting.")
            sys.exit(1)
        print("Virtual environment created successfully.")
        
    # Determine python/pip executables inside virtual environment
    is_windows = os.name == 'nt'
    if is_windows:
        pip_path = os.path.join("venv", "Scripts", "pip.exe")
        python_path = os.path.join("venv", "Scripts", "python.exe")
    else:
        pip_path = os.path.join("venv", "bin", "pip")
        python_path = os.path.join("venv", "bin", "python")
        
    print(f"Using pip path: {pip_path}")
    print(f"Using python path: {python_path}\n")
    
    # 2. Upgrade pip
    print("Upgrading pip...")
    run_command(f'"{pip_path}" install --upgrade pip')
    print()

    # 3. Install base dependencies from requirements.txt
    print("Installing base python packages from requirements.txt...")
    if not run_command(f'"{pip_path}" install -r requirements.txt'):
        print("Failed to install base dependencies. Exiting.")
        sys.exit(1)
        
    # 4. Check and install patched twifork
    print("\nChecking twikit/twifork library status...")
    try:
        # Try importing twikit Client from virtual env python to check status
        test_import_cmd = f'"{python_path}" -c "from twikit import Client; print(\'Import check passed!\')"'
        subprocess.run(test_import_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Twikit library is already installed and patched correctly.")
    except subprocess.CalledProcessError:
        print("Twikit library is missing or broken. Initiating twifork git patch...")
        
        # Define temp clone folder
        temp_dir = "temp_twifork"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            
        # Clone twifork
        if not run_command("git clone https://github.com/PawiX25/twifork.git temp_twifork"):
            print("Failed to clone twifork from Git. Please verify git is installed.")
            sys.exit(1)
            
        # Patch __init__.py inside twikit/client to satisfy setuptools folder copying
        init_file = os.path.join(temp_dir, "twikit", "client", "__init__.py")
        print(f"Applying patch: creating {init_file}")
        with open(init_file, "w") as f:
            pass # write empty file
            
        # Install from local patched directory
        if not run_command(f'"{pip_path}" install ./temp_twifork'):
            print("Failed to install patched twifork package. Exiting.")
            sys.exit(1)
            
        # Clean up cloned folder
        print("Cleaning up temporary clone files...")
        shutil.rmtree(temp_dir)
        print("Successfully installed and patched twifork!")

    print("\n==================================================")
    print("SETUP COMPLETED SUCCESSFULLY!")
    print("==================================================")
    print("You can now run the pipeline:")
    if is_windows:
        print("venv\\Scripts\\python main.py --mode run-all")
    else:
        print("venv/bin/python main.py --mode run-all")
    print("==================================================\n")

if __name__ == "__main__":
    main()
