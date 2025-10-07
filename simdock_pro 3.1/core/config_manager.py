import os
import json
import sys
import subprocess
from typing import Dict, Any, Optional
import shutil


class ConfigManager:
    """Manages application configuration from external files."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self._default_config = self._get_default_config()
        self.load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration as fallback."""
        return {
            "executables": {
                "obabel": "obabel",
                "vina": "vina",
                "chimerax": "chimerax",
                "vmd": "vmd"
            },
            "platform_settings": {
                "windows": {
                    "obabel": "C:\\Program Files (x86)\\OpenBabel-3.1.1\\obabel.exe",
                    "vina": "C:\\Program Files (x86)\\PyRx\\vina.exe",
                    "chimerax": "C:\\Program Files\\Chimerax 1.10.1\\bin\\Chimerax.exe",
                    "vmd": "C:\\Program Files\\University of Illinois\\UMD2\\vmd.exe",
                    "create_no_window": True
                },
                "linux": {
                    "obabel": "obabel",
                    "vina": "vina",
                    "chimerax": "chimerax",
                    "vmd": "vmd",
                    "create_no_window": False
                },
                "darwin": {
                    "obabel": "obabel",
                    "vina": "vina",
                    "chimerax": "chimerax",
                    "vmd": "vmd",
                    "create_no_window": False
                }
            },
            "docking": {
                "default_exhaustiveness": 8,
                "default_refine_percentage": 10,
                "default_box_size": [25.0, 25.0, 25.0],
                "box_padding": 5.0,
                "adaptive_exhaustiveness_thresholds": [7, 12],
                "adaptive_exhaustiveness_values": [8, 16, 32]
            },
            "file_formats": {
                "supported_ligand_formats": [".pdb", ".sdf", ".mol2"],
                "supported_receptor_formats": [".pdb"]
            },
            "ui": {
                "default_mode": "Normal",
                "default_viewer": "VMD",
                "window_size": [1200, 800],
                "min_window_size": [1000, 700]
            },
            "network": {
                "pdb_download_url": "https://files.rcsb.org/download/{pdb_id}.pdb",
                "pubchem_base_url": "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound",
                "timeout": 30
            },
            "temp": {
                "temp_dir_prefix": "simdock_",
                "cleanup_on_exit": True
            }
        }
    
    def load_config(self) -> bool:
        """Load configuration from file or create default if not exists."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults (loaded config overrides defaults)
                self.config = self._deep_merge(self._default_config, loaded_config)
                print(f"Configuration loaded from {self.config_file}")
            else:
                self.config = self._default_config.copy()
                self.save_config()  # Create default config file
                print(f"Default configuration created at {self.config_file}")
            return True
        except Exception as e:
            print(f"Error loading configuration: {e}. Using defaults.")
            self.config = self._default_config.copy()
            return False
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in update.items():
            if (key in result and isinstance(result[key], dict) 
                and isinstance(value, dict)):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def get_platform_config(self) -> Dict[str, Any]:
        """Get platform-specific configuration."""
        platform = sys.platform
        platform_key = "windows" if platform == "win32" else platform
        return self.config["platform_settings"].get(platform_key, {})
    
    def get_executable_path(self, program: str) -> str:
        """Get executable path for a program."""
        platform_config = self.get_platform_config()
        
        # First try platform-specific path
        if program in platform_config:
            return platform_config[program]
        
        # Fall back to generic executable name
        return self.config["executables"].get(program, program)
    
    def get_docking_setting(self, key: str, default: Any = None) -> Any:
        """Get docking-specific setting."""
        return self.config["docking"].get(key, default)
    
    def get_ui_setting(self, key: str, default: Any = None) -> Any:
        """Get UI-specific setting."""
        return self.config["ui"].get(key, default)
    
    def get_file_formats(self, format_type: str) -> list:
        """Get supported file formats."""
        return self.config["file_formats"].get(format_type, [])
    
    def get_network_setting(self, key: str, default: Any = None) -> Any:
        """Get network-related setting."""
        return self.config["network"].get(key, default)
    
    def get_temp_setting(self, key: str, default: Any = None) -> Any:
        """Get temporary directory settings."""
        return self.config["temp"].get(key, default)
    
    def set_setting(self, category: str, key: str, value: Any) -> bool:
        """Update a configuration setting."""
        try:
            if category in self.config:
                self.config[category][key] = value
            else:
                self.config[category] = {key: value}
            return True
        except Exception as e:
            print(f"Error setting configuration: {e}")
            return False
    
    def validate_config(self) -> Dict[str, list]:
        """Validate configuration and return any issues."""
        issues = {}
        
        # Check if executables exist and are functional
        required_executables = ["obabel", "vina"]
        optional_executables = ["chimerax", "vmd"]
        
        for exe in required_executables + optional_executables:
            path = self.get_executable_path(exe)
            check_result = self._check_executable_functional(path, exe)
            
            if not check_result["exists"]:
                if exe in required_executables:
                    if "missing_executables" not in issues:
                        issues["missing_executables"] = []
                    issues["missing_executables"].append(f"{exe}: {path} (NOT FOUND)")
            elif not check_result["functional"]:
                if "non_functional_executables" not in issues:
                    issues["non_functional_executables"] = []
                issues["non_functional_executables"].append(f"{exe}: {path} ({check_result.get('error', 'Unknown error')})")
        
        # Validate docking settings
        docking_settings = self.config["docking"]
        if docking_settings["default_exhaustiveness"] <= 0:
            if "invalid_settings" not in issues:
                issues["invalid_settings"] = []
            issues["invalid_settings"].append("default_exhaustiveness must be positive")
        
        # Validate box sizes
        box_size = docking_settings["default_box_size"]
        if len(box_size) != 3 or any(s <= 0 for s in box_size):
            if "invalid_settings" not in issues:
                issues["invalid_settings"] = []
            issues["invalid_settings"].append("default_box_size must have 3 positive values")
        
        # Validate adaptive exhaustiveness settings
        thresholds = docking_settings.get("adaptive_exhaustiveness_thresholds", [])
        values = docking_settings.get("adaptive_exhaustiveness_values", [])
        if len(thresholds) + 1 != len(values):
            if "invalid_settings" not in issues:
                issues["invalid_settings"] = []
            issues["invalid_settings"].append("adaptive_exhaustiveness_thresholds and values length mismatch")
        
        return issues
    
    def _check_executable_functional(self, path: str, program: str) -> Dict[str, Any]:
        """Check if an executable exists and is functional."""
        result = {
            "exists": False,
            "functional": False,
            "error": None
        }
        
        # Check if executable exists
        if os.path.isabs(path):
            result["exists"] = os.path.exists(path)
        else:
            # Check if executable is in PATH
            result["exists"] = shutil.which(path) is not None
        
        if not result["exists"]:
            return result
        
        # Test if executable is functional
        try:
            if program == "obabel":
                cmd = [path, "-L", "formats"]
            elif program in ["vina"]:
                cmd = [path, "--help"]
            elif program in ["chimerax", "vmd"]:
                cmd = [path, "--version"]
            else:
                cmd = [path, "--help"]
            
            # Run test command
            process = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=10,  # 10 second timeout
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            result["functional"] = process.returncode == 0 or len(process.stdout) > 0
            if not result["functional"]:
                result["error"] = process.stderr[:100] if process.stderr else "No output produced"
                
        except subprocess.TimeoutExpired:
            result["functional"] = False
            result["error"] = "Command timed out"
        except Exception as e:
            result["functional"] = False
            result["error"] = str(e)
        
        return result
    
    def save_config(self) -> bool:
        """Save current configuration to file with backup."""
        try:
            # Create backup of existing config
            if os.path.exists(self.config_file):
                backup_file = self.config_file + '.backup'
                shutil.copy2(self.config_file, backup_file)
            
            # Save to temporary file first
            temp_file = self.config_file + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            # Atomic replace
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            os.rename(temp_file, self.config_file)
            
            # Remove backup if save was successful
            if os.path.exists(self.config_file + '.backup'):
                os.remove(self.config_file + '.backup')
                
            return True
        except Exception as e:
            # Restore from backup if save failed
            if os.path.exists(self.config_file + '.backup'):
                try:
                    if os.path.exists(self.config_file):
                        os.remove(self.config_file)
                    os.rename(self.config_file + '.backup', self.config_file)
                except:
                    pass
            print(f"Error saving configuration: {e}")
            return False
    
    def create_config_wizard(self) -> bool:
        """Interactive configuration wizard for first-time setup."""
        try:
            print("=== SimDock Configuration Wizard ===")
            print("This wizard will help you configure the paths to required executables.")
            print("If you're not sure, you can press Enter to use the default values.")
            print()
            
            platform_config = self.get_platform_config()
            
            # Configure Open Babel
            current_obabel = platform_config.get("obabel", "obabel")
            new_obabel = input(f"Open Babel path [{current_obabel}]: ").strip()
            if new_obabel:
                self.set_setting("platform_settings", sys.platform, 
                               {**platform_config, "obabel": new_obabel})
            
            # Configure AutoDock Vina
            current_vina = platform_config.get("vina", "vina")
            new_vina = input(f"AutoDock Vina path [{current_vina}]: ").strip()
            if new_vina:
                self.set_setting("platform_settings", sys.platform,
                               {**platform_config, "vina": new_vina})
            
            # Configure ChimeraX
            current_chimerax = platform_config.get("chimerax", "chimerax")
            new_chimerax = input(f"ChimeraX path [{current_chimerax}]: ").strip()
            if new_chimerax:
                self.set_setting("platform_settings", sys.platform,
                               {**platform_config, "chimerax": new_chimerax})
            
            # Configure VMD
            current_vmd = platform_config.get("vmd", "vmd")
            new_vmd = input(f"VMD path [{current_vmd}]: ").strip()
            if new_vmd:
                self.set_setting("platform_settings", sys.platform,
                               {**platform_config, "vmd": new_vmd})
            
            # Save configuration
            if self.save_config():
                print(f"\nConfiguration saved to {self.config_file}")
                
                # Validate configuration
                issues = self.validate_config()
                if issues:
                    print("\nConfiguration issues found:")
                    for category, problems in issues.items():
                        print(f"  {category}:")
                        for problem in problems:
                            print(f"    - {problem}")
                else:
                    print("Configuration validated successfully!")
                
                return True
            else:
                print("Failed to save configuration.")
                return False
                
        except Exception as e:
            print(f"Error in configuration wizard: {e}")
            return False
    
    def _check_executable_exists(self, path: str) -> bool:
        """Check if an executable exists."""
        if os.path.isabs(path):
            return os.path.exists(path)
        else:
            # Check if executable is in PATH
            return shutil.which(path) is not None
    
    def get_executable_status(self, program: str) -> Dict[str, Any]:
        """Get detailed status of an executable."""
        path = self.get_executable_path(program)
        return self._check_executable_functional(path, program)
    
    def get_all_executable_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all executables."""
        status = {}
        executables = ["obabel", "vina", "chimerax", "vmd"]
        
        for exe in executables:
            status[exe] = self.get_executable_status(exe)
        
        return status