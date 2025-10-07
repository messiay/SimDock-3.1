import os
import tkinter as tk
from tkinter import ttk, messagebox
import csv
from typing import List, Dict
import customtkinter as ctk


class AdvancedSettingsDialog:
    """Dialog for advanced docking settings."""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.dialog = None
        
    def show(self):
        """Show the advanced settings dialog."""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Advanced Settings")
        self.dialog.geometry("500x400")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Viewer selection
        viewer_frame = ctk.CTkFrame(main_frame)
        viewer_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(viewer_frame, text="Default Viewer:").pack(side="left", padx=(0, 10))
        viewer_selector = ctk.CTkComboBox(viewer_frame, 
                                        values=["VMD", "ChimeraX"], 
                                        variable=self.app.viewer_choice,
                                        state="readonly")
        viewer_selector.pack(fill="x", expand=True)
        
        # Coordinate entries
        coord_frame = ctk.CTkFrame(main_frame)
        coord_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(coord_frame, text="Docking Box Center (Å):").pack(anchor="w")
        center_frame = ctk.CTkFrame(coord_frame, fg_color="transparent")
        center_frame.pack(fill="x", pady=5)
        
        ctk.CTkEntry(center_frame, textvariable=self.app.center_x, width=80).pack(side="left", padx=2)
        ctk.CTkEntry(center_frame, textvariable=self.app.center_y, width=80).pack(side="left", padx=2)
        ctk.CTkEntry(center_frame, textvariable=self.app.center_z, width=80).pack(side="left", padx=2)
        
        ctk.CTkLabel(coord_frame, text="Docking Box Size (Å):").pack(anchor="w", pady=(10, 0))
        size_frame = ctk.CTkFrame(coord_frame, fg_color="transparent")
        size_frame.pack(fill="x", pady=5)
        
        ctk.CTkEntry(size_frame, textvariable=self.app.size_x, width=80).pack(side="left", padx=2)
        ctk.CTkEntry(size_frame, textvariable=self.app.size_y, width=80).pack(side="left", padx=2)
        ctk.CTkEntry(size_frame, textvariable=self.app.size_z, width=80).pack(side="left", padx=2)
        
        # Exhaustiveness settings
        adaptive_frame = ctk.CTkFrame(main_frame)
        adaptive_frame.pack(fill="x", pady=10)
        
        exh_frame = ctk.CTkFrame(adaptive_frame, fg_color="transparent")
        exh_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(exh_frame, text="Exhaustiveness:").pack(side="left")
        exh_entry = ctk.CTkEntry(exh_frame, textvariable=self.app.exhaustiveness, width=60)
        exh_entry.pack(side="right")
        
        def toggle_adaptive():
            state = "disabled" if self.app.use_adaptive_exhaustiveness.get() else "normal"
            exh_entry.configure(state=state)
            if self.app.use_adaptive_exhaustiveness.get():
                self.app.use_hierarchical_docking.set(False)

        adaptive_check = ctk.CTkCheckBox(adaptive_frame, 
                                       text="Use Adaptive Exhaustiveness", 
                                       variable=self.app.use_adaptive_exhaustiveness,
                                       command=toggle_adaptive)
        adaptive_check.pack(anchor="w", pady=5)
        
        separator = ctk.CTkFrame(main_frame, height=2, fg_color="gray")
        separator.pack(fill="x", pady=10)
        
        # Hierarchical docking settings
        hierarchical_frame = ctk.CTkFrame(main_frame)
        hierarchical_frame.pack(fill="x", pady=10)
        
        refine_frame = ctk.CTkFrame(hierarchical_frame, fg_color="transparent")
        refine_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(refine_frame, text="Refine top [%]:").pack(side="left")
        refine_entry = ctk.CTkEntry(refine_frame, textvariable=self.app.refine_percentage, width=60)
        refine_entry.pack(side="right")
        
        def toggle_hierarchical():
            is_batch = len(self.app.ligand_library) > 1
            state = "normal" if self.app.use_hierarchical_docking.get() and is_batch else "disabled"
            refine_entry.configure(state=state)
            if self.app.use_hierarchical_docking.get():
                self.app.use_adaptive_exhaustiveness.set(False)
                toggle_adaptive()

        hierarchical_check = ctk.CTkCheckBox(hierarchical_frame, 
                                           text="Use Hierarchical Docking (Batch Only)", 
                                           variable=self.app.use_hierarchical_docking,
                                           command=toggle_hierarchical)
        hierarchical_check.pack(anchor="w", pady=5)
        
        # Initialize states
        toggle_adaptive()
        toggle_hierarchical()
        if len(self.app.ligand_library) <= 1:
            hierarchical_check.configure(state="disabled")

        ctk.CTkButton(main_frame, text="Close", command=self.dialog.destroy).pack(pady=(15,0))


