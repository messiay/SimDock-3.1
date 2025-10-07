import os
import tempfile
import shutil
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

from utils.config import OBABEL_PATH, get_config_manager
from utils.helpers import run_command


class FileManager:
    """Centralized manager for all file operations and conversions."""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.temp_dirs = []
        self.max_temp_dirs = 50  # Limit to prevent memory growth
    
    def prepare_receptor(self, receptor_path: str, output_dir: str, 
                        remove_water: bool = True, remove_hetatm: bool = True) -> Optional[str]:
        """Prepare receptor file for docking by converting to PDBQT format."""
        try:
            # Validate input file
            if not self._validate_file(receptor_path, ['.pdb']):
                return None
            
            # Check file content validity
            validation_result = self.validate_structure(receptor_path)
            if not validation_result['valid']:
                print(f"Receptor validation failed: {validation_result.get('errors', ['Unknown error'])}")
                return None
            
            base_name = Path(receptor_path).stem
            output_path = os.path.join(output_dir, f"{base_name}_receptor.pdbqt")
            
            # Build Open Babel command for receptor preparation
            command = [
                OBABEL_PATH,
                "-ipdb", receptor_path,
                "-opdbqt",
                "-O", output_path,
                "-xr"  # Remove non-standard residues for receptor
            ]
            
            # Add cleaning options
            if remove_water:
                command.extend(["-d"])  # Delete water molecules
            
            if remove_hetatm:
                command.extend(["-xr"])  # Remove HETATM records
            
            result = run_command(command)
            
            if result and os.path.exists(output_path):
                # Verify output file is valid
                output_validation = self.validate_structure(output_path)
                if output_validation['valid']:
                    return output_path
                else:
                    print(f"Prepared receptor validation failed: {output_validation.get('errors')}")
                    return None
            else:
                error_msg = result.stderr if result else 'Unknown error'
                print(f"Receptor preparation failed: {error_msg}")
                return None
                
        except Exception as e:
            print(f"Error preparing receptor: {e}")
            return None
    
    def prepare_ligand(self, ligand_path: str, output_dir: str, 
                      add_hydrogens: bool = True, pH: float = 7.4) -> Optional[str]:
        """Prepare ligand file for docking by converting to PDBQT format."""
        try:
            # Validate input file and get format
            file_ext = Path(ligand_path).suffix.lower()
            if not self._validate_file(ligand_path, ['.pdb', '.sdf', '.mol2']):
                return None
            
            # Check file content validity
            validation_result = self.validate_structure(ligand_path)
            if not validation_result['valid']:
                print(f"Ligand validation failed: {validation_result.get('errors', ['Unknown error'])}")
                return None
            
            base_name = Path(ligand_path).stem
            output_path = os.path.join(output_dir, f"{base_name}_ligand.pdbqt")
            
            # Build Open Babel command for ligand preparation
            command = [
                OBABEL_PATH,
                f"-i{file_ext[1:]}", ligand_path,  # Remove dot from extension
                "-opdbqt",
                "-O", output_path
            ]
            
            # Add preparation options
            if add_hydrogens:
                command.extend(["-h"])  # Add hydrogens
            
            command.extend(["-p", str(pH)])  # Set pH for protonation
            
            result = run_command(command)
            
            if result and os.path.exists(output_path):
                # Verify output file is valid
                output_validation = self.validate_structure(output_path)
                if output_validation['valid']:
                    return output_path
                else:
                    print(f"Prepared ligand validation failed: {output_validation.get('errors')}")
                    return None
            else:
                error_msg = result.stderr if result else 'Unknown error'
                print(f"Ligand preparation failed: {error_msg}")
                return None
                
        except Exception as e:
            print(f"Error preparing ligand: {e}")
            return None
    
    def create_temp_directory(self, prefix: str = "simdock_") -> str:
        """Create a temporary directory and track it for cleanup."""
        # Clean up if we have too many temp directories
        if len(self.temp_dirs) >= self.max_temp_dirs:
            self.cleanup_temp_directories()
        
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def cleanup_temp_directories(self):
        """Clean up all temporary directories created by this manager."""
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"Error cleaning up temp directory {temp_dir}: {e}")
        
        self.temp_dirs.clear()
    
    def _validate_file(self, file_path: str, allowed_extensions: List[str]) -> bool:
        """Validate that a file exists and has an allowed extension and content."""
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return False
        
        if not os.path.isfile(file_path):
            print(f"Path is not a file: {file_path}")
            return False
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            print(f"File is empty: {file_path}")
            return False
        
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in allowed_extensions:
            print(f"Unsupported file format: {file_ext}. Allowed: {allowed_extensions}")
            return False
        
        # Additional content validation using file signatures
        if not self._validate_file_signature(file_path, file_ext):
            print(f"File signature validation failed: {file_path}")
            return False
        
        return True
    
    def _validate_file_signature(self, file_path: str, file_ext: str) -> bool:
        """Validate file using basic signature checking."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = [f.readline().strip() for _ in range(5)]
                
            if file_ext == '.pdb':
                # PDB files should start with ATOM, HETATM, HEADER, etc.
                valid_starts = ('ATOM', 'HETATM', 'HEADER', 'TITLE', 'COMPND', 'REMARK')
                return any(line.startswith(valid_starts) for line in first_lines if line)
            
            elif file_ext == '.sdf':
                # SDF files should have specific structure
                return any('V2000' in line or 'V3000' in line for line in first_lines if line)
            
            elif file_ext == '.mol2':
                # MOL2 files should start with @<TRIPOS>MOLECULE
                return any(line.startswith('@<TRIPOS>') for line in first_lines if line)
            
            # For unknown formats, assume valid
            return True
            
        except Exception:
            return False
    
    def validate_structure(self, file_path: str) -> Dict[str, Any]:
        """Validate molecular structure and return any issues."""
        try:
            if not os.path.exists(file_path):
                return {
                    "valid": False,
                    "readable": False,
                    "errors": [f"File does not exist: {file_path}"]
                }
            
            file_ext = Path(file_path).suffix[1:]  # Remove dot
            
            command = [
                OBABEL_PATH,
                f"-i{file_ext}", file_path,
                "-o", "smi",  # Convert to SMILES to check readability
                "--errorlevel", "2"  # Show warnings and errors
            ]
            
            result = run_command(command)
            
            validation_result = {
                "valid": result is not None and result.returncode == 0,
                "readable": bool(result and result.stdout),
                "warnings": [],
                "errors": []
            }
            
            if result:
                # Parse Open Babel output for warnings and errors
                if result.stderr:
                    lines = result.stderr.strip().split('\n')
                    for line in lines:
                        line_lower = line.lower()
                        if "error" in line_lower:
                            validation_result["errors"].append(line)
                        elif "warning" in line_lower:
                            validation_result["warnings"].append(line)
                
                # Check if conversion produced any output
                if not result.stdout.strip():
                    validation_result["errors"].append("File could not be converted to SMILES format")
                    validation_result["valid"] = False
                    validation_result["readable"] = False
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "readable": False,
                "errors": [f"Validation failed: {e}"]
            }
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported file formats."""
        return {
            'receptor': ['.pdb'],
            'ligand': ['.pdb', '.sdf', '.mol2']
        }
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get basic information about a molecular file."""
        try:
            # Use Open Babel to get file information
            file_ext = Path(file_path).suffix[1:]
            command = [
                OBABEL_PATH,
                f"-i{file_ext}", file_path,
                "-o", "smi",
                "--append", "title",
                "--errorlevel", "1"
            ]
            
            result = run_command(command)
            
            info = {
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'rotatable_bonds': 0,
                'heavy_atoms': 0,
                'readable': bool(result and result.stdout)
            }
            
            # Basic rotatable bond estimation (simplified)
            if result and result.stdout:
                # Count number of lines as a rough estimate of molecules/conformers
                lines = result.stdout.strip().split('\n')
                info['molecule_count'] = len([l for l in lines if l.strip()])
                
                # Very basic rotatable bond estimation
                # This is a simplified approach - in production you'd want more sophisticated analysis
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Rough estimate based on common patterns
                    info['rotatable_bonds'] = content.count('ROTATABLE') + content.count('TOR') // 2
            
            return info
            
        except Exception as e:
            return {
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'rotatable_bonds': 0,
                'heavy_atoms': 0,
                'readable': False,
                'error': str(e)
            }