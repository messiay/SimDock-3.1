import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from typing import List, Dict, Optional, Callable
import customtkinter as ctk
import subprocess
import sys


class DockingSetupTab:
    """Docking setup tab component."""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the docking setup tab UI."""
        # Main frame with scrollbar
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollable frame
        self.canvas = tk.Canvas(main_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ctk.CTkFrame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        
        # Setup content
        self._create_receptor_section()
        self._create_ligand_section()
        self._create_docking_section()
        self._create_control_buttons()
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _create_receptor_section(self):
        """Create receptor selection section."""
        receptor_frame = ctk.CTkFrame(self.scrollable_frame)
        receptor_frame.pack(fill="x", pady=(0, 10), padx=10)
        
        # Title
        title_label = ctk.CTkLabel(
            receptor_frame, 
            text="Receptor Setup", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(anchor="w", pady=(10, 5), padx=10)
        
        # File selection
        file_frame = ctk.CTkFrame(receptor_frame, fg_color="transparent")
        file_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(file_frame, text="Receptor File:").pack(side="left")
        ctk.CTkEntry(
            file_frame, 
            textvariable=self.app.receptor_path,
            width=300
        ).pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkButton(
            file_frame, 
            text="Browse", 
            command=self.app.select_receptor_file,
            width=80
        ).pack(side="right", padx=5)
        
        # PDB download
        pdb_frame = ctk.CTkFrame(receptor_frame, fg_color="transparent")
        pdb_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(pdb_frame, text="Or fetch from PDB:").pack(side="left")
        ctk.CTkEntry(
            pdb_frame, 
            textvariable=self.app.pdb_id,
            placeholder_text="Enter PDB ID (e.g., 1ABC)",
            width=120
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            pdb_frame, 
            text="Download", 
            command=self.app.fetch_pdb_structure,
            width=80
        ).pack(side="right", padx=5)
    
    def _create_ligand_section(self):
        """Create ligand selection section."""
        ligand_frame = ctk.CTkFrame(self.scrollable_frame)
        ligand_frame.pack(fill="x", pady=(0, 10), padx=10)
        
        # Title
        title_label = ctk.CTkLabel(
            ligand_frame, 
            text="Ligand Setup", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(anchor="w", pady=(10, 5), padx=10)
        
        # Single ligand selection
        single_frame = ctk.CTkFrame(ligand_frame, fg_color="transparent")
        single_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkButton(
            single_frame, 
            text="Select Single Ligand", 
            command=self.app.select_ligand_file,
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            single_frame, 
            text="Import Ligand Folder", 
            command=self.app.import_ligand_folder,
            width=150
        ).pack(side="left", padx=5)
        
        # PubChem download
        pubchem_frame = ctk.CTkFrame(ligand_frame, fg_color="transparent")
        pubchem_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(pubchem_frame, text="Or fetch from PubChem:").pack(side="left")
        ctk.CTkEntry(
            pubchem_frame, 
            textvariable=self.app.pubchem_id,
            placeholder_text="Enter CID or name",
            width=150
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            pubchem_frame, 
            text="Download", 
            command=self.app.fetch_pubchem_ligand,
            width=80
        ).pack(side="right", padx=5)
        
        # Ligand list
        list_frame = ctk.CTkFrame(ligand_frame)
        list_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(list_frame, text="Selected Ligands:").pack(anchor="w", pady=(5, 0), padx=5)
        
        # Create listbox with scrollbar
        list_container = ctk.CTkFrame(list_frame)
        list_container.pack(fill="x", padx=5, pady=5)
        
        self.ligand_listbox = tk.Listbox(
            list_container, 
            height=6,
            bg='#343638',
            fg='white',
            selectbackground='#3b8ed0',
            selectforeground='white'
        )
        scrollbar = ttk.Scrollbar(list_container, orient="vertical")
        
        self.ligand_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.ligand_listbox.yview)
        
        self.ligand_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_docking_section(self):
        """Create docking parameters section."""
        docking_frame = ctk.CTkFrame(self.scrollable_frame)
        docking_frame.pack(fill="x", pady=(0, 10), padx=10)
        
        # Title
        title_label = ctk.CTkLabel(
            docking_frame, 
            text="Docking Parameters", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(anchor="w", pady=(10, 5), padx=10)
        
        # Docking mode
        mode_frame = ctk.CTkFrame(docking_frame, fg_color="transparent")
        mode_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(mode_frame, text="Docking Mode:").pack(side="left")
        mode_combo = ctk.CTkComboBox(
            mode_frame,
            values=["Blind Docking", "Targeted Docking"],
            variable=self.app.docking_mode,
            state="readonly",
            width=150
        )
        mode_combo.pack(side="left", padx=5)
        
        # Engine selection
        engine_frame = ctk.CTkFrame(docking_frame, fg_color="transparent")
        engine_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(engine_frame, text="Docking Engine:").pack(side="left")
        engine_combo = ctk.CTkComboBox(
            engine_frame,
            values=self.app.available_engines,
            variable=self.app.selected_engine,
            state="readonly",
            width=150
        )
        engine_combo.pack(side="left", padx=5)
        
        ctk.CTkButton(
            engine_frame,
            text="Info",
            command=self.app.show_engine_info,
            width=60
        ).pack(side="left", padx=5)
        
        # Coordinates
        coords_frame = ctk.CTkFrame(docking_frame)
        coords_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(coords_frame, text="Docking Box Center (Å):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkLabel(coords_frame, text="X:").grid(row=0, column=1, padx=2)
        ctk.CTkEntry(coords_frame, textvariable=self.app.center_x, width=80).grid(row=0, column=2, padx=2)
        ctk.CTkLabel(coords_frame, text="Y:").grid(row=0, column=3, padx=2)
        ctk.CTkEntry(coords_frame, textvariable=self.app.center_y, width=80).grid(row=0, column=4, padx=2)
        ctk.CTkLabel(coords_frame, text="Z:").grid(row=0, column=5, padx=2)
        ctk.CTkEntry(coords_frame, textvariable=self.app.center_z, width=80).grid(row=0, column=6, padx=2)
        
        ctk.CTkLabel(coords_frame, text="Docking Box Size (Å):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkLabel(coords_frame, text="X:").grid(row=1, column=1, padx=2)
        ctk.CTkEntry(coords_frame, textvariable=self.app.size_x, width=80).grid(row=1, column=2, padx=2)
        ctk.CTkLabel(coords_frame, text="Y:").grid(row=1, column=3, padx=2)
        ctk.CTkEntry(coords_frame, textvariable=self.app.size_y, width=80).grid(row=1, column=4, padx=2)
        ctk.CTkLabel(coords_frame, text="Z:").grid(row=1, column=5, padx=2)
        ctk.CTkEntry(coords_frame, textvariable=self.app.size_z, width=80).grid(row=1, column=6, padx=2)
        
        # Exhaustiveness
        exh_frame = ctk.CTkFrame(docking_frame, fg_color="transparent")
        exh_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(exh_frame, text="Exhaustiveness:").pack(side="left")
        ctk.CTkEntry(exh_frame, textvariable=self.app.exhaustiveness, width=80).pack(side="left", padx=5)
        
        ctk.CTkCheckBox(
            exh_frame,
            text="Adaptive Exhaustiveness",
            variable=self.app.use_adaptive_exhaustiveness
        ).pack(side="left", padx=20)
    
    def _create_control_buttons(self):
        """Create control buttons section."""
        button_frame = ctk.CTkFrame(self.scrollable_frame)
        button_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkButton(
            button_frame,
            text="Advanced Settings",
            command=self.app._open_settings,
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Calculate Coordinates",
            command=self.app._start_coordinate_calculation,
            width=140
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Start Docking",
            command=self.app.start_docking,
            fg_color="#2aa876",
            hover_color="#228c61",
            width=120
        ).pack(side="right", padx=5)
    
    def refresh_ligand_list(self):
        """Refresh the ligand list display."""
        if hasattr(self, 'ligand_listbox'):
            self.ligand_listbox.delete(0, tk.END)
            for ligand_path in self.app.ligand_library:
                ligand_name = os.path.basename(ligand_path)
                self.ligand_listbox.insert(tk.END, ligand_name)


class ResultsTab:
    """Results display tab component."""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the results tab UI."""
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        self.title_label = ctk.CTkLabel(
            main_frame,
            text="Docking Results",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_label.pack(anchor="w", pady=(0, 10))
        
        # Results container
        self.results_frame = ctk.CTkFrame(main_frame)
        self.results_frame.pack(fill="both", expand=True)
        
        # Initial message
        self.initial_label = ctk.CTkLabel(
            self.results_frame,
            text="No docking results yet. Run a docking simulation to see results here.",
            font=ctk.CTkFont(size=14)
        )
        self.initial_label.pack(expand=True)
        
        # Buttons frame (initially hidden)
        self.button_frame = ctk.CTkFrame(main_frame)
        
        self.visualize_button = ctk.CTkButton(
            self.button_frame,
            text="Visualize Results",
            command=self.app.visualize_results,
            width=120
        )
        
        self.save_button = ctk.CTkButton(
            self.button_frame,
            text="Save Results",
            command=self._save_results,
            width=120
        )
    
    def show_single_results(self, results: List[Dict]):
        """Show single docking results."""
        self._clear_results()
        self.title_label.configure(text="Single Docking Results")
        
        if not results:
            self._show_message("No results to display.")
            return
        
        # Create results table
        tree_frame = ctk.CTkFrame(self.results_frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create treeview
        from tkinter import ttk
        
        columns = ('mode', 'affinity', 'rmsd_lb', 'rmsd_ub')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)
        
        # Configure columns
        tree.heading('mode', text='Mode')
        tree.heading('affinity', text='Affinity (kcal/mol)')
        tree.heading('rmsd_lb', text='RMSD L.B.')
        tree.heading('rmsd_ub', text='RMSD U.B.')
        
        tree.column('mode', width=80, anchor=tk.CENTER)
        tree.column('affinity', width=120, anchor=tk.CENTER)
        tree.column('rmsd_lb', width=100, anchor=tk.CENTER)
        tree.column('rmsd_ub', width=100, anchor=tk.CENTER)
        
        # Populate data
        for score in results:
            tree.insert('', tk.END, values=(
                score.get('Mode', ''),
                f"{score.get('Affinity (kcal/mol)', ''):.2f}",
                f"{score.get('RMSD L.B.', ''):.2f}",
                f"{score.get('RMSD U.B.', ''):.2f}"
            ))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Show buttons
        self._show_buttons()
    
    def show_batch_results(self, summary_results: List[Dict], full_results: List[Dict]):
        """Show batch docking results."""
        self._clear_results()
        self.title_label.configure(text=f"Batch Docking Results ({len(summary_results)} ligands)")
        
        if not summary_results:
            self._show_message("No results to display.")
            return
        
        # Create results table
        tree_frame = ctk.CTkFrame(self.results_frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create treeview
        from tkinter import ttk
        
        columns = ('ligand', 'affinity', 'engine')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        tree.heading('ligand', text='Ligand')
        tree.heading('affinity', text='Best Affinity (kcal/mol)')
        tree.heading('engine', text='Engine')
        
        tree.column('ligand', width=400, anchor='w')
        tree.column('affinity', width=150, anchor=tk.CENTER)
        tree.column('engine', width=120, anchor=tk.CENTER)
        
        # Populate data
        for result in summary_results:
            affinity = result.get('Best Affinity (kcal/mol)', 'N/A')
            if isinstance(affinity, (int, float)):
                affinity = f"{affinity:.2f}"
            
            tree.insert('', tk.END, values=(
                result['Ligand'],
                affinity,
                result.get('Engine', 'Vina')
            ))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Show buttons
        self._show_buttons()
    
    def _clear_results(self):
        """Clear the results display."""
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # Hide buttons
        self.button_frame.pack_forget()
    
    def _show_message(self, message: str):
        """Show a message in the results area."""
        label = ctk.CTkLabel(
            self.results_frame,
            text=message,
            font=ctk.CTkFont(size=14)
        )
        label.pack(expand=True)
    
    def _show_buttons(self):
        """Show action buttons."""
        self.button_frame.pack(fill="x", pady=(10, 0))
        self.visualize_button.pack(side="left", padx=5)
        self.save_button.pack(side="left", padx=5)
    
    def _save_results(self):
        """Save results to file."""
        if not self.app.last_results and not self.app.batch_results_summary:
            messagebox.showwarning("Warning", "No results to save.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Results As",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    if self.app.last_run_type == 'single' and self.app.last_results:
                        # Save single results
                        writer.writerow(['Mode', 'Affinity (kcal/mol)', 'RMSD L.B.', 'RMSD U.B.', 'Engine'])
                        for result in self.app.last_results:
                            writer.writerow([
                                result.get('Mode', ''),
                                result.get('Affinity (kcal/mol)', ''),
                                result.get('RMSD L.B.', ''),
                                result.get('RMSD U.B.', ''),
                                result.get('Engine', 'Vina')
                            ])
                    
                    elif self.app.last_run_type == 'batch' and self.app.batch_results_summary:
                        # Save batch results
                        writer.writerow(['Ligand', 'Best Affinity (kcal/mol)', 'Engine'])
                        for result in self.app.batch_results_summary:
                            writer.writerow([
                                result['Ligand'],
                                result.get('Best Affinity (kcal/mol)', ''),
                                result.get('Engine', 'Vina')
                            ])
                
                messagebox.showinfo("Success", f"Results saved to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save results: {e}")


class VisualizationTab:
    """Visualization tab component."""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the visualization tab UI."""
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Results Visualization",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 10))
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Initial message
        self.initial_label = ctk.CTkLabel(
            content_frame,
            text="Visualization options will appear here after docking.\n\n"
                 "You can visualize single docking results or browse batch results.",
            font=ctk.CTkFont(size=14),
            justify="left"
        )
        self.initial_label.pack(expand=True)
        
        # Visualization controls (initially hidden)
        self.controls_frame = ctk.CTkFrame(content_frame)
        
        # Batch results list
        self.batch_frame = ctk.CTkFrame(content_frame)
        
        self.batch_label = ctk.CTkLabel(
            self.batch_frame,
            text="Batch Results:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        
        self.batch_listbox = tk.Listbox(
            self.batch_frame,
            height=10,
            bg='#343638',
            fg='white',
            selectbackground='#3b8ed0',
            selectforeground='white'
        )
        
        self.visualize_batch_button = ctk.CTkButton(
            self.batch_frame,
            text="Visualize Selected",
            command=self._visualize_selected_batch,
            width=120
        )
    
    def visualize_single_results(self, receptor_path: str, results_path: str, viewer: str = "ChimeraX"):
        """Visualize single docking results."""
        self._clear_visualization()
        
        try:
            info_text = f"""Ready to visualize results with {viewer}:

Receptor: {os.path.basename(receptor_path)}
Results: {os.path.basename(results_path)}

Click the button below to launch the visualization."""

            info_label = ctk.CTkLabel(
                self.controls_frame,
                text=info_text,
                font=ctk.CTkFont(size=12),
                justify="left"
            )
            info_label.pack(padx=10, pady=10, anchor="w")
            
            # Launch visualization button
            ctk.CTkButton(
                self.controls_frame,
                text=f"Launch {viewer}",
                command=lambda: self._launch_visualization(receptor_path, results_path, viewer),
                width=120,
                fg_color="#2aa876",
                hover_color="#228c61"
            ).pack(pady=10)
            
            self.controls_frame.pack(fill="both", expand=True)
            
        except Exception as e:
            messagebox.showerror("Visualization Error", f"Failed to setup visualization: {e}")
    
    def _launch_visualization(self, receptor_path: str, results_path: str, viewer: str):
        """Launch external visualization tool."""
        try:
            if viewer == "VMD":
                self._launch_vmd(receptor_path, results_path)
            elif viewer == "ChimeraX":
                self._launch_chimerax(receptor_path, results_path)
            else:
                messagebox.showerror("Error", f"Unsupported viewer: {viewer}")
                
        except Exception as e:
            messagebox.showerror("Visualization Error", f"Failed to launch {viewer}: {e}")
    
    def _launch_vmd(self, receptor_path: str, results_path: str):
        """Launch VMD with receptor and results."""
        try:
            from utils.config import get_config_manager
            config_manager = get_config_manager()
            vmd_path = config_manager.get_executable_path("vmd")
            
            # Create a temporary script for VMD
            temp_dir = self.app.file_manager.create_temp_directory()
            script_path = os.path.join(temp_dir, "vmd_script.tcl")
            
            # Create VMD script
            script_content = f"""
# Load receptor
mol new "{receptor_path}" type pdbqt
# Load docked poses
mol new "{results_path}" type pdbqt

# Style settings
mol modstyle 0 0 NewCartoon
mol modcolor 0 0 Chain
mol modstyle 1 0 Licorice
mol modcolor 1 0 ColorID 1

# Zoom to see everything
scale by 1.2
"""
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Launch VMD
            cmd = [vmd_path, "-e", script_path]
            subprocess.Popen(cmd)
            messagebox.showinfo("Success", f"VMD launched with receptor and results!")
            
        except Exception as e:
            messagebox.showerror("VMD Error", f"Failed to launch VMD: {e}\n\nMake sure VMD is installed and configured in settings.")
    
    def _launch_chimerax(self, receptor_path: str, results_path: str):
        """Launch ChimeraX with receptor and results."""
        try:
            from utils.config import get_config_manager
            config_manager = get_config_manager()
            chimerax_path = config_manager.get_executable_path("chimerax")
            
            # Create a temporary script for ChimeraX
            temp_dir = self.app.file_manager.create_temp_directory()
            script_path = os.path.join(temp_dir, "chimerax_script.cxc")
            
            # Create ChimeraX script
            script_content = f"""
# Open receptor and results
open "{receptor_path}"
open "{results_path}"

# Style settings
cartoon
color bychain
style ligand ball
color ligand red

# View settings
view
"""
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Launch ChimeraX
            cmd = [chimerax_path, "--script", script_path]
            subprocess.Popen(cmd)
            messagebox.showinfo("Success", f"ChimeraX launched with receptor and results!")
            
        except Exception as e:
            messagebox.showerror("ChimeraX Error", f"Failed to launch ChimeraX: {e}\n\nMake sure ChimeraX is installed and configured in settings.")
    
    def _clear_visualization(self):
        """Clear visualization area."""
        self.initial_label.pack_forget()
        self.controls_frame.pack_forget()
        self.batch_frame.pack_forget()
        
        for widget in self.controls_frame.winfo_children():
            widget.destroy()
        
        for widget in self.batch_frame.winfo_children():
            widget.destroy()
    
    def show_batch_visualization(self, results_summary: List[Dict]):
        """Show batch visualization options."""
        self._clear_visualization()
        
        if not results_summary:
            self._show_message("No batch results to visualize.")
            return
        
        self.batch_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Populate batch list
        for result in results_summary:
            self.batch_listbox.insert(tk.END, result['Ligand'])
        
        # Add scrollbar
        list_container = ctk.CTkFrame(self.batch_frame)
        list_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(list_container, orient="vertical")
        self.batch_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.batch_listbox.yview)
        
        self.batch_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.visualize_batch_button.pack(pady=10)
        
        self.batch_frame.pack(fill="both", expand=True)
    
    def _visualize_selected_batch(self):
        """Visualize selected batch result."""
        selection = self.batch_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a ligand to visualize.")
            return
        
        ligand_name = self.batch_listbox.get(selection[0])
        
        # Find the corresponding result file
        result_file = None
        for result in self.app.batch_results_summary:
            if result['Ligand'] == ligand_name and result.get('OutputFile'):
                result_file = result['OutputFile']
                break
        
        if result_file and os.path.exists(result_file) and self.app.receptor_pdbqt_path:
            self._launch_visualization(self.app.receptor_pdbqt_path, result_file, self.app.viewer_choice.get())
        else:
            messagebox.showerror("Error", f"Could not find result file for {ligand_name}")
    
    def _show_message(self, message: str):
        """Show a message in the visualization area."""
        label = ctk.CTkLabel(
            self.controls_frame,
            text=message,
            font=ctk.CTkFont(size=14)
        )
        label.pack(expand=True)
        self.controls_frame.pack(fill="both", expand=True)