import threading
import socket
import time
import sys
import ipaddress

lock = threading.Lock()

linux_keywords = ['ubuntu', 'debian', 'linux', 'centos', 'fedora', 'redhat']

list_ips = open(sys.argv[1]).read().splitlines()
list_ips = iter(list_ips)

goods = 0
not_linux = 0
timeout = 0
refuse = 0
error = 0
status = True

found_hosts = []

def banner():
    global goods, not_linux, timeout, refuse, error
    print(f"\r Linux Servers: {goods} | Not Linux: {not_linux} | Timeout: {timeout} | Refused: {refuse} | Error: {error}", end="", flush=True)

def check_ssh(ip_port, timeout_=2):
    global goods, not_linux, timeout, refuse, error

    try:
        host_port = ip_port.strip().split("@")[0]
        host, port = host_port.split(":")
        port = int(port)
    except Exception:
        with lock:
            error += 1
        return False

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout_)
        try:
            s.connect((host, port))
            data = s.recv(1024).decode(errors='ignore')
            data_lower = data.lower()
            if "openssh" in data_lower and any(k in data_lower for k in linux_keywords):
                with lock:
                    goods += 1
                    found_hosts.append(f"{host}:{port}")
                return True
            else:
                with lock:
                    not_linux += 1
                return False
        except socket.timeout:
            with lock:
                timeout += 1
            return False
        except ConnectionRefusedError:
            with lock:
                refuse += 1
            return False
        except socket.error:
            with lock:
                error += 1
            return False
        except Exception:
            with lock:
                error += 1
            return False

def start():
    global list_ips, status
    while True:
        try:
            ip = next(list_ips)
            check_ssh(ip)
        except StopIteration:
            status = False
            break

if __name__ == "__main__":
    thread_count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    for _ in range(thread_count):
        threading.Thread(target=start, daemon=True).start()

    while status:
        banner()
        time.sleep(1)

    # ????????? ?? ???? IP ????
    def ip_sort_key(ip_port):
        ip, port = ip_port.split(":")
        return (ipaddress.ip_address(ip), int(port))

    sorted_hosts = sorted(found_hosts, key=ip_sort_key)

    with open("linux_servers.txt", "w") as f:
        for entry in sorted_hosts:
            f.write(entry + "\n")

    print("\nScan finished.")
    print(f"Linux Servers found: {goods}")
    print(f"Not Linux: {not_linux}")
    print(f"Timeouts: {timeout}")
    print(f"Connection Refused: {refuse}")
    print(f"Errors: {error}")
