import time
import random
import datetime

LOG_FILE = "access.log"

IPS = [
    "192.168.1.10",
    "10.0.0.50",
    "172.16.0.5",
    "192.168.1.100",
    "8.8.8.8",
    "10.10.10.10"
]

is_running = True

def generate_log():
    ip = random.choice(IPS)
    
    # 70% chance to be current time, 30% chance to be random hour for testing off-hours (outside 9-6)
    if random.random() < 0.3:
        hour = random.choice(list(range(0, 9)) + list(range(18, 24)))
        now = datetime.datetime.now().replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))
    else:
        now = datetime.datetime.now()
        
    # Bias towards Failed Login for some IPs to easily trigger Brute Force detection (e.g., 192.168.1.100)
    if ip == "192.168.1.100":
        status = random.choices(["Success Login", "Failed Login"], weights=[0.1, 0.9])[0]
    else:
        status = random.choices(["Success Login", "Failed Login"], weights=[0.7, 0.3])[0]

    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{timestamp_str} - {ip} - {status}\n"
    return log_line

def main():
    global is_running
    is_running = True
    print(f"Starting log simulator. Writing to '{LOG_FILE}'...")
    print("Press Ctrl+C to stop.")
    try:
        while is_running:
            log_line = generate_log()
            # Append log to file
            with open(LOG_FILE, "a") as f:
                f.write(log_line)
            print(f"Appended: {log_line.strip()}")
            
            # Sleep in short chunks so it can be interrupted instantly
            sleep_duration = random.uniform(0.5, 2.5)
            iterations = int(sleep_duration / 0.1)
            for _ in range(iterations):
                if not is_running:
                    break
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nSimulator stopped (Keyboard Interrupt).")
    
    print("Simulator thread terminated.")

if __name__ == "__main__":
    main()
