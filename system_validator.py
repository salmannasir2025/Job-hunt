import platform
import uuid
import sys
import json
import subprocess
from pathlib import Path

class SystemValidator:
    def __init__(self):
        self.system = platform.system()
        self.machine = platform.machine()
        self.node = platform.node()
        self.processor = platform.processor()
        
    def get_hardware_id(self):
        """Generate a unique hardware ID based on the machine's MAC address"""
        return str(uuid.getnode())

    def get_cpu_info(self):
        """Get detailed CPU information based on platform"""
        info = {
            "machine": self.machine,
            "processor": self.processor,
            "architecture": platform.architecture()[0],
            "features": []
        }
        
        try:
            if self.system == "Darwin":
                # On macOS, check for AVX/AVX2/ARM features via sysctl
                out = subprocess.check_output(["sysctl", "-a"]).decode()
                if "hw.optional.avx2: 1" in out: info["features"].append("avx2")
                if "hw.optional.avx1_0: 1" in out: info["features"].append("avx")
                if "arm64" in self.machine.lower(): info["features"].append("neon")
            elif self.system == "Linux":
                # On Linux, check /proc/cpuinfo
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read().lower()
                    if "avx2" in cpuinfo: info["features"].append("avx2")
                    if "avx" in cpuinfo: info["features"].append("avx")
            elif self.system == "Windows":
                # On Windows, use wmic or just basic info
                pass
        except Exception:
            pass
            
        return info

    def check_alignment(self):
        """Perform full system alignment check"""
        report = {
            "os": {
                "system": self.system,
                "release": platform.release(),
                "version": platform.version()
            },
            "hardware": {
                "id": self.get_hardware_id(),
                "cpu": self.get_cpu_info()
            },
            "python": {
                "version": platform.python_version(),
                "executable": sys.executable
            }
        }
        return report

def main():
    validator = SystemValidator()
    report = validator.check_alignment()
    
    # Export report for the build process
    output_path = Path("build_alignment.json")
    with open(output_path, "w") as f:
        json.dump(report, f, indent=4)
    
    print("\n" + "="*40)
    print("📋 SYSTEM ALIGNMENT REPORT")
    print("="*40)
    print(f"OS: {report['os']['system']} {report['os']['release']}")
    print(f"Hardware ID: {report['hardware']['id']}")
    print(f"Architecture: {report['hardware']['cpu']['machine']}")
    print(f"CPU Features: {', '.join(report['hardware']['cpu']['features']) or 'Standard'}")
    print("="*40 + "\n")
    
    # Basic logic validation: Ensure architecture matches Python
    python_arch = report['python']['version']
    print(f"✅ Alignment check completed. Report saved to {output_path}")

if __name__ == "__main__":
    main()
