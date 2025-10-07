import os
import subprocess
import re
import math
import tempfile
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Any

from utils.config import CREATE_NO_WINDOW, get_config_manager, OBABEL_PATH
from utils.helpers import run_command
from .file_manager import FileManager


class BaseDockingEngine(ABC):
    """Abstract base class for all docking engines."""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.file_manager = FileManager()
        self.results = []
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the name of the docking engine."""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Return the version of the docking engine."""
        pass
    
    def prepare_ligand(self, ligand_path: str, output_dir: str) -> Optional[str]:
        """Prepare ligand for docking using centralized file manager."""
        return self.file_manager.prepare_ligand(ligand_path, output_dir)
    
    def prepare_receptor(self, receptor_path: str, output_dir: str) -> Optional[str]:
        """Prepare receptor for docking using centralized file manager."""
        return self.file_manager.prepare_receptor(receptor_path, output_dir)
    
    @abstractmethod
    def run_docking(self, receptor_path: str, ligand_path: str, output_path: str,
                   center: Tuple[float, float, float], size: Tuple[float, float, float],
                   exhaustiveness: int = 8, **kwargs) -> Dict[str, Any]:
        """Run docking simulation."""
        pass
    
    @abstractmethod
    def parse_output(self, output_content: str) -> List[Dict[str, Any]]:
        """Parse docking output to extract scores and poses."""
        pass
    
    @abstractmethod
    def validate_parameters(self, center: Tuple[float, float, float],
                          size: Tuple[float, float, float]) -> bool:
        """Validate docking parameters."""
        pass
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported file formats for this engine."""
        return self.file_manager.get_supported_formats()
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default docking parameters."""
        return {
            'exhaustiveness': 8,
            'num_modes': 9,
            'energy_range': 3.0
        }
    
    def get_parameter_ranges(self) -> Dict[str, Tuple[Any, Any]]:
        """Get valid parameter ranges for this engine."""
        return {
            'exhaustiveness': (1, 128),
            'num_modes': (1, 20),
            'energy_range': (0.0, 10.0)
        }
    
    def get_rotatable_bonds(self, ligand_file: str) -> int:
        """Calculate number of rotatable bonds in ligand using file manager."""
        file_info = self.file_manager.get_file_info(ligand_file)
        return file_info.get('rotatable_bonds', 0)
    
    def get_adaptive_exhaustiveness(self, ligand_file: str, base_exhaustiveness: int = None) -> int:
        """Calculate adaptive exhaustiveness based on rotatable bonds."""
        if base_exhaustiveness is None:
            base_exhaustiveness = self.get_default_parameters()['exhaustiveness']
            
        thresholds = self.config_manager.get_docking_setting("adaptive_exhaustiveness_thresholds", [7, 12])
        values = self.config_manager.get_docking_setting("adaptive_exhaustiveness_values", [8, 16, 32])
        
        rot_bonds = self.get_rotatable_bonds(ligand_file)
        
        if rot_bonds <= thresholds[0]:
            return values[0]
        elif rot_bonds <= thresholds[1]:
            return values[1]
        else:
            return values[2]
    
    def run_quick_screening(self, receptor_path: str, ligand_path: str,
                           output_path: str, center: Tuple[float, float, float],
                           size: Tuple[float, float, float]) -> Dict[str, Any]:
        """Run quick screening with low exhaustiveness."""
        return self.run_docking(
            receptor_path, ligand_path, output_path,
            center, size, exhaustiveness=4  # Very low for quick screening
        )
    
    def run_refinement_docking(self, receptor_path: str, ligand_path: str,
                              output_path: str, center: Tuple[float, float, float],
                              size: Tuple[float, float, float]) -> Dict[str, Any]:
        """Run refinement docking with high exhaustiveness."""
        return self.run_docking(
            receptor_path, ligand_path, output_path,
            center, size, exhaustiveness=32  # Very high for refinement
        )