class ResultsDialog:
    """Dialog for displaying single docking results."""
    
    def __init__(self, parent, results: List[Dict], save_callback: callable):
        self.parent = parent
        self.results = results
        self.save_callback = save_callback
        self.dialog = None
        
    def show(self):
        """Show the results dialog."""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Docking Results")
        self.dialog.geometry("600x400")
        
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create results table
        tree_frame = ctk.CTkFrame(main_frame)
        tree_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        from tkinter import ttk
        
        columns = ('mode', 'affinity', 'rmsd_lb', 'rmsd_ub', 'engine')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        # Configure columns
        tree.heading('mode', text='Mode')
        tree.heading('affinity', text='Affinity (kcal/mol)')
        tree.heading('rmsd_lb', text='RMSD L.B.')
        tree.heading('rmsd_ub', text='RMSD U.B.')
        tree.heading('engine', text='Engine')
        
        tree.column('mode', width=60, anchor=tk.CENTER)
        tree.column('affinity', width=120, anchor=tk.CENTER)
        tree.column('rmsd_lb', width=100, anchor=tk.CENTER)
        tree.column('rmsd_ub', width=100, anchor=tk.CENTER)
        tree.column('engine', width=120, anchor=tk.CENTER)
        
        # Populate data
        for score in self.results:
            tree.insert('', tk.END, values=(
                score.get('Mode', ''),
                score.get('Affinity (kcal/mol)', ''),
                score.get('RMSD L.B.', ''),
                score.get('RMSD U.B.', ''),
                score.get('Engine', '')
            ))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        ctk.CTkButton(button_frame, text="Save Results...", 
                     command=self.save_callback).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Close", 
                     command=self.dialog.destroy).pack(side="right")
        
        self.dialog.transient(self.parent)
        self.dialog.grab_set()


class BatchResultsDialog:
    """Dialog for displaying batch docking results."""
    
    def __init__(self, parent, results_summary: List[Dict], full_results: List[Dict], 
                 visualize_callback: callable, save_callback: callable):
        self.parent = parent
        self.results_summary = results_summary
        self.full_results = full_results
        self.visualize_callback = visualize_callback
        self.save_callback = save_callback
        self.dialog = None
        self.tree = None
        
    def show(self):
        """Show the batch results dialog."""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Batch Docking Results")
        self.dialog.geometry("700x500")
        
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create results table
        tree_frame = ctk.CTkFrame(main_frame)
        tree_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        from tkinter import ttk
        
        columns = ('ligand', 'affinity', 'engine')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        self.tree.heading('ligand', text='Ligand')
        self.tree.heading('affinity', text='Best Affinity (kcal/mol)')
        self.tree.heading('engine', text='Engine')
        
        self.tree.column('ligand', anchor='w', width=400)
        self.tree.column('affinity', anchor='center', width=150)
        self.tree.column('engine', anchor='center', width=120)
        
        # Populate data
        for result in self.results_summary:
            self.tree.insert('', tk.END, values=(
                result['Ligand'], 
                result['Best Affinity (kcal/mol)'],
                result.get('Engine', '')
            ))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        ctk.CTkButton(button_frame, text="Visualize Selected Pose", 
                     command=self._visualize_selected).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Save Full Results...", 
                     command=self.save_callback).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Close", 
                     command=self.dialog.destroy).pack(side="right", padx=5)
        
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
    
    def _visualize_selected(self):
        """Visualize selected ligand pose."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a ligand from the list to visualize.")
            return
        
        item = self.tree.item(selected_item[0])
        filename = item['values'][0]
        self.visualize_callback(filename)