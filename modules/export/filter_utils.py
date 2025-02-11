import tkinter as tk
import customtkinter as ctk

class FilterDialog(ctk.CTkToplevel):
    def __init__(self, parent, categories, callback):
        super().__init__(parent)
        
        self.title("Step 1: Select Classes to Keep")
        self.geometry("500x600")
        self.attributes('-topmost', True)
        
        self.categories = categories
        self.callback = callback
        self.filtered_categories = set(categories.keys())
        
        self.create_ui()
        
    def create_ui(self):
        # Main scrollable frame
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Instructions
        ctk.CTkLabel(
            main_frame,
            text="Select the classes you want to keep in the exported annotations.",
            wraplength=450
        ).pack(pady=(0, 10))
        
        # Header frame with title and select/deselect buttons
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(header_frame, text="Available Classes", font=("", 16, "bold")).pack(side="left", padx=5)
        
        # Select/Deselect All buttons
        buttons_frame = ctk.CTkFrame(header_frame)
        buttons_frame.pack(side="right", padx=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="Select All",
            command=self.select_all,
            width=100
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            buttons_frame,
            text="Deselect All",
            command=self.deselect_all,
            width=100
        ).pack(side="left", padx=2)
        
        # Checkboxes for categories
        self.filter_vars = {}
        for cat_id, cat_info in self.categories.items():
            var = tk.BooleanVar(value=True)
            self.filter_vars[cat_id] = var
            
            checkbox = ctk.CTkCheckBox(
                main_frame,
                text=f"{cat_info['name']} (ID: {cat_id})",
                variable=var,
                command=self.update_filtered_categories
            )
            checkbox.pack(pady=2, anchor="w")
        
        # Bottom buttons frame (outside scrollable area)
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame,
            text="Next: Merge Classes",
            command=self.next_step
        ).pack(pady=5)
        
    def select_all(self):
        for var in self.filter_vars.values():
            var.set(True)
        self.update_filtered_categories()
    
    def deselect_all(self):
        for var in self.filter_vars.values():
            var.set(False)
        self.update_filtered_categories()
        
    def update_filtered_categories(self):
        self.filtered_categories = {
            cat_id for cat_id, var in self.filter_vars.items()
            if var.get()
        }
        
    def next_step(self):
        if not self.filtered_categories:
            # Show warning if no categories selected
            warning = ctk.CTkToplevel(self)
            warning.title("Warning")
            warning.geometry("300x150")
            warning.attributes('-topmost', True)
            warning.grab_set()
            
            ctk.CTkLabel(
                warning,
                text="Please select at least one category to continue.",
                wraplength=250
            ).pack(pady=20)
            
            ctk.CTkButton(
                warning,
                text="OK",
                command=warning.destroy
            ).pack(pady=10)
            
            return
            
        self.callback(self.filtered_categories)
        self.destroy()