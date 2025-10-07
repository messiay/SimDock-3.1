import os
import json
import shutil
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class ProjectManager:
    """
    Manages SimDock projects with organized folder structure and file management.
    Each project is stored in a dedicated folder with all necessary files.
    """
    
    def __init__(self):
        self.current_project_path: Optional[str] = None
        self.project_data: Dict[str, Any] = {}
    
    def create_new_project(self, project_name: str, base_directory: str) -> str:
        """
        Create a new project with organized folder structure.
        
        Args:
            project_name: Name for the new project
            base_directory: Directory where project folder will be created
            
        Returns:
            Path to the created project folder
        """
        try:
            # Create project folder with timestamp and unique ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            folder_name = f"{project_name}_{timestamp}_{unique_id}"
            project_path = os.path.join(base_directory, folder_name)
            
            # Create main project folder
            os.makedirs(project_path, exist_ok=True)
            
            # Create subdirectories
            subdirs = [
                'receptors',
                'ligands',
                'results',
                'docking_runs',
                'temp',
                'backups'
            ]
            
            for subdir in subdirs:
                os.makedirs(os.path.join(project_path, subdir), exist_ok=True)
            
            # Initialize project data
            self.project_data = {
                'project_info': {
                    'name': project_name,
                    'created': datetime.now().isoformat(),
                    'version': '1.0',
                    'simdock_version': '3.1'
                },
                'files': {
                    'receptors': [],
                    'ligands': [],
                    'results': []
                },
                'docking_sessions': [],
                'settings': {},
                'metadata': {}
            }
            
            self.current_project_path = project_path
            self._save_project_file()
            
            return project_path
            
        except Exception as e:
            raise Exception(f"Failed to create project: {e}")
    
    def load_project(self, project_path: str) -> Dict[str, Any]:
        """
        Load an existing project.
        
        Args:
            project_path: Path to project folder or project.json file
            
        Returns:
            Project data dictionary
        """
        try:
            # If path is to project.json, get the folder path
            if project_path.endswith('project.json'):
                project_path = os.path.dirname(project_path)
            
            project_file = os.path.join(project_path, 'project.json')
            
            if not os.path.exists(project_file):
                raise FileNotFoundError(f"Project file not found: {project_file}")
            
            with open(project_file, 'r') as f:
                self.project_data = json.load(f)
            
            self.current_project_path = project_path
            
            # Update paths to be absolute
            self._update_paths_to_absolute()
            
            return self.project_data
            
        except Exception as e:
            raise Exception(f"Failed to load project: {e}")
    
    def save_project(self) -> bool:
        """Save current project state."""
        if not self.current_project_path:
            raise Exception("No project loaded")
        
        try:
            # Update modification time
            self.project_data['project_info']['modified'] = datetime.now().isoformat()
            
            # Convert absolute paths to relative before saving
            self._update_paths_to_relative()
            
            self._save_project_file()
            
            # Convert back to absolute for continued use
            self._update_paths_to_absolute()
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to save project: {e}")
    
    def add_receptor(self, receptor_path: str, copy_file: bool = True) -> str:
        """
        Add a receptor file to the project.
        
        Args:
            receptor_path: Path to receptor file
            copy_file: Whether to copy the file to project folder
            
        Returns:
            Path to receptor file in project (relative or absolute)
        """
        if not self.current_project_path:
            raise Exception("No project loaded")
        
        try:
            receptor_name = os.path.basename(receptor_path)
            
            if copy_file:
                # Copy to project receptors folder
                project_receptor_path = os.path.join(
                    self.current_project_path, 'receptors', receptor_name
                )
                shutil.copy2(receptor_path, project_receptor_path)
                stored_path = project_receptor_path
            else:
                stored_path = receptor_path
            
            # Add to project data
            receptor_info = {
                'name': receptor_name,
                'path': stored_path,
                'added': datetime.now().isoformat(),
                'file_size': os.path.getsize(receptor_path)
            }
            
            self.project_data['files']['receptors'].append(receptor_info)
            self.save_project()
            
            return stored_path
            
        except Exception as e:
            raise Exception(f"Failed to add receptor: {e}")
    
    def add_ligands(self, ligand_paths: List[str], copy_files: bool = True) -> List[str]:
        """
        Add multiple ligand files to the project.
        
        Args:
            ligand_paths: List of paths to ligand files
            copy_files: Whether to copy files to project folder
            
        Returns:
            List of paths to ligand files in project
        """
        if not self.current_project_path:
            raise Exception("No project loaded")
        
        try:
            project_ligand_paths = []
            
            for ligand_path in ligand_paths:
                ligand_name = os.path.basename(ligand_path)
                
                if copy_files:
                    # Copy to project ligands folder
                    project_ligand_path = os.path.join(
                        self.current_project_path, 'ligands', ligand_name
                    )
                    shutil.copy2(ligand_path, project_ligand_path)
                    stored_path = project_ligand_path
                else:
                    stored_path = ligand_path
                
                # Add to project data
                ligand_info = {
                    'name': ligand_name,
                    'path': stored_path,
                    'added': datetime.now().isoformat(),
                    'file_size': os.path.getsize(ligand_path)
                }
                
                self.project_data['files']['ligands'].append(ligand_info)
                project_ligand_paths.append(stored_path)
            
            self.save_project()
            return project_ligand_paths
            
        except Exception as e:
            raise Exception(f"Failed to add ligands: {e}")
    
    def save_docking_session(self, session_data: Dict[str, Any]) -> str:
        """
        Save a docking session to the project.
        
        Args:
            session_data: Docking session data
            
        Returns:
            Path to saved session file
        """
        if not self.current_project_path:
            raise Exception("No project loaded")
        
        try:
            # Create session ID and timestamp
            session_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_name = f"docking_session_{timestamp}_{session_id}"
            
            # Create session folder
            session_folder = os.path.join(self.current_project_path, 'docking_runs', session_name)
            os.makedirs(session_folder, exist_ok=True)
            
            # Copy result files to session folder
            copied_files = {}
            if 'receptor_pdbqt_path' in session_data and os.path.exists(session_data['receptor_pdbqt_path']):
                receptor_name = os.path.basename(session_data['receptor_pdbqt_path'])
                new_receptor_path = os.path.join(session_folder, receptor_name)
                shutil.copy2(session_data['receptor_pdbqt_path'], new_receptor_path)
                copied_files['receptor_pdbqt_path'] = new_receptor_path
            
            if 'single_docking_output_path' in session_data and os.path.exists(session_data['single_docking_output_path']):
                result_name = os.path.basename(session_data['single_docking_output_path'])
                new_result_path = os.path.join(session_folder, result_name)
                shutil.copy2(session_data['single_docking_output_path'], new_result_path)
                copied_files['single_docking_output_path'] = new_result_path
            
            # Copy batch result files
            batch_files = []
            for result in session_data.get('batch_results_summary', []):
                if result.get('OutputFile') and os.path.exists(result['OutputFile']):
                    result_name = os.path.basename(result['OutputFile'])
                    new_result_path = os.path.join(session_folder, result_name)
                    shutil.copy2(result['OutputFile'], new_result_path)
                    batch_files.append({
                        'Ligand': result['Ligand'],
                        'OutputFile': new_result_path
                    })
            
            # Update session data with new paths
            session_data.update(copied_files)
            if batch_files:
                session_data['batch_files'] = batch_files
            
            # Save session file
            session_file = os.path.join(session_folder, 'session.json')
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=4)
            
            # Add to project data
            session_info = {
                'name': session_name,
                'session_file': session_file,
                'created': datetime.now().isoformat(),
                'type': session_data.get('last_run_type', 'unknown'),
                'ligand_count': len(session_data.get('ligand_library', [])),
                'results_count': len(session_data.get('last_results', [])) + len(session_data.get('batch_results_summary', []))
            }
            
            self.project_data['docking_sessions'].append(session_info)
            self.save_project()
            
            return session_file
            
        except Exception as e:
            raise Exception(f"Failed to save docking session: {e}")
    
    def export_results(self, output_format: str = 'csv', include_files: bool = True) -> str:
        """
        Export project results in specified format.
        
        Args:
            output_format: Export format ('csv', 'json', 'xlsx')
            include_files: Whether to include result files in export
            
        Returns:
            Path to export file/folder
        """
        if not self.current_project_path:
            raise Exception("No project loaded")
        
        try:
            export_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_name = f"project_export_{export_time}"
            export_path = os.path.join(self.current_project_path, 'exports', export_name)
            os.makedirs(export_path, exist_ok=True)
            
            if output_format == 'csv':
                self._export_to_csv(export_path)
            elif output_format == 'json':
                self._export_to_json(export_path)
            elif output_format == 'xlsx':
                self._export_to_excel(export_path)
            
            if include_files:
                # Copy important files to export folder
                self._copy_files_for_export(export_path)
            
            return export_path
            
        except Exception as e:
            raise Exception(f"Failed to export project: {e}")
    
    def get_project_summary(self) -> Dict[str, Any]:
        """Get summary of project contents."""
        if not self.current_project_path:
            raise Exception("No project loaded")
        
        summary = {
            'project_info': self.project_data.get('project_info', {}),
            'file_counts': {
                'receptors': len(self.project_data.get('files', {}).get('receptors', [])),
                'ligands': len(self.project_data.get('files', {}).get('ligands', [])),
                'sessions': len(self.project_data.get('docking_sessions', []))
            },
            'total_file_size': self._calculate_total_size(),
            'recent_sessions': self.project_data.get('docking_sessions', [])[-5:]  # Last 5 sessions
        }
        
        return summary
    
    def backup_project(self) -> str:
        """Create a backup of the entire project."""
        if not self.current_project_path:
            raise Exception("No project loaded")
        
        try:
            backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"project_backup_{backup_time}"
            backup_path = os.path.join(self.current_project_path, 'backups', backup_name)
            
            # Create zip of entire project
            shutil.make_archive(backup_path, 'zip', self.current_project_path)
            
            # Add backup info to project
            backup_info = {
                'name': backup_name,
                'path': f"{backup_path}.zip",
                'created': datetime.now().isoformat(),
                'size': os.path.getsize(f"{backup_path}.zip")
            }
            
            if 'backups' not in self.project_data:
                self.project_data['backups'] = []
            
            self.project_data['backups'].append(backup_info)
            self.save_project()
            
            return f"{backup_path}.zip"
            
        except Exception as e:
            raise Exception(f"Failed to create backup: {e}")
    
    def _save_project_file(self):
        """Save project.json file."""
        project_file = os.path.join(self.current_project_path, 'project.json')
        with open(project_file, 'w') as f:
            json.dump(self.project_data, f, indent=4)
    
    def _update_paths_to_relative(self):
        """Convert absolute paths to relative paths for storage."""
        if not self.current_project_path:
            return
        
        # Update receptor paths
        for receptor in self.project_data.get('files', {}).get('receptors', []):
            if 'path' in receptor and os.path.isabs(receptor['path']):
                receptor['path'] = os.path.relpath(receptor['path'], self.current_project_path)
        
        # Update ligand paths
        for ligand in self.project_data.get('files', {}).get('ligands', []):
            if 'path' in ligand and os.path.isabs(ligand['path']):
                ligand['path'] = os.path.relpath(ligand['path'], self.current_project_path)
        
        # Update session paths
        for session in self.project_data.get('docking_sessions', []):
            if 'session_file' in session and os.path.isabs(session['session_file']):
                session['session_file'] = os.path.relpath(session['session_file'], self.current_project_path)
    
    def _update_paths_to_absolute(self):
        """Convert relative paths to absolute paths for use."""
        if not self.current_project_path:
            return
        
        # Update receptor paths
        for receptor in self.project_data.get('files', {}).get('receptors', []):
            if 'path' in receptor and not os.path.isabs(receptor['path']):
                receptor['path'] = os.path.join(self.current_project_path, receptor['path'])
        
        # Update ligand paths
        for ligand in self.project_data.get('files', {}).get('ligands', []):
            if 'path' in ligand and not os.path.isabs(ligand['path']):
                ligand['path'] = os.path.join(self.current_project_path, ligand['path'])
        
        # Update session paths
        for session in self.project_data.get('docking_sessions', []):
            if 'session_file' in session and not os.path.isabs(session['session_file']):
                session['session_file'] = os.path.join(self.current_project_path, session['session_file'])
    
    def _calculate_total_size(self) -> int:
        """Calculate total size of project files."""
        total_size = 0
        
        # Calculate size of all files in project
        for root, dirs, files in os.walk(self.current_project_path):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
        
        return total_size
    
    def _export_to_csv(self, export_path: str):
        """Export project data to CSV format."""
        # Implementation for CSV export
        pass
    
    def _export_to_json(self, export_path: str):
        """Export project data to JSON format."""
        export_file = os.path.join(export_path, 'project_export.json')
        with open(export_file, 'w') as f:
            json.dump(self.project_data, f, indent=4)
    
    def _export_to_excel(self, export_path: str):
        """Export project data to Excel format."""
        # Implementation for Excel export (would require openpyxl)
        pass
    
    def _copy_files_for_export(self, export_path: str):
        """Copy important files for export."""
        # Copy receptors
        receptors_dir = os.path.join(export_path, 'receptors')
        os.makedirs(receptors_dir, exist_ok=True)
        for receptor in self.project_data.get('files', {}).get('receptors', []):
            if os.path.exists(receptor['path']):
                shutil.copy2(receptor['path'], receptors_dir)
        
        # Copy ligands
        ligands_dir = os.path.join(export_path, 'ligands')
        os.makedirs(ligands_dir, exist_ok=True)
        for ligand in self.project_data.get('files', {}).get('ligands', []):
            if os.path.exists(ligand['path']):
                shutil.copy2(ligand['path'], ligands_dir)
        
        # Copy session results
        results_dir = os.path.join(export_path, 'results')
        os.makedirs(results_dir, exist_ok=True)
        for session in self.project_data.get('docking_sessions', []):
            if os.path.exists(session['session_file']):
                shutil.copy2(session['session_file'], results_dir)


class ProjectBrowser:
    """
    Utility class for browsing and managing multiple projects.
    """
    
    @staticmethod
    def list_projects(projects_directory: str) -> List[Dict[str, Any]]:
        """
        List all projects in a directory.
        
        Args:
            projects_directory: Directory containing projects
            
        Returns:
            List of project information dictionaries
        """
        projects = []
        
        if not os.path.exists(projects_directory):
            return projects
        
        for item in os.listdir(projects_directory):
            item_path = os.path.join(projects_directory, item)
            project_file = os.path.join(item_path, 'project.json')
            
            if os.path.isdir(item_path) and os.path.exists(project_file):
                try:
                    with open(project_file, 'r') as f:
                        project_data = json.load(f)
                    
                    project_info = {
                        'name': project_data.get('project_info', {}).get('name', item),
                        'path': item_path,
                        'created': project_data.get('project_info', {}).get('created', ''),
                        'modified': project_data.get('project_info', {}).get('modified', ''),
                        'file_count': len(project_data.get('files', {}).get('receptors', [])) +
                                     len(project_data.get('files', {}).get('ligands', [])),
                        'session_count': len(project_data.get('docking_sessions', []))
                    }
                    
                    projects.append(project_info)
                    
                except Exception:
                    # Skip projects that can't be read
                    continue
        
        # Sort by modification time (newest first)
        projects.sort(key=lambda x: x.get('modified', ''), reverse=True)
        
        return projects
    
    @staticmethod
    def get_recent_projects(projects_directory: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get most recently modified projects.
        
        Args:
            projects_directory: Directory containing projects
            limit: Maximum number of projects to return
            
        Returns:
            List of recent project information
        """
        all_projects = ProjectBrowser.list_projects(projects_directory)
        return all_projects[:limit]