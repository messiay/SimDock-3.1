import os
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
import threading
from typing import Dict, List, Optional, Any
import tkinter as tk
import traceback

from core.docking_manager import DockingManager
from core.file_manager import FileManager
from core.file_processor import FileProcessor
from core.session_manager import SessionManager
from core.project_manager import ProjectManager
from gui.dialogs import AdvancedSettingsDialog, ResultsDialog, BatchResultsDialog
from gui.docking_panel import DockingPanel
from gui.visualization_panel import VisualizationPanel
from gui.results_panel import ResultsPanel
from utils.config import get_config_manager


class MainWindow:
    """Main application window with modern GUI using customtkinter."""
    
    def __init__(self):
        # Initialize customtkinter
        ctk.set_appearance_mode("Dark")  # Modes: "System", "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("SimDock 3.1 - Advanced Molecular Docking")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Initialize core components
        self.docking_manager = DockingManager(default_engine="vina")
        self.file_manager = FileManager()
        self.file_processor = FileProcessor()
        self.session_manager = SessionManager()
        self.project_manager = ProjectManager()
        self.config_manager = get_config_manager()
        
        # Thread safety
        self.thread_lock = threading.Lock()
        self.docking_thread = None
        
        # Application state
        self._initialize_state()
        
        # Setup GUI
        self._setup_gui()
        
        # Setup project directory
        self._setup_project_directory()
    
    def _initialize_state(self):
        """Initialize application state variables."""
        # File paths
        self.receptor_path = tk.StringVar(value="")
        self.pdb_id = tk.StringVar(value="")
        self.pubchem_id = tk.StringVar(value="")
        
        # Ligand management
        self.ligand_library = []
        self.selected_ligand_index = tk.IntVar(value=0)
        
        # Docking parameters
        self.center_x = tk.DoubleVar(value=0.0)
        self.center_y = tk.DoubleVar(value=0.0)
        self.center_z = tk.DoubleVar(value=0.0)
        self.size_x = tk.DoubleVar(value=20.0)
        self.size_y = tk.DoubleVar(value=20.0)
        self.size_z = tk.DoubleVar(value=20.0)
        self.exhaustiveness = tk.IntVar(value=8)
        
        # Engine selection
        self.selected_engine = tk.StringVar(value="vina")
        self.available_engines = self.docking_manager.get_available_engines()
        
        # Settings
        self.docking_mode = tk.StringVar(value="Blind Docking")
        self.viewer_choice = tk.StringVar(value="ChimeraX")
        self.use_adaptive_exhaustiveness = tk.BooleanVar(value=False)
        self.use_hierarchical_docking = tk.BooleanVar(value=False)
        self.refine_percentage = tk.IntVar(value=10)
        
        # Results
        self.last_results = []
        self.batch_results_summary = []
        self.full_batch_results = []
        self.last_run_type = None
        self.receptor_pdbqt_path = None
        self.single_docking_output_path = None
        
        # Project management
        self.current_project_path = tk.StringVar(value="")
        self.projects_directory = os.path.join(os.path.expanduser("~"), "SimDock_Projects")
        
        # Threading control
        self.is_calculating = False
        self.is_docking = False
        self.cancel_docking = False
    
    def _setup_gui(self):
        """Setup the main GUI components."""
        # Create main container
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create header
        self._create_header()
        
        # Create tabview for main interface
        self._create_main_tabs()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_header(self):
        """Create application header with menu and project info."""
        header_frame = ctk.CTkFrame(self.main_container)
        header_frame.pack(fill="x", pady=(0, 10))
        
        # Title and logo
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="SimDock 3.1", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left", padx=10)
        
        # Project info
        project_label = ctk.CTkLabel(
            title_frame,
            textvariable=self.current_project_path,
            font=ctk.CTkFont(size=12)
        )
        project_label.pack(side="left", padx=20)
        
        # Menu buttons
        menu_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        menu_frame.pack(side="right")
        
        # Project buttons
        new_project_btn = ctk.CTkButton(
            menu_frame, 
            text="New Project", 
            command=self._create_new_project,
            width=100
        )
        new_project_btn.pack(side="left", padx=5)
        
        load_project_btn = ctk.CTkButton(
            menu_frame, 
            text="Load Project", 
            command=self._load_project,
            width=100
        )
        load_project_btn.pack(side="left", padx=5)
        
        # Settings button
        settings_btn = ctk.CTkButton(
            menu_frame,
            text="Settings",
            command=self._open_settings,
            width=80
        )
        settings_btn.pack(side="left", padx=5)
    
    def _create_main_tabs(self):
        """Create the main tabbed interface."""
        self.tabview = ctk.CTkTabview(self.main_container)
        self.tabview.pack(fill="both", expand=True)
        
        # Create tabs
        self.docking_tab = self.tabview.add("Docking Setup")
        self.results_tab = self.tabview.add("Results")
        self.visualization_tab = self.tabview.add("Visualization")
        
        # Initialize tab components - FIXED: Remove extra parameters
        self.docking_panel = DockingPanel(self.docking_tab, self)
        self.results_panel = ResultsPanel(self.results_tab, self)
        self.visualization_panel = VisualizationPanel(self.visualization_tab, self)
    
    def _create_status_bar(self):
        """Create status bar at bottom of window."""
        status_frame = ctk.CTkFrame(self.main_container)
        status_frame.pack(fill="x", pady=(10, 0))
        
        # Status label
        self.status_label = ctk.CTkLabel(
            status_frame, 
            text="Ready to start docking...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(status_frame)
        self.progress_bar.pack(side="right", padx=10, pady=5, fill="x", expand=True)
        self.progress_bar.set(0)
        
        # Cancel button (initially hidden)
        self.cancel_button = ctk.CTkButton(
            status_frame,
            text="Cancel",
            command=self.cancel_docking_process,
            width=80,
            fg_color="red",
            hover_color="darkred"
        )
        self.cancel_button.pack(side="right", padx=5)
        self.cancel_button.pack_forget()  # Hide initially
    
    def _setup_project_directory(self):
        """Setup projects directory if it doesn't exist."""
        os.makedirs(self.projects_directory, exist_ok=True)
    
    def _create_new_project(self):
        """Create a new project."""
        project_name = simpledialog.askstring(
            "New Project", 
            "Enter project name:",
            parent=self.root
        )
        
        if project_name:
            try:
                project_path = self.project_manager.create_new_project(
                    project_name, 
                    self.projects_directory
                )
                self.current_project_path.set(f"Project: {project_name}")
                self.update_status(f"Created new project: {project_name}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create project: {e}")
    
    def _load_project(self):
        """Load an existing project."""
        project_path = filedialog.askdirectory(
            title="Select Project Folder",
            initialdir=self.projects_directory
        )
        
        if project_path:
            try:
                project_data = self.project_manager.load_project(project_path)
                project_name = project_data['project_info']['name']
                self.current_project_path.set(f"Project: {project_name}")
                
                # Load project data into application state
                self._load_project_data(project_data)
                
                self.update_status(f"Loaded project: {project_name}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load project: {e}")
    
    def _load_project_data(self, project_data: Dict[str, Any]):
        """Load project data into application state."""
        # Load receptor and ligands
        if project_data.get('files', {}).get('receptors'):
            receptor = project_data['files']['receptors'][0]
            self.receptor_path.set(receptor['path'])
        
        if project_data.get('files', {}).get('ligands'):
            self.ligand_library = [ligand['path'] for ligand in project_data['files']['ligands']]
            self.docking_panel.refresh_ligand_list()
        
        # Load docking parameters if available
        if 'settings' in project_data:
            settings = project_data['settings']
            self.center_x.set(settings.get('center_x', 0.0))
            self.center_y.set(settings.get('center_y', 0.0))
            self.center_z.set(settings.get('center_z', 0.0))
            self.size_x.set(settings.get('size_x', 20.0))
            self.size_y.set(settings.get('size_y', 20.0))
            self.size_z.set(settings.get('size_z', 20.0))
    
    def _open_settings(self):
        """Open advanced settings dialog."""
        dialog = AdvancedSettingsDialog(self.root, self)
        dialog.show()
    
    def show_engine_info(self):
        """Show information about the selected engine."""
        engine_type = self.selected_engine.get()
        try:
            info = self.docking_manager.get_engine_info(engine_type)
            
            message = f"Engine: {info['name']}\n"
            message += f"Version: {info['version']}\n"
            message += f"Description: {info.get('description', 'No description available')}\n\n"
            message += "Default Parameters:\n"
            for key, value in info['default_parameters'].items():
                message += f"  {key}: {value}\n"
            
            messagebox.showinfo("Engine Information", message)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not get engine info: {e}")
    
    # Core functionality methods
    def select_receptor_file(self):
        """Select receptor file."""
        file_path = filedialog.askopenfilename(
            title="Select Receptor File",
            filetypes=[("PDB files", "*.pdb"), ("All files", "*.*")]
        )
        
        if file_path:
            self.receptor_path.set(file_path)
            self.update_status(f"Selected receptor: {os.path.basename(file_path)}")
            self._start_coordinate_calculation()
    
    def select_ligand_file(self):
        """Select single ligand file."""
        file_path = filedialog.askopenfilename(
            title="Select Ligand File",
            filetypes=[
                ("SDF files", "*.sdf"),
                ("MOL2 files", "*.mol2"), 
                ("PDB files", "*.pdb"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.ligand_library = [file_path]
            self.docking_panel.refresh_ligand_list()
            self.update_status(f"Selected ligand: {os.path.basename(file_path)}")
            self._start_coordinate_calculation()
    
    def import_ligand_folder(self):
        """Import folder of ligand files."""
        folder_path = filedialog.askdirectory(title="Select Ligand Folder")
        
        if folder_path:
            try:
                self.ligand_library.clear()
                supported_formats = ('.pdb', '.sdf', '.mol2')
                
                for filename in os.listdir(folder_path):
                    if filename.lower().endswith(supported_formats):
                        file_path = os.path.join(folder_path, filename)
                        self.ligand_library.append(file_path)
                
               self.docking_panel.refresh_ligand_list()
                self.update_status(f"Imported {len(self.ligand_library)} ligands")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import ligands: {e}")
    
    def fetch_pdb_structure(self):
        """Fetch receptor from PDB."""
        pdb_id = self.pdb_id.get().strip().upper()
        
        if not pdb_id or len(pdb_id) != 4:
            messagebox.showerror("Error", "Please enter a valid 4-character PDB ID")
            return
        
        def fetch_thread():
            try:
                self.update_status(f"Downloading {pdb_id} from PDB...")
                cleaned_path = self.file_processor.fetch_pdb_structure(pdb_id, self.file_manager.create_temp_directory())
                self.root.after(0, lambda p=cleaned_path, i=pdb_id: self._on_pdb_fetched(p, i))
            except Exception as e:
                self.root.after(0, lambda s=f"PDB {pdb_id}", err=str(e): self._on_fetch_error(s, err))
        
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    def _on_pdb_fetched(self, file_path: str, pdb_id: str):
        """Handle successful PDB fetch."""
        self.receptor_path.set(file_path)
        self.update_status(f"Downloaded and cleaned PDB: {pdb_id}")
        self._start_coordinate_calculation()
    
    def fetch_pubchem_ligand(self):
        """Fetch ligand from PubChem."""
        identifier = self.pubchem_id.get().strip()
        
        if not identifier:
            messagebox.showerror("Error", "Please enter a PubChem CID or name")
            return
        
        def fetch_thread():
            try:
                self.update_status(f"Downloading {identifier} from PubChem...")
                ligand_path = self.file_processor.fetch_pubchem_ligand(identifier, self.file_manager.create_temp_directory())
                self.root.after(0, lambda p=ligand_path, i=identifier: self._on_pubchem_fetched(p, i))
            except Exception as e:
                self.root.after(0, lambda s=f"PubChem {identifier}", err=str(e): self._on_fetch_error(s, err))
        
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    def _on_pubchem_fetched(self, file_path: str, identifier: str):
        """Handle successful PubChem fetch."""
        self.ligand_library = [file_path]
        self.docking_panel.refresh_ligand_list()
        self.update_status(f"Downloaded ligand: {identifier}")
        self._start_coordinate_calculation()
    
    def _on_fetch_error(self, source: str, error: str):
        """Handle fetch errors."""
        messagebox.showerror("Download Error", f"Failed to download from {source}:\n{error}")
        self.update_status("Download failed")
    
    def _start_coordinate_calculation(self):
        """Start coordinate calculation in background thread."""
        if self.is_calculating:
            return
        
        self.is_calculating = True
        
        def calculate_thread():
            try:
                receptor = self.receptor_path.get()
                if not receptor:
                    return
                
                # Calculate coordinates based on docking mode
                if self.docking_mode.get() == "Blind Docking":
                    coords = self.file_processor.get_coordinates_from_file(receptor, self.file_manager.create_temp_directory())
                    if coords:
                        center, size = self.file_processor.calculate_bounding_box(coords)
                        self.root.after(0, lambda c=center, s=size: self._on_coordinates_calculated(c, s))
                
                elif self.docking_mode.get() == "Targeted Docking" and self.ligand_library:
                    ligand_path = self.ligand_library[0]  # Use first ligand
                    coords = self.file_processor.get_coordinates_from_file(ligand_path, self.file_manager.create_temp_directory())
                    if coords:
                        center, size = self.file_processor.get_ligand_based_box(coords)
                        self.root.after(0, lambda c=center, s=size: self._on_coordinates_calculated(c, s))
                        
            except Exception as e:
                self.root.after(0, lambda err=str(e): self._on_calculation_error(err))
            finally:
                self.is_calculating = False
        
        threading.Thread(target=calculate_thread, daemon=True).start()
        self.update_status("Calculating docking coordinates...")
    
    def _on_coordinates_calculated(self, center: tuple, size: tuple):
        """Handle calculated coordinates."""
        self.center_x.set(round(center[0], 3))
        self.center_y.set(round(center[1], 3))
        self.center_z.set(round(center[2], 3))
        self.size_x.set(round(size[0], 3))
        self.size_y.set(round(size[1], 3))
        self.size_z.set(round(size[2], 3))
        self.update_status("Coordinates calculated successfully")
    
    def _on_calculation_error(self, error: str):
        """Handle coordinate calculation errors."""
        messagebox.showerror("Calculation Error", f"Failed to calculate coordinates:\n{error}")
        self.update_status("Coordinate calculation failed")
    
    def start_docking(self):
        """Start docking process."""
        if not self.receptor_path.get() or not self.ligand_library:
            messagebox.showerror("Error", "Please select a receptor and at least one ligand")
            return
        
        if self.is_docking:
            messagebox.showwarning("Warning", "Docking is already in progress")
            return
        
        self.is_docking = True
        self.cancel_docking = False
        self.progress_bar.set(0)
        
        # Show cancel button
        self.cancel_button.pack(side="right", padx=5)
        
        # Clear previous results under thread lock
        with self.thread_lock:
            self.last_results.clear()
            self.batch_results_summary.clear()
            self.full_batch_results.clear()
        
        def docking_thread():
            try:
                is_batch = len(self.ligand_library) > 1
                
                if is_batch:
                    self._run_batch_docking()
                else:
                    self._run_single_docking()
                    
            except Exception as e:
                self.root.after(0, lambda err=str(e): self._on_docking_error(err))
            finally:
                self.is_docking = False
                self.cancel_docking = False
                # Hide cancel button
                self.root.after(0, lambda: self.cancel_button.pack_forget())
        
        self.docking_thread = threading.Thread(target=docking_thread, daemon=True)
        self.docking_thread.start()
    
    def cancel_docking_process(self):
        """Cancel ongoing docking process."""
        if self.is_docking:
            self.cancel_docking = True
            self.update_status("Cancelling docking...")
    
    def _run_single_docking(self):
        """Run single ligand docking."""
        try:
            engine = self.docking_manager.get_engine(self.selected_engine.get())
            
            # Check cancellation
            if self.cancel_docking:
                self.root.after(0, lambda: self.update_status("Docking cancelled", 0))
                return
            
            # Prepare files
            self.root.after(0, lambda: self.update_status(f"Preparing receptor with {engine.get_name()}...", 10))
            receptor_pdbqt = engine.prepare_receptor(self.receptor_path.get(), self.file_manager.create_temp_directory())
            
            if not receptor_pdbqt:
                raise Exception("Failed to prepare receptor")
            
            # Check cancellation
            if self.cancel_docking:
                self.root.after(0, lambda: self.update_status("Docking cancelled", 0))
                return
            
            self.root.after(0, lambda: self.update_status("Preparing ligand...", 30))
            ligand_pdbqt = engine.prepare_ligand(self.ligand_library[0], self.file_manager.create_temp_directory())
            
            if not ligand_pdbqt:
                raise Exception("Failed to prepare ligand")
            
            # Check cancellation
            if self.cancel_docking:
                self.root.after(0, lambda: self.update_status("Docking cancelled", 0))
                return
            
            # Run docking
            self.root.after(0, lambda: self.update_status(f"Running {engine.get_name()}...", 50))
            output_path = os.path.join(self.file_manager.create_temp_directory(), "docked_poses.pdbqt")
            
            center = (self.center_x.get(), self.center_y.get(), self.center_z.get())
            size = (self.size_x.get(), self.size_y.get(), self.size_z.get())
            
            # Calculate exhaustiveness
            if self.use_adaptive_exhaustiveness.get():
                current_exhaustiveness = engine.get_adaptive_exhaustiveness(ligand_pdbqt)
            else:
                current_exhaustiveness = self.exhaustiveness.get()
            
            result = engine.run_docking(
                receptor_pdbqt, ligand_pdbqt, output_path,
                center, size, exhaustiveness=current_exhaustiveness
            )
            
            # Check cancellation
            if self.cancel_docking:
                self.root.after(0, lambda: self.update_status("Docking cancelled", 0))
                return
            
            if result['success']:
                with self.thread_lock:
                    self.last_results = result['scores']
                    self.single_docking_output_path = output_path
                    self.receptor_pdbqt_path = receptor_pdbqt
                    self.last_run_type = 'single'
                
                self.root.after(0, lambda r=result: self._on_docking_complete(r))
            else:
                error_msg = result.get('error', 'Docking failed')
                raise Exception(error_msg)
                
        except Exception as e:
            self.root.after(0, lambda err=str(e): self._on_docking_error(err))
    
    def _run_batch_docking(self):
        """Run batch docking with multiple ligands."""
        try:
            engine = self.docking_manager.get_engine(self.selected_engine.get())
            
            # Check cancellation
            if self.cancel_docking:
                self.root.after(0, lambda: self.update_status("Docking cancelled", 0))
                return
            
            self.root.after(0, lambda: self.update_status(f"Preparing receptor with {engine.get_name()}...", 5))
            receptor_pdbqt = engine.prepare_receptor(self.receptor_path.get(), self.file_manager.create_temp_directory())
            
            if not receptor_pdbqt:
                raise Exception("Failed to prepare receptor")
            
            # Initialize results under thread lock
            with self.thread_lock:
                self.batch_results_summary.clear()
                self.full_batch_results.clear()
            
            total_ligands = len(self.ligand_library)
            processed_ligands = 0
            
            for i, ligand_path in enumerate(self.ligand_library):
                # Check cancellation
                if self.cancel_docking:
                    self.root.after(0, lambda: self.update_status("Docking cancelled", 0))
                    return
                
                progress = 10 + (i / total_ligands) * 85
                ligand_name = os.path.basename(ligand_path)
                
                self.root.after(0, lambda p=progress, ln=ligand_name: self.update_status(f"Docking {ln} with {engine.get_name()}...", p))
                
                ligand_pdbqt = engine.prepare_ligand(ligand_path, self.file_manager.create_temp_directory())
                if not ligand_pdbqt:
                    # Record error but continue with other ligands
                    with self.thread_lock:
                        self.batch_results_summary.append({
                            'Ligand': ligand_name, 
                            'Best Affinity (kcal/mol)': 'PREPARATION_ERROR', 
                            'OutputFile': '',
                            'Engine': engine.get_name()
                        })
                    processed_ligands += 1
                    continue

                # Calculate exhaustiveness
                if self.use_adaptive_exhaustiveness.get():
                    current_exhaustiveness = engine.get_adaptive_exhaustiveness(ligand_pdbqt)
                else:
                    current_exhaustiveness = self.exhaustiveness.get()
                
                output_path = os.path.join(self.file_manager.create_temp_directory(), f"{ligand_name}_out.pdbqt")
                center = (self.center_x.get(), self.center_y.get(), self.center_z.get())
                size = (self.size_x.get(), self.size_y.get(), self.size_z.get())
                
                result = engine.run_docking(
                    receptor_pdbqt, ligand_pdbqt, output_path,
                    center, size, exhaustiveness=current_exhaustiveness
                )
                
                # Thread-safe result recording
                with self.thread_lock:
                    if result['success'] and result['scores']:
                        best_score = result['scores'][0]['Affinity (kcal/mol)']
                        for score_details in result['scores']:
                            self.full_batch_results.append({'Ligand': ligand_name, **score_details})
                    else:
                        best_score = 'DOCKING_ERROR'
                    
                    self.batch_results_summary.append({
                        'Ligand': ligand_name, 
                        'Best Affinity (kcal/mol)': best_score, 
                        'OutputFile': output_path,
                        'Engine': engine.get_name()
                    })
                
                processed_ligands += 1
            
            # Check if any ligands were successfully processed
            if processed_ligands == 0:
                raise Exception("No ligands were successfully processed")
            
            with self.thread_lock:
                self.receptor_pdbqt_path = receptor_pdbqt
                self.last_run_type = 'batch'
            
            self.root.after(0, self._on_batch_docking_complete)
            
        except Exception as e:
            self.root.after(0, lambda err=str(e): self._on_docking_error(err))
    
    def _on_docking_complete(self, result: Dict[str, Any]):
        """Handle single docking completion."""
        self.update_status("Docking completed successfully!", 100)
        self.is_docking = False
        self.cancel_docking = False
        
        # Switch to results tab
        self.tabview.set("Results")
        self.results_panel.show_single_results(self.last_results)
        
        # Auto-visualize if in single mode
        if len(self.ligand_library) == 1:
            self.visualize_results()
    
    def _on_batch_docking_complete(self):
        """Handle batch docking completion."""
        self.update_status("Batch docking completed!", 100)
        self.is_docking = False
        self.cancel_docking = False
        
        # Switch to results tab
        self.tabview.set("Results")
        self.results_panel.show_batch_results(self.batch_results_summary, self.full_batch_results)

    
    def _on_docking_error(self, error: str):
        """Handle docking errors."""
        error_msg = f"Docking failed:\n{error}"
        if self.cancel_docking:
            error_msg = "Docking was cancelled by user"
        
        self.root.after(0, lambda: messagebox.showerror("Docking Error", error_msg))
        self.update_status("Docking failed" if not self.cancel_docking else "Docking cancelled")
        self.is_docking = False
        self.cancel_docking = False
        self.progress_bar.set(0)
    
    def visualize_results(self):
        """Visualize docking results."""
        if self.last_run_type == 'single' and self.single_docking_output_path:
            # Switch to visualization tab first
            self.tabview.set("Visualization")
            self.visualization_panel.visualize_single_results(
                self.receptor_pdbqt_path, 
                self.single_docking_output_path,
                self.viewer_choice.get()
            )
        elif self.last_run_type == 'batch':
            # Switch to visualization tab and show batch options
            self.tabview.set("Visualization")
            self.visualization_panel.show_batch_visualization(self.batch_results_summary)
    
    def update_status(self, message: str, progress: Optional[float] = None):
        """Update status bar and progress."""
        self.status_label.configure(text=message)
        if progress is not None:
            self.progress_bar.set(progress / 100)
        self.root.update_idletasks()
    
    def run(self):
        """Start the application."""
        self.root.mainloop()
