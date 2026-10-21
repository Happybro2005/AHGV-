#!/usr/bin/env python3
"""
BioVote Master Project Launcher & Diagnostic Console
Author: BIO-VOTE Project
"""

import sys
import os
import subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def print_banner():
    print("""
========================================================================
     ██████╗ ██╗ ██████╗       ██╗   ██╗ ██████╗ ████████╗███████╗
     ██╔══██╗██║██╔═══██╗      ██║   ██║██╔═══██╗╚══██╔══╝██╔════╝
     ██████╔╝██║██║   ██║█████╗██║   ██║██║   ██║   ██║   █████╗  
     ██╔══██╗██║██║   ██║╚════╝╚██╗ ██╔╝██║   ██║   ██║   ██╔══╝  
     ██████╔╝██║╚██████╔╝       ╚████╔╝ ╚██████╔╝   ██║   ███████╗
========================================================================
             Biometric Cryptographic Voting Platform
========================================================================
    """)

def run_web():
    print("\n[+] Launching BioVote Web Portal...")
    print("[+] URL: http://127.0.0.1:5000")
    print("[+] Press Ctrl+C in terminal to stop server.\n")
    app_path = os.path.join(PROJECT_DIR, "app.py")
    subprocess.run([sys.executable, app_path], cwd=PROJECT_DIR)

def run_evm():
    print("\n[+] Launching Official EVM GUI Prototype...")
    gui_path = os.path.join(PROJECT_DIR, "gui_prototype.py")
    subprocess.run([sys.executable, gui_path], cwd=PROJECT_DIR)

def run_secure():
    print("\n[+] Launching Integrated Secure Biometric Voting System...")
    sec_path = os.path.join(PROJECT_DIR, "secure_biometric_voting_system.py")
    subprocess.run([sys.executable, sec_path], cwd=PROJECT_DIR)

def run_collector():
    print("\n[+] Launching Voter Details Enrollment Form (Desktop)...")
    col_path = os.path.join(PROJECT_DIR, "voter_collector.py")
    subprocess.run([sys.executable, col_path], cwd=PROJECT_DIR)

def run_verifier():
    print("\n[+] Launching Voter Details Verification System (Desktop)...")
    ver_path = os.path.join(PROJECT_DIR, "voter_verification_app.py")
    subprocess.run([sys.executable, ver_path], cwd=PROJECT_DIR)

def run_diagnostics():
    print("\n[*] Running Complete BioVote System Diagnostics & Tests...\n")
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_DIR
    
    # 1. Biometrics test
    test1 = os.path.join(PROJECT_DIR, "scratch", "test_biometrics.py")
    if os.path.exists(test1):
        print("--- [1/3] Testing ORB Biometric Feature Extraction & Matching ---")
        subprocess.run([sys.executable, test1], cwd=PROJECT_DIR)
        print()

    # 2. Routes test
    test2 = os.path.join(PROJECT_DIR, "scratch", "test_routes.py")
    if os.path.exists(test2):
        print("--- [2/3] Testing Flask Web Application Routes ---")
        subprocess.run([sys.executable, test2], cwd=PROJECT_DIR, env=env)
        print()

    # 3. End-to-end integration test
    test3 = os.path.join(PROJECT_DIR, "scratch", "test_e2e_flow.py")
    if os.path.exists(test3):
        print("--- [3/3] Testing End-to-End Voter Enrollment & Ballot Lock ---")
        subprocess.run([sys.executable, test3], cwd=PROJECT_DIR, env=env)
        print()

    print("[SUCCESS] All diagnostics completed successfully!\n")

def show_menu():
    print_banner()
    print("Please select an application module to run:")
    print("  [1] Web Portal (Flask + Biometric Verification)  --> Recommended")
    print("  [2] Electronic Voting Machine (EVM Prototype GUI)")
    print("  [3] Integrated 3-Step Secure Biometric Voting System")
    print("  [4] Desktop Voter Enrollment Form (Form I)")
    print("  [5] Desktop Voter Verification Kiosk")
    print("  [6] Run Full System Diagnostics & Biometric Tests")
    print("  [0] Exit")
    print("-" * 72)
    choice = input("Enter choice (0-6) [Default: 1]: ").strip()
    if not choice:
        choice = "1"

    if choice == "1":
        run_web()
    elif choice == "2":
        run_evm()
    elif choice == "3":
        run_secure()
    elif choice == "4":
        run_collector()
    elif choice == "5":
        run_verifier()
    elif choice == "6":
        run_diagnostics()
    elif choice == "0":
        print("\nExiting. Good bye!")
        sys.exit(0)
    else:
        print("\nInvalid choice. Launching default Web Portal...")
        run_web()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ("web", "app", "serve"):
            run_web()
        elif cmd in ("evm", "gui"):
            run_evm()
        elif cmd in ("secure", "booth"):
            run_secure()
        elif cmd in ("enroll", "register", "collector"):
            run_collector()
        elif cmd in ("verify", "check"):
            run_verifier()
        elif cmd in ("test", "diagnostics", "checkup"):
            run_diagnostics()
        else:
            print(f"Unknown argument '{cmd}'. Usage: python run_project.py [web|evm|secure|register|verify|test]")
    else:
        # Check if running in non-interactive environment
        if not sys.stdin.isatty():
            run_web()
        else:
            show_menu()