class VinaEngine(BaseDockingEngine):
    """AutoDock Vina docking engine implementation."""
    
    def __init__(self):
        super().__init__()
        from utils.config import VINA_PATH
        self.vina_path = VINA_PATH
    
    def get_name(self) -> str:
        return "AutoDock Vina"
    
    def get_version(self) -> str:
        """Get Vina version by running the command."""
        try:
            command = [self.vina_path, "--help"]
            result = subprocess.run(command, capture_output=True, text=True, 
                                  creationflags=CREATE_NO_WINDOW)
            # Extract version from help output
            for line in result.stdout.splitlines():
                if "Vina" in line and "version" in line.lower():
                    return line.strip()
            return "AutoDock Vina (version unknown)"
        except Exception:
            return "AutoDock Vina"
    
    def run_docking(self, receptor_path: str, ligand_path: str, output_path: str,
                   center: Tuple[float, float, float], size: Tuple[float, float, float],
                   exhaustiveness: int = 8, **kwargs) -> Dict[str, Any]:
        """Run AutoDock Vina docking."""
        
        # Build Vina command
        command = self._build_vina_command(
            receptor_path, ligand_path, output_path,
            center, size, exhaustiveness, kwargs
        )
        
        # Execute docking
        result = run_command(command)
        
        if result and os.path.exists(output_path):
            scores = self.parse_output(result.stdout)
            return {
                'success': True,
                'engine': self.get_name(),
                'scores': scores,
                'output_file': output_path,
                'log': result.stdout,
                'error': result.stderr
            }
        else:
            return {
                'success': False,
                'engine': self.get_name(),
                'error': 'Docking failed - no output file generated',
                'log': result.stdout if result else '',
                'error_log': result.stderr if result else ''
            }
    
    def _build_vina_command(self, receptor: str, ligand: str, out: str,
                           center: Tuple[float, float, float], 
                           size: Tuple[float, float, float],
                           exhaustiveness: int, kwargs: Dict) -> List[str]:
        """Build Vina command with all parameters."""
        cx, cy, cz = center
        sx, sy, sz = size
        
        command = [
            self.vina_path,
            "--receptor", receptor,
            "--ligand", ligand,
            "--out", out,
            "--center_x", f"{cx:.3f}",
            "--center_y", f"{cy:.3f}", 
            "--center_z", f"{cz:.3f}",
            "--size_x", f"{sx:.3f}",
            "--size_y", f"{sy:.3f}",
            "--size_z", f"{sz:.3f}",
            "--exhaustiveness", str(exhaustiveness)
        ]
        
        # Add optional parameters
        if 'num_modes' in kwargs:
            command.extend(["--num_modes", str(kwargs['num_modes'])])
        
        if 'energy_range' in kwargs:
            command.extend(["--energy_range", str(kwargs['energy_range'])])
        
        if 'cpu' in kwargs:
            command.extend(["--cpu", str(kwargs['cpu'])])
        
        if 'seed' in kwargs:
            command.extend(["--seed", str(kwargs['seed'])])
        
        return command
    
    def parse_output(self, output_content: str) -> List[Dict[str, Any]]:
        """Parse Vina output to extract docking scores."""
        scores = []
        pattern = re.compile(r"^\s*(\d+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)")
        
        for line in output_content.splitlines():
            match = pattern.match(line)
            if match:
                mode, affinity, rmsd_lb, rmsd_ub = match.groups()
                scores.append({
                    'Mode': int(mode),
                    'Affinity (kcal/mol)': float(affinity),
                    'RMSD L.B.': float(rmsd_lb),
                    'RMSD U.B.': float(rmsd_ub),
                    'Engine': self.get_name()
                })
        return scores
    
    def validate_parameters(self, center: Tuple[float, float, float],
                          size: Tuple[float, float, float]) -> bool:
        """Validate Vina docking parameters."""
        # Check if center coordinates are numbers
        if not all(isinstance(c, (int, float)) for c in center):
            return False
        
        # Check if size values are positive
        if not all(s > 0 for s in size):
            return False
        
        # Check if size values are reasonable
        if any(s < 1.0 or s > 200.0 for s in size):
            return False
            
        return True


class DockingEngineFactory:
    """Factory class for creating docking engine instances."""
    
    @staticmethod
    def create_engine(engine_type: str = "vina") -> BaseDockingEngine:
        """Create a docking engine instance."""
        engines = {
            "vina": VinaEngine,
        }
        
        if engine_type.lower() not in engines:
            raise ValueError(f"Unknown docking engine: {engine_type}. "
                           f"Available engines: {list(engines.keys())}")
        
        return engines[engine_type.lower()]()
    
    @staticmethod
    def get_available_engines() -> List[str]:
        """Get list of available docking engines."""
        available = ["vina"]  # Vina is always available
        
        return available
    
    @staticmethod
    def get_engine_info(engine_type: str) -> Dict[str, str]:
        """Get information about a specific docking engine."""
        engine = DockingEngineFactory.create_engine(engine_type)
        return {
            'name': engine.get_name(),
            'version': engine.get_version(),
            'supported_formats': engine.get_supported_formats(),
            'default_parameters': engine.get_default_parameters(),
            'description': DockingEngineFactory._get_engine_description(engine_type)
        }
    
    @staticmethod
    def _get_engine_description(engine_type: str) -> str:
        """Get description for each docking engine."""
        descriptions = {
            "vina": "AutoDock Vina - Most popular docking software with good balance of speed and accuracy",
        }
        return descriptions.get(engine_type, "No description available")
