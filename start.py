import config
import subprocess
import sys
import os

for port in config.PORTS:
    try:
        print(f"Попытка запуска app.py на порту {port}...")
        if sys.platform.startswith('win'):
            command = ["start", "cmd", "/k", sys.executable, "app.py", str(port)]
            process = subprocess.Popen(command, shell=True)
        else:
            print(f"Открытие нового окна сейчас не поддерживается на {sys.platform}. Открытие в этом окне.")
            process = subprocess.Popen([sys.executable, "app.py", str(port)])

        print(f"Запущен процесс для порта {port} с PID: {process.pid}")
    except Exception as e:
        print(f"Ошибка запуска app.py для порта {port}: {e}")

print("Все процессы запущенны (или пробовали запустится).\nВы можете закрыть ЭТУ консоль.")