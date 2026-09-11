import subprocess
import sys

print("--- Instalacja zależności ---")
install_result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
if install_result.returncode != 0:
    print("Błąd podczas instalacji pakietów z requirements.txt")
    sys.exit(install_result.returncode)

scripts = ["join_realm_configs.py"]

for script in scripts:
    print(f"--- Uruchamianie {script} ---")
    result = subprocess.run([sys.executable, script])
    if result.returncode != 0:
        print(f"Błąd podczas wykonywania {script}")
        sys.exit(result.returncode)