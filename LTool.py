#!/usr/bin/env python3
"""
Linux System Manager - Professional Maintenance Tool BY XROOT
====================================================
A comprehensive system maintenance application for Linux systems.
Features: Update/Upgrade, System Repair, Cleanup, Performance Boost
Requires: Root privileges for system operations
Author: System Admin
Date: 2025
"""

import os
import sys
import subprocess
import threading
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/system_manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SystemInfo:
    """System information structure"""
    os_name: str
    kernel_version: str
    uptime: str
    memory_usage: str
    disk_usage: str
    cpu_usage: str

class SystemManager:
    """Core system management functionality"""
    
    def __init__(self):
        self.supported_distros = {
            'ubuntu': ['apt', 'apt-get'],
            'debian': ['apt', 'apt-get'],
            'fedora': ['dnf', 'yum'],
            'centos': ['yum', 'dnf'],
            'arch': ['pacman'],
            'opensuse': ['zypper']
        }
        self.distro = self.detect_distro()
        self.package_manager = self.get_package_manager()
        logger.info(f"Detected distribution: {self.distro}")
    
    def detect_distro(self) -> str:
        """Detect the Linux distribution"""
        try:
            # Check /etc/os-release
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    content = f.read().lower()
                    if 'ubuntu' in content:
                        return 'ubuntu'
                    elif 'debian' in content:
                        return 'debian'
                    elif 'fedora' in content:
                        return 'fedora'
                    elif 'centos' in content:
                        return 'centos'
                    elif 'arch' in content:
                        return 'arch'
                    elif 'opensuse' in content:
                        return 'opensuse'
            
            # Fallback methods
            if os.path.exists('/etc/debian_version'):
                return 'debian'
            elif os.path.exists('/etc/redhat-release'):
                return 'fedora'
            elif os.path.exists('/etc/arch-release'):
                return 'arch'
            
            return 'unknown'
        except Exception as e:
            logger.error(f"Error detecting distribution: {e}")
            return 'unknown'
    
    def get_package_manager(self) -> str:
        """Get the appropriate package manager"""
        if self.distro in self.supported_distros:
            for pm in self.supported_distros[self.distro]:
                if self.command_exists(pm):
                    return pm
        return 'apt'  # Default fallback
    
    def command_exists(self, command: str) -> bool:
        """Check if a command exists"""
        try:
            subprocess.run(['which', command], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def run_command(self, command: List[str], timeout: int = 300) -> Tuple[bool, str]:
        """Execute a system command with timeout"""
        try:
            logger.info(f"Executing command: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return True, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except subprocess.CalledProcessError as e:
            return False, f"Command failed: {e.stderr}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_system_info(self) -> SystemInfo:
        """Get comprehensive system information"""
        try:
            # OS Name
            os_name = subprocess.getoutput("lsb_release -d 2>/dev/null | cut -f2 || echo 'Unknown'")
            
            # Kernel Version
            kernel_version = subprocess.getoutput("uname -r")
            
            # Uptime
            uptime = subprocess.getoutput("uptime -p 2>/dev/null || uptime")
            
            # Memory Usage
            memory_usage = subprocess.getoutput("free -h | grep 'Mem:' | awk '{print $3\"/\"$2}'")
            
            # Disk Usage
            disk_usage = subprocess.getoutput("df -h / | tail -1 | awk '{print $3\"/\"$2\" (\"$5\" used)\"}'")
            
            # CPU Usage
            cpu_usage = subprocess.getoutput("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//' || echo 'N/A'")
            
            return SystemInfo(
                os_name=os_name,
                kernel_version=kernel_version,
                uptime=uptime,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                cpu_usage=cpu_usage
            )
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return SystemInfo("Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown")

class MaintenanceOperations:
    """System maintenance operations"""
    
    def __init__(self, system_manager: SystemManager):
        self.sm = system_manager
        self.operations_log = []
    
    def update_system(self, progress_callback=None) -> Tuple[bool, str]:
        """Update and upgrade the system"""
        operations = []
        
        if self.sm.package_manager in ['apt', 'apt-get']:
            operations = [
                (['sudo', 'apt', 'update'], "Updating package lists..."),
                (['sudo', 'apt', 'upgrade', '-y'], "Upgrading packages..."),
                (['sudo', 'apt', 'dist-upgrade', '-y'], "Distribution upgrade..."),
                (['sudo', 'apt', 'autoremove', '-y'], "Removing unused packages..."),
                (['sudo', 'apt', 'autoclean'], "Cleaning package cache...")
            ]
        elif self.sm.package_manager in ['dnf', 'yum']:
            operations = [
                (['sudo', 'dnf', 'check-update'], "Checking for updates..."),
                (['sudo', 'dnf', 'upgrade', '-y'], "Upgrading packages..."),
                (['sudo', 'dnf', 'autoremove', '-y'], "Removing unused packages..."),
                (['sudo', 'dnf', 'clean', 'all'], "Cleaning package cache...")
            ]
        elif self.sm.package_manager == 'pacman':
            operations = [
                (['sudo', 'pacman', '-Syu', '--noconfirm'], "System update..."),
                (['sudo', 'pacman', '-Rns', '--noconfirm', '$(pacman -Qtdq)'], "Removing orphans..."),
                (['sudo', 'pacman', '-Scc', '--noconfirm'], "Cleaning cache...")
            ]
        
        return self._execute_operations(operations, progress_callback)
    
    def fix_system(self, progress_callback=None) -> Tuple[bool, str]:
        """Fix common system issues"""
        operations = []
        
        if self.sm.package_manager in ['apt', 'apt-get']:
            operations = [
                (['sudo', 'apt', 'update', '--fix-missing'], "Fixing missing packages..."),
                (['sudo', 'apt', '-f', 'install'], "Fixing broken dependencies..."),
                (['sudo', 'dpkg', '--configure', '-a'], "Configuring packages..."),
                (['sudo', 'apt', 'check'], "Checking package integrity..."),
                (['sudo', 'apt', 'autoremove', '-y'], "Removing broken packages...")
            ]
        elif self.sm.package_manager in ['dnf', 'yum']:
            operations = [
                (['sudo', 'dnf', 'check'], "Checking system integrity..."),
                (['sudo', 'dnf', 'distro-sync'], "Synchronizing packages..."),
                (['sudo', 'dnf', 'autoremove', '-y'], "Removing problematic packages...")
            ]
        elif self.sm.package_manager == 'pacman':
            operations = [
                (['sudo', 'pacman', '-Dk'], "Checking dependencies..."),
                (['sudo', 'pacman', '-Syu', '--noconfirm'], "Synchronizing system..."),
                (['sudo', 'pacman', '-Rns', '--noconfirm', '$(pacman -Qtdq)'], "Removing orphaned packages...")
            ]
        
        # Common system fixes
        common_fixes = [
            (['sudo', 'journalctl', '--vacuum-time=7d'], "Cleaning system logs..."),
            (['sudo', 'systemctl', 'daemon-reload'], "Reloading systemd..."),
            (['sudo', 'ldconfig'], "Updating library cache..."),
            (['sudo', 'updatedb'], "Updating locate database...")
        ]
        
        operations.extend(common_fixes)
        return self._execute_operations(operations, progress_callback)
    
    def auto_remove_unused(self, progress_callback=None) -> Tuple[bool, str]:
        """Remove unused packages, files, and clean system"""
        operations = []
        
        # Package cleanup
        if self.sm.package_manager in ['apt', 'apt-get']:
            operations.extend([
                (['sudo', 'apt', 'autoremove', '-y'], "Removing unused packages..."),
                (['sudo', 'apt', 'autoclean'], "Cleaning package cache..."),
                (['sudo', 'apt', 'clean'], "Deep cleaning cache...")
            ])
        elif self.sm.package_manager in ['dnf', 'yum']:
            operations.extend([
                (['sudo', 'dnf', 'autoremove', '-y'], "Removing unused packages..."),
                (['sudo', 'dnf', 'clean', 'all'], "Cleaning package cache...")
            ])
        elif self.sm.package_manager == 'pacman':
            operations.extend([
                (['sudo', 'pacman', '-Rns', '--noconfirm', '$(pacman -Qtdq)'], "Removing orphaned packages..."),
                (['sudo', 'pacman', '-Scc', '--noconfirm'], "Cleaning package cache...")
            ])
        
        # System cleanup
        cleanup_operations = [
            (['sudo', 'journalctl', '--vacuum-time=3d'], "Cleaning old logs..."),
            (['sudo', 'find', '/tmp', '-type', 'f', '-atime', '+7', '-delete'], "Cleaning temp files..."),
            (['sudo', 'find', '/var/tmp', '-type', 'f', '-atime', '+7', '-delete'], "Cleaning var temp..."),
            (['sudo', 'find', '/var/log', '-name', '*.log', '-type', 'f', '-mtime', '+30', '-delete'], "Cleaning old logs..."),
            (['sudo', 'find', '/home', '-name', '.cache', '-type', 'd', '-exec', 'rm', '-rf', '{}', '+'], "Cleaning user caches...")
        ]
        
        operations.extend(cleanup_operations)
        return self._execute_operations(operations, progress_callback)
    
    def boost_system(self, progress_callback=None) -> Tuple[bool, str]:
        """Optimize system performance"""
        operations = [
            (['sudo', 'sysctl', '-w', 'vm.swappiness=10'], "Optimizing swap usage..."),
            (['sudo', 'sysctl', '-w', 'vm.vfs_cache_pressure=50'], "Optimizing cache pressure..."),
            (['sudo', 'sysctl', '-w', 'net.core.rmem_max=16777216'], "Optimizing network buffers..."),
            (['sudo', 'sysctl', '-w', 'net.core.wmem_max=16777216'], "Optimizing network buffers..."),
            (['sudo', 'systemctl', 'disable', 'bluetooth'], "Disabling bluetooth service..."),
            (['sudo', 'systemctl', 'mask', 'plymouth-quit-wait.service'], "Optimizing boot time..."),
            (['sudo', 'systemctl', 'mask', 'plymouth-start.service'], "Optimizing boot time..."),
            (['sudo', 'prelink', '-amR'], "Optimizing binaries..."),
            (['sudo', 'sync'], "Syncing filesystems..."),
            (['sudo', 'sysctl', '-p'], "Applying kernel parameters...")
        ]
        
        return self._execute_operations(operations, progress_callback)
    
    def _execute_operations(self, operations: List[Tuple[List[str], str]], progress_callback=None) -> Tuple[bool, str]:
        """Execute a list of operations"""
        results = []
        total_ops = len(operations)
        
        for i, (command, description) in enumerate(operations):
            if progress_callback:
                progress = (i + 1) / total_ops * 100
                progress_callback(progress, description)
            
            success, output = self.sm.run_command(command)
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'command': ' '.join(command),
                'description': description,
                'success': success,
                'output': output[:200] + '...' if len(output) > 200 else output
            }
            
            self.operations_log.append(log_entry)
            results.append(f"{'✓' if success else '✗'} {description}")
            
            if not success:
                logger.error(f"Operation failed: {description} - {output}")
        
        return True, '\n'.join(results)

class SystemManagerGUI:
    """GUI interface for the system manager"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Linux System Manager - Professional Maintenance Tool")
        self.root.geometry("900x700")
        self.root.configure(bg='#2c3e50')
        
        # Initialize system manager
        self.system_manager = SystemManager()
        self.maintenance_ops = MaintenanceOperations(self.system_manager)
        
        # Check root privileges
        if os.geteuid() != 0:
            messagebox.showerror("Root Required", 
                               "This application requires root privileges to perform system operations.\n"
                               "Please run with: sudo python3 system_manager.py")
            sys.exit(1)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🐧 Linux System Manager", 
                               font=("Arial", 20, "bold"))
        title_label.pack(pady=(0, 20))
        
        # System info frame
        self.setup_system_info(main_frame)
        
        # Operations frame
        self.setup_operations(main_frame)
        
        # Progress frame
        self.setup_progress(main_frame)
        
        # Log frame
        self.setup_log(main_frame)
        
        # Load initial system info
        self.update_system_info()
    
    def setup_system_info(self, parent):
        """Setup system information display"""
        info_frame = ttk.LabelFrame(parent, text="System Information", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Create info labels
        self.info_labels = {}
        info_items = [
            ("OS", "os_name"),
            ("Kernel", "kernel_version"),
            ("Uptime", "uptime"),
            ("Memory", "memory_usage"),
            ("Disk", "disk_usage"),
            ("CPU", "cpu_usage")
        ]
        
        for i, (label, key) in enumerate(info_items):
            row = i // 2
            col = i % 2
            
            ttk.Label(info_frame, text=f"{label}:", font=("Arial", 9, "bold")).grid(
                row=row, column=col*2, sticky=tk.W, padx=(0, 5), pady=2)
            
            self.info_labels[key] = ttk.Label(info_frame, text="Loading...", font=("Arial", 9))
            self.info_labels[key].grid(row=row, column=col*2+1, sticky=tk.W, padx=(0, 20), pady=2)
    
    def setup_operations(self, parent):
        """Setup operation buttons"""
        ops_frame = ttk.LabelFrame(parent, text="System Operations", padding="10")
        ops_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Button configuration
        button_config = {
            'width': 20,
            'style': 'Custom.TButton'
        }
        
        # Create buttons
        buttons = [
            ("🔄 Update & Upgrade", self.update_system, "#3498db"),
            ("🔧 Fix System Issues", self.fix_system, "#e74c3c"),
            ("🗑️ Remove Unused Files", self.auto_remove, "#f39c12"),
            ("🚀 Boost Performance", self.boost_system, "#2ecc71")
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            row = i // 2
            col = i % 2
            
            btn = ttk.Button(ops_frame, text=text, command=command, **button_config)
            btn.grid(row=row, column=col, padx=10, pady=5, sticky=tk.EW)
        
        # Configure grid weights
        ops_frame.columnconfigure(0, weight=1)
        ops_frame.columnconfigure(1, weight=1)
    
    def setup_progress(self, parent):
        """Setup progress display"""
        progress_frame = ttk.LabelFrame(parent, text="Operation Progress", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(progress_frame, text="Ready", font=("Arial", 10))
        self.status_label.pack()
    
    def setup_log(self, parent):
        """Setup log display"""
        log_frame = ttk.LabelFrame(parent, text="Operation Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80,
                                                font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Clear log button
        clear_btn = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_btn.pack(pady=(10, 0))
    
    def update_system_info(self):
        """Update system information display"""
        def update_info():
            info = self.system_manager.get_system_info()
            
            self.info_labels["os_name"].config(text=info.os_name)
            self.info_labels["kernel_version"].config(text=info.kernel_version)
            self.info_labels["uptime"].config(text=info.uptime)
            self.info_labels["memory_usage"].config(text=info.memory_usage)
            self.info_labels["disk_usage"].config(text=info.disk_usage)
            self.info_labels["cpu_usage"].config(text=f"{info.cpu_usage}%")
        
        threading.Thread(target=update_info, daemon=True).start()
    
    def update_progress(self, progress, status):
        """Update progress display"""
        self.progress_var.set(progress)
        self.status_label.config(text=status)
        self.root.update_idletasks()
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear the log display"""
        self.log_text.delete(1.0, tk.END)
    
    def run_operation(self, operation_func, operation_name):
        """Run a maintenance operation"""
        def worker():
            try:
                self.log_message(f"Starting {operation_name}...")
                self.progress_var.set(0)
                
                success, result = operation_func(self.update_progress)
                
                if success:
                    self.log_message(f"✓ {operation_name} completed successfully")
                    self.log_message(result)
                else:
                    self.log_message(f"✗ {operation_name} failed")
                    self.log_message(result)
                
                self.progress_var.set(100)
                self.status_label.config(text=f"{operation_name} completed")
                
                # Update system info after operation
                self.update_system_info()
                
            except Exception as e:
                self.log_message(f"✗ Error during {operation_name}: {str(e)}")
                logger.error(f"Error in {operation_name}: {e}")
        
        threading.Thread(target=worker, daemon=True).start()
    
    def update_system(self):
        """Update and upgrade system"""
        self.run_operation(self.maintenance_ops.update_system, "System Update")
    
    def fix_system(self):
        """Fix system issues"""
        self.run_operation(self.maintenance_ops.fix_system, "System Fix")
    
    def auto_remove(self):
        """Remove unused files"""
        self.run_operation(self.maintenance_ops.auto_remove_unused, "Cleanup")
    
    def boost_system(self):
        """Boost system performance"""
        if messagebox.askyesno("Performance Boost", 
                              "This will modify system settings for better performance.\n"
                              "Some changes may require a reboot. Continue?"):
            self.run_operation(self.maintenance_ops.boost_system, "Performance Boost")
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        app = SystemManagerGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()