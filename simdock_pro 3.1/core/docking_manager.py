from typing import Dict, List, Optional, Any, Tuple
import os
from .docking_engine import BaseDockingEngine, DockingEngineFactory


class DockingManager:
    """Manages multiple docking engines and provides a unified interface."""
    
    def __init__(self, default_engine: str = "vina"):
        self.engines: Dict[str, BaseDockingEngine] = {}
        self.default_engine_type = default_engine
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize all available docking engines."""
        available_engines = DockingEngineFactory.get_available_engines()
        for engine_type in available_engines:
            try:
                self.engines[engine_type] = DockingEngineFactory.create_engine(engine_type)
                print(f"✓ Initialized {engine_type} engine successfully")
            except Exception as e:
                print(f"✗ Warning: Could not initialize {engine_type} engine: {e}")
    
    def get_engine(self, engine_type: str = None) -> BaseDockingEngine:
        """Get a docking engine instance."""
        if engine_type is None:
            engine_type = self.default_engine_type
        
        if engine_type not in self.engines:
            raise ValueError(f"Engine {engine_type} not available. "
                           f"Available engines: {list(self.engines.keys())}")
        
        return self.engines[engine_type]
    
    def get_available_engines(self) -> List[str]:
        """Get list of available engine types."""
        return list(self.engines.keys())
    
    def get_engine_info(self, engine_type: str = None) -> Dict[str, Any]:
        """Get information about a docking engine."""
        engine = self.get_engine(engine_type)
        engine_info = DockingEngineFactory.get_engine_info(engine_type if engine_type else self.default_engine_type)
        return {
            'name': engine.get_name(),
            'version': engine.get_version(),
            'supported_formats': engine.get_supported_formats(),
            'default_parameters': engine.get_default_parameters(),
            'parameter_ranges': engine.get_parameter_ranges(),
            'description': engine_info.get('description', 'No description available')
        }
    
    def get_all_engines_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available engines."""
        return {engine_type: self.get_engine_info(engine_type) 
                for engine_type in self.get_available_engines()}
    
    def set_default_engine(self, engine_type: str):
        """Set the default docking engine."""
        if engine_type not in self.engines:
            raise ValueError(f"Engine {engine_type} not available")
        self.default_engine_type = engine_type
    
    def validate_engine_availability(self, engine_type: str) -> bool:
        """Check if a specific engine is available."""
        return engine_type in self.engines
    
    def run_docking(self, receptor_path: str, ligand_path: str, output_path: str,
                   center: Tuple[float, float, float], size: Tuple[float, float, float],
                   engine_type: str = None, **kwargs) -> Dict[str, Any]:
        """Run docking using specified engine."""
        engine = self.get_engine(engine_type)
        
        # Validate parameters
        if not engine.validate_parameters(center, size):
            return {
                'success': False,
                'error': 'Invalid docking parameters',
                'engine': engine.get_name()
            }
        
        return engine.run_docking(
            receptor_path, ligand_path, output_path,
            center, size, **kwargs
        )
    
    def compare_engines(self, receptor_path: str, ligand_path: str, 
                       center: Tuple[float, float, float], size: Tuple[float, float, float],
                       engines: List[str] = None) -> Dict[str, Any]:
        """Run docking with multiple engines and compare results."""
        if engines is None:
            engines = self.get_available_engines()
        
        results = {}
        for engine_type in engines:
            if self.validate_engine_availability(engine_type):
                try:
                    temp_dir = self.engines[engine_type].file_manager.create_temp_directory()
                    output_path = os.path.join(temp_dir, f"comparison_{engine_type}.pdbqt")
                    
                    result = self.run_docking(
                        receptor_path, ligand_path, output_path,
                        center, size, engine_type=engine_type
                    )
                    
                    results[engine_type] = result
                except Exception as e:
                    results[engine_type] = {
                        'success': False,
                        'error': str(e)
                    }
        
        return results