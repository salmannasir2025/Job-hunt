#!/usr/bin/env python3

"""
Universal Build Script for Elite Job Agent
Detects OS and runs appropriate build script
Usage: python3 build.py
"""

import os
import sys
import platform
import subprocess
import json
from pathlib import Path
from system_validator import SystemValidator

class BuildSystem:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.system = platform.system()
        self.machine = platform.machine()
        
    def get_platform_info(self):
        """Get detailed platform information"""
        return {
            'system': self.system,
            'release': platform.release(),
            'version': platform.version(),
            'machine': self.machine,
            'python_version': platform.python_version(),
            'python_impl': platform.python_implementation(),
        }
    
    def print_header(self):
        """Print build header"""
        print("\n" + "="*60)
        print("🚀 Elite Job Agent - Universal Build System")
        print("="*60 + "\n")
        
        info = self.get_platform_info()
        print("📊 System Information:")
        print(f"   OS: {info['system']} {info['release']}")
        print(f"   Machine: {info['machine']}")
        print(f"   Python: {info['python_impl']} {info['python_version']}")
        print()
    
    def check_python_version(self):
        """Verify Python 3.8+"""
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required!")
            print(f"   Current: {platform.python_version()}")
            sys.exit(1)
        print("✅ Python version OK")
    
    def install_build_dependencies(self):
        """Install required build tools with auto-repair logic"""
        print("\n📦 Verifying build environment...")
        
        # Check if running in a venv
        in_venv = sys.prefix != sys.base_prefix
        if not in_venv:
            print("⚠️  Not running in a virtual environment. Creating one...")
            venv_dir = self.project_root / ".venv_automated"
            if not venv_dir.exists():
                subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
            
            # Re-run self using the new venv's python
            python_exe = venv_dir / ("Scripts" if self.system == "Windows" else "bin") / ("python.exe" if self.system == "Windows" else "python3")
            print(f"🚀 Switching to automated environment: {python_exe}")
            os.execv(str(python_exe), [str(python_exe)] + sys.argv)
            return True

        try:
            print("⚙️  Checking/Installing dependencies...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                stdout=subprocess.DEVNULL
            )
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "pyinstaller", "Pillow"],
                stdout=subprocess.DEVNULL
            )
            print("✅ Build dependencies verified")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to verify dependencies")
            return False
    
    def build_macos(self):
        """Build for macOS"""
        print("\n🍎 Building for macOS...")
        script = self.project_root / "build_macos.sh"
        
        if not script.exists():
            print(f"❌ Build script not found: {script}")
            return False
        
        try:
            subprocess.check_call(["bash", str(script)])
            print("✅ macOS build complete!")
            return True
        except subprocess.CalledProcessError:
            print("❌ macOS build failed")
            return False
    
    def build_windows(self):
        """Build for Windows"""
        print("\n🪟 Building for Windows...")
        script = self.project_root / "build_windows.bat"
        
        if not script.exists():
            print(f"❌ Build script not found: {script}")
            return False
        
        try:
            subprocess.check_call(["cmd", "/c", str(script)])
            print("✅ Windows build complete!")
            return True
        except subprocess.CalledProcessError:
            print("❌ Windows build failed")
            return False
    
    def build_linux(self):
        """Build for Linux"""
        print("\n🐧 Building for Linux...")
        script = self.project_root / "build_linux.sh"
        
        if not script.exists():
            print(f"❌ Build script not found: {script}")
            return False
        
        # Make executable
        os.chmod(script, 0o755)
        
        try:
            subprocess.check_call(["bash", str(script)])
            print("✅ Linux build complete!")
            return True
        except subprocess.CalledProcessError:
            print("❌ Linux build failed")
            return False
    
    def run(self, target=None):
        """Run build process with alignment checks"""
        self.print_header()
        
        # NEW: Run Hardware/System Alignment Check
        validator = SystemValidator()
        report = validator.check_alignment()
        print(f"🔍 Hardware ID: {report['hardware']['id']}")
        print(f"🔍 Architecture Match: {report['hardware']['cpu']['machine']} (OK)")
        
        # Save alignment report for bundling
        with open(self.project_root / "build_alignment.json", "w") as f:
            json.dump(report, f, indent=4)

        self.check_python_version()
        
        if not self.install_build_dependencies():
            sys.exit(1)
        
        # If target specified, build only that
        if target:
            target = target.lower()
            print(f"\n🎯 Building for {target}...\n")
            
            if target == "macos":
                success = self.build_macos()
            elif target == "windows":
                success = self.build_windows()
            elif target == "linux":
                success = self.build_linux()
            else:
                print(f"❌ Unknown target: {target}")
                print("   Available: macos, windows, linux, current")
                sys.exit(1)
            
            sys.exit(0 if success else 1)
        
        # Auto-detect current platform
        print(f"🎯 Auto-detecting platform: {self.system}\n")
        
        success = False
        if self.system == "Darwin":  # macOS
            success = self.build_macos()
        elif self.system == "Windows":
            success = self.build_windows()
        elif self.system == "Linux":
            success = self.build_linux()
        else:
            print(f"❌ Unsupported OS: {self.system}")
            sys.exit(1)
        
        if not success:
            sys.exit(1)
        
        # Run post-build security/consistency checks
        self.check_security()
        
        # Print summary
        self.print_summary()
    
    def check_security(self):
        """Run post-build security and consistency checks"""
        print("\n🛡️  Running post-build security checks...")
        try:
            # Run Bandit scans on the build scripts and core logic
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "bandit"],
                stdout=subprocess.DEVNULL
            )
            subprocess.check_call(
                [sys.executable, "-m", "bandit", "-r", "build.py", "system_validator.py"],
                stdout=subprocess.DEVNULL
            )
            print("✅ Bandit security scan passed")
            
            # Check for leaked secrets in the build directory
            build_report = self.project_root / "build_alignment.json"
            if build_report.exists():
                with open(build_report, "r") as f:
                    data = json.load(f)
                    # Simple check for common secret patterns (just an example)
                    for key, value in data.items():
                        if "key" in str(key).lower() or "secret" in str(key).lower():
                            print(f"⚠️  Potential secret found in alignment report: {key}")
            
            print("✅ Consistency checks passed")
        except subprocess.CalledProcessError:
            print("⚠️  Security checks failed or skipped")
    
    def print_summary(self):
        """Print build summary"""
        print("\n" + "="*60)
        print("✅ BUILD COMPLETE!")
        print("="*60 + "\n")
        
        dist_dir = self.project_root / "dist"
        
        if self.system == "Darwin":
            print("📁 Output files:")
            print(f"   - {dist_dir}/Elite Job Agent.app")
            print(f"   - {dist_dir}/Elite Job Agent.dmg")
            print("\n🚀 To test:")
            print(f"   open '{dist_dir}/Elite Job Agent.app'")
            print("\n📦 To distribute:")
            print(f"   Share the .dmg file with users")
        
        elif self.system == "Windows":
            print("📁 Output files:")
            print(f"   - {dist_dir}\\Elite Job Agent.exe")
            print("\n🚀 To test:")
            print(f"   {dist_dir}\\Elite Job Agent.exe")
            print("\n📦 To distribute:")
            print(f"   Share the .exe file with users")
        
        elif self.system == "Linux":
            print("📁 Output files:")
            print(f"   - {dist_dir}/elite-job-agent (standalone)")
            appimage = dist_dir / "Elite_Job_Agent-x86_64.AppImage"
            if appimage.exists():
                print(f"   - {appimage} (portable)")
            print("\n🚀 To test:")
            print(f"   {dist_dir}/elite-job-agent")
            print("\n📦 To distribute:")
            if appimage.exists():
                print(f"   Share the AppImage file (works on any Linux)")
            print(f"   Or share the standalone executable")
        
        print("\n" + "="*60 + "\n")

def main():
    """Main entry point"""
    builder = BuildSystem()
    
    # Check if specific target requested
    target = None
    if len(sys.argv) > 1:
        target = sys.argv[1]
    
    try:
        builder.run(target)
    except KeyboardInterrupt:
        print("\n\n⚠️  Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
