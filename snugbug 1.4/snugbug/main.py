import os
import subprocess


def main():
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "app.py"))
    subprocess.run(["python", script_path])


if __name__ == "__main__":
    main()
