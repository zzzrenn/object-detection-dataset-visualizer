import customtkinter as ctk
import tkinter as tk

class MergeGroupFrame(ctk.CTkFrame):
    def __init__(self, parent, categories, categories_available, on_remove):
        super().__init__(parent)
        self.categories = categories
        self.categories_available = categories_available
        self.on_remove = on_remove
        self.is_confirmed = False
        self.selected_categories = set()
        
        self.create_ui()
        
    def create_ui(self):
        # New category name entry
        self.name_frame = ctk.CTkFrame(self)
        self.name_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(self.name_frame, text="New Class Name:").pack(side="left", padx=5)
        self.name_entry = ctk.CTkEntry(self.name_frame)
        self.name_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Selection frame for checkboxes
        self.selection_frame = ctk.CTkFrame(self)
        self.selection_frame.pack(fill="x", pady=2)
        
        # Add Select/Deselect All buttons
        self.buttons_frame = ctk.CTkFrame(self.selection_frame)
        self.buttons_frame.pack(fill="x", pady=2)
        
        self.category_vars = {}
        
        ctk.CTkButton(
            self.buttons_frame,
            text="Select All",
            command=self.select_all,
            width=100
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            self.buttons_frame,
            text="Deselect All",
            command=self.deselect_all,
            width=100
        ).pack(side="left", padx=2)
        
        # Category checkboxes
        self.checkbox_frame = ctk.CTkFrame(self.selection_frame)
        self.checkbox_frame.pack(fill="x")
        
        for cat_id, cat_info in self.categories.items():
            if not self.categories_available[cat_id]:
                continue
            var = tk.BooleanVar(value=False)
            self.category_vars[cat_id] = var
            
            checkbox = ctk.CTkCheckBox(
                self.checkbox_frame,
                text=f"{cat_info['name']} (ID: {cat_id})",
                variable=var
            )
            checkbox.pack(pady=2, anchor="w")
        
        # Bottom buttons frame
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.pack(fill="x", pady=5)
        
        # Confirm button
        self.confirm_button = ctk.CTkButton(
            self.control_frame,
            text="Confirm Selection",
            command=self.confirm_selection
        )
        self.confirm_button.pack(side="left", padx=5)
        
        # Edit button (initially hidden)
        self.edit_button = ctk.CTkButton(
            self.control_frame,
            text="Edit",
            command=self.edit_selection
        )
        
        # Remove button
        ctk.CTkButton(
            self.control_frame,
            text="Remove Group",
            command=lambda: self.on_remove(self)
        ).pack(side="right", padx=5)
        
    def select_all(self):
        for var in self.category_vars.values():
            var.set(True)
    
    def deselect_all(self):
        for var in self.category_vars.values():
            var.set(False)
            
    def confirm_selection(self):
        if not self.name_entry.get().strip():
            self.show_warning("Please enter a name for the merged class.")
            return
            
        selected = [cat_id for cat_id, var in self.category_vars.items() if var.get()]
            
        self.selected_categories = selected
        self.is_confirmed = True
        
        # Hide checkbox frame and show summary
        self.checkbox_frame.pack_forget()
        self.buttons_frame.pack_forget()
        
        # Create and show summary frame
        self.summary_frame = ctk.CTkFrame(self.selection_frame)
        self.summary_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            self.summary_frame,
            text="Selected Classes:",
            font=("", 12, "bold")
        ).pack(anchor="w", padx=5)
        
        for cat_id in selected:
            self.categories_available[cat_id] = False
            cat_name = self.categories[cat_id]['name']
            ctk.CTkLabel(
                self.summary_frame,
                text=f"• {cat_name} (ID: {cat_id})"
            ).pack(anchor="w", padx=20)
        
        # Update buttons
        self.confirm_button.pack_forget()
        self.edit_button.pack(side="left", padx=5)
        
    def edit_selection(self):
        # Remove summary frame
        self.summary_frame.destroy()
        
        # Show checkbox frame again
        self.buttons_frame.pack(fill="x", pady=2)
        self.checkbox_frame.pack(fill="x")
        
        # Update buttons
        self.edit_button.pack_forget()
        self.confirm_button.pack(side="left", padx=5)
        
        self.is_confirmed = False
        
    def show_warning(self, message):
        warning = ctk.CTkToplevel(self)
        warning.title("Warning")
        warning.geometry("300x150")
        warning.attributes('-topmost', True)
        warning.grab_set()
        
        ctk.CTkLabel(
            warning,
            text=message,
            wraplength=250
        ).pack(pady=20)
        
        ctk.CTkButton(
            warning,
            text="OK",
            command=warning.destroy
        ).pack(pady=10)
        
    def get_merge_info(self):
        if not self.is_confirmed:
            return None
        return {
            'new_name': self.name_entry.get().strip(),
            'categories': self.selected_categories
        }

class MergeDialog(ctk.CTkToplevel):
    def __init__(self, parent, categories, filtered_categories, callback):
        super().__init__(parent)
        
        self.title("Step 2: Merge Classes")
        self.geometry("500x600")
        
        self.categories = {k: v for k, v in categories.items() if k in filtered_categories}
        self.categories_available = {k:True for k in categories.keys()}
        self.callback = callback
        self.merge_groups = []
        
        self.create_ui()
        
    def create_ui(self):
        # Main scrollable frame
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Instructions
        ctk.CTkLabel(
            main_frame,
            text="Optionally create groups of classes to merge. Each group will become a new class in the exported annotations.",
            wraplength=450
        ).pack(pady=(0, 10))
        
        # Merge groups section
        ctk.CTkLabel(main_frame, text="Merge Groups", font=("", 16, "bold")).pack(pady=5)
        
        # Add merge group button
        ctk.CTkButton(
            main_frame,
            text="Add Merge Group",
            command=self.add_merge_group
        ).pack(pady=5)
        
        # Container for merge groups
        self.groups_container = ctk.CTkFrame(main_frame)
        self.groups_container.pack(fill="x", expand=True)
        
        # Bottom buttons frame (outside scrollable area)
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame,
            text="Export",
            command=self.export
        ).pack(pady=5)
        
    def add_merge_group(self):
        group_frame = MergeGroupFrame(
            self.groups_container,
            self.categories,
            self.categories_available,
            self.remove_merge_group
        )
        group_frame.pack(fill="x", pady=5)
        self.merge_groups.append(group_frame)
        self.categories_available = group_frame.categories_available
        
    def remove_merge_group(self, group_frame):
        self.merge_groups.remove(group_frame)
        group_frame.destroy()
        
    def export(self):
        merge_groups = []
        for group in self.merge_groups:
            merge_info = group.get_merge_info()
            if merge_info:
                merge_groups.append(merge_info)
        
        self.callback(merge_groups)
        self.destroy()