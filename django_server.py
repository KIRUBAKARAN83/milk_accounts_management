import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import webbrowser

PROJECT_PATH = r"D:\project\milk_accounts\milk_accounts"

server_process = None


# ==============================
# LOGGING FUNCTION
# ==============================
def log(msg):
    console.insert(tk.END, msg + "\n")
    console.see(tk.END)


# ==============================
# GENERIC COMMAND RUNNER
# ==============================
def run_command(cmd):

    process = subprocess.Popen(
        cmd,
        cwd=PROJECT_PATH,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout: # pyright: ignore[reportOptionalIterable]
        log(line.strip())


# ==============================
# START DJANGO SERVER
# ==============================
def start_server():
    global server_process

    if server_process and server_process.poll() is None:
        log("Server already running")
        return

    def run():
        global server_process

        log("Starting Django server...\n")

        server_process = subprocess.Popen(
            ["python", "manage.py", "runserver"],
            cwd=PROJECT_PATH,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in server_process.stdout: # pyright: ignore[reportOptionalIterable]
            log(line.strip())

    threading.Thread(target=run, daemon=True).start()

    webbrowser.open("http://127.0.0.1:8000")


# ==============================
# STOP DJANGO SERVER
# ==============================
def stop_server():
    global server_process

    if server_process and server_process.poll() is None:
        server_process.kill()
        server_process = None
        log("Server stopped successfully")
    else:
        log("Server is not running")


# ==============================
# DJANGO COMMANDS
# ==============================
def run_migrations():
    threading.Thread(
        target=lambda: run_command(["python", "manage.py", "migrate"]),
        daemon=True
    ).start()


def create_superuser():
    threading.Thread(
        target=lambda: run_command(["python", "manage.py", "createsuperuser"]),
        daemon=True
    ).start()


def collect_static():
    threading.Thread(
        target=lambda: run_command(
            ["python", "manage.py", "collectstatic", "--noinput"]
        ),
        daemon=True
    ).start()


def open_admin():
    webbrowser.open("http://127.0.0.1:8000/admin")


# ==============================
# GUI SETUP
# ==============================
root = tk.Tk()
root.title("Django Control Panel")
root.geometry("600x450")

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Button(
    frame,
    text="Start Server",
    width=18,
    command=start_server
).grid(row=0, column=0, padx=5, pady=5)

tk.Button(
    frame,
    text="Stop Server",
    width=18,
    command=stop_server
).grid(row=0, column=1, padx=5, pady=5)

tk.Button(
    frame,
    text="Run Migrations",
    width=18,
    command=run_migrations
).grid(row=1, column=0, padx=5, pady=5)

tk.Button(
    frame,
    text="Create Superuser",
    width=18,
    command=create_superuser
).grid(row=1, column=1, padx=5, pady=5)

tk.Button(
    frame,
    text="Collect Static",
    width=18,
    command=collect_static
).grid(row=2, column=0, padx=5, pady=5)

tk.Button(
    frame,
    text="Open Admin Panel",
    width=18,
    command=open_admin
).grid(row=2, column=1, padx=5, pady=5)

console = scrolledtext.ScrolledText(root, height=18)
console.pack(fill="both", expand=True, padx=10, pady=10)

root.mainloop()