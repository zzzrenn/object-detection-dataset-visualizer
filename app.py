import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import json
import os
import threading
from collections import defaultdict
from modules.export import FilterDialog, MergeDialog

class ObjectDetectionViewer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Object Detection Dataset Viewer")
        self.geometry("1400x800")

        # Initialize variables
        self.current_image_index = 0
        self.images = []
        self.annotations = []
        self.categories = {}  # {id: {name: str, count: int}}
        self.image_annotations = defaultdict(list)  # {image_id: [annotations]}
        self._current_image = None # original image
        self.current_image = None # resized image
        self.photo_image = None
        self.resize_factor = 1.0
        self.zoom_factor = 1.0
        self.class_checkboxes = {}
        self.visible_classes = set()
        self.selected_box = None
        self.loaded_dataset = False
        self.loaded_current_image = False
        self._image_min_height = 720
        self._image_min_width = 1280
        self.hovered_box = None  # Track the currently hovered box
        self.metadata_popup = None

        # Add threading lock for popup operations
        self.popup_lock = threading.Lock()

        # dataset info
        self.dataset_format_options = ["COCO"]
        self.image_path = None
        self.annotation_path = None

        # Add panning variables
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.is_panning = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create main layout
        self.grid_columnconfigure(1, weight=1)  # Canvas column
        self.grid_rowconfigure(2, weight=1)     # Main content row

        # Create menu bar
        self.create_menu()
        
        # Create canvas for image display
        self.canvas_frame = ctk.CTkFrame(self)
        self.canvas_frame.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)
        self.canvas_frame.grid_columnconfigure(1, weight=1)
        self.canvas_frame.grid_rowconfigure(2, weight=1)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg='gray20', highlightthickness=0)
        self.canvas.grid(row=2, column=1, sticky="nsew")
        
        # Create right sidebar for class checkboxes
        self.sidebar = ctk.CTkScrollableFrame(self, width=250)
        self.sidebar.grid(row=2, column=3, sticky="nsew", padx=10, pady=10)
        
        # Bind events
        self.bind('<Left>', self.prev_image)
        self.bind('<Right>', self.next_image)
        self.canvas.bind('<Motion>', self.on_canvas_motion)  # Bind motion event
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)

        # Add pan bindings
        self.canvas.bind('<ButtonPress-1>', self.start_pan)
        self.canvas.bind('<B1-Motion>', self.pan)
        self.canvas.bind('<ButtonRelease-1>', self.stop_pan)


    # Menu functions
    def create_menu(self):
        # Main load frame with dataset loading options
        self.load_frame = ctk.CTkFrame(self)
        self.load_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
        
        # Dataset format dropdown
        ctk.CTkLabel(self.load_frame, text="Format:").grid(row=0, column=0, padx=5, pady=5)
        dataset_format_dd = ctk.CTkOptionMenu(
            self.load_frame,
            values=self.dataset_format_options,
            width=100
        )
        dataset_format_dd.grid(row=0, column=1, padx=5, pady=5)

        # Image folder selection
        ctk.CTkLabel(self.load_frame, text="Images:").grid(row=0, column=2, padx=5, pady=5)
        image_folder_btn = ctk.CTkButton(
            self.load_frame,
            text="Select Folder",
            width=100,
            command=self.select_image_directory
        )
        image_folder_btn.grid(row=0, column=3, padx=5, pady=5)

        # Image path entry
        self.image_path_entry = ctk.CTkEntry(
            self.load_frame, 
            placeholder_text="No folder selected",
            width=300,
            state="readonly"
        )
        self.image_path_entry.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

        # Annotation file selection
        ctk.CTkLabel(self.load_frame, text="Annotations:").grid(row=0, column=5, padx=5, pady=5)
        annotation_folder_btn = ctk.CTkButton(
            self.load_frame,
            text="Select File",
            width=100,
            command=self.select_annotation
        )
        annotation_folder_btn.grid(row=0, column=6, padx=5, pady=5)

        # Annotation path entry
        self.annotation_path_entry = ctk.CTkEntry(
            self.load_frame, 
            placeholder_text="No annotation file selected",
            width=300,
            state="readonly"
        )
        self.annotation_path_entry.grid(row=0, column=7, padx=5, pady=5, sticky="ew")

        # Load dataset button
        self.load_btn = ctk.CTkButton(
            self.load_frame, 
            text="Load Dataset", 
            width=100,
            command=self.load_dataset,
            state="disabled"
        )
        self.load_btn.grid(row=0, column=8, padx=5, pady=5)

        # Save and export frame
        self.save_frame = ctk.CTkFrame(self)
        self.save_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=5, pady=5)

        # Save current image button
        self.save_btn = ctk.CTkButton(
            self.save_frame, 
            text="Save Current Image", 
            command=self.save_current_image
        )
        self.save_btn.pack(side="left", padx=5)
        
        # Export button
        self.export_btn = ctk.CTkButton(
            self.save_frame, 
            text="Export COCO Annotations", 
            command=self.export_annotations
        )
        self.export_btn.pack(side="left", padx=5)

        # Configure column weights for responsive layout
        self.load_frame.grid_columnconfigure(4, weight=1)
        self.load_frame.grid_columnconfigure(7, weight=1)   

    # Dataset loading functions
    def select_image_directory(self):
        self.image_path = tk.filedialog.askdirectory(
            title="Select image folder"
        )
        if self.image_path:
            # Update the entry with the selected path
            self.image_path_entry.configure(state="normal")
            self.image_path_entry.delete(0, tk.END)
            self.image_path_entry.insert(0, self.image_path)
            self.image_path_entry.configure(state="readonly")

        if self.image_path and self.annotation_path:
            self.load_btn.configure(state="normal")
        
    def select_annotation(self):
        self.annotation_path = tk.filedialog.askopenfilename(
            title="Select COCO annotation file",
            filetypes=[("JSON files", "*.json")]
        )
        if self.annotation_path:
            # Update the entry with the selected path
            self.annotation_path_entry.configure(state="normal")
            self.annotation_path_entry.delete(0, tk.END)
            self.annotation_path_entry.insert(0, self.annotation_path)
            self.annotation_path_entry.configure(state="readonly")
        
        if self.image_path and self.annotation_path:
            self.load_btn.configure(state="normal")
    
    def set_dataset_button_state(self, state):
        # Enable and disable buttons related to dataset
        self.load_btn.configure(state=state)
        self.save_btn.configure(state=state)
        self.export_btn.configure(state=state)

    def load_dataset(self):     
        try:
            assert self.image_path, "Missing image folder path!"
            assert self.annotation_path, "Missing annotation file path!"
                
            # Load COCO format annotations
            with open(self.annotation_path, 'r') as f:
                coco_data = json.load(f)
                
            # Process categories
            self.categories = {
                cat['id']: {'name': cat['name'], 'count': 0} 
                for cat in coco_data['categories']
            }
            
            # Process images
            self.images = {
                img['id']: {
                    'file_name': img['file_name'],
                    'width': img['width'],
                    'height': img['height']
                }
                for img in coco_data['images']
            }
            
            # Process annotations
            self.image_annotations.clear()
            for ann in coco_data['annotations']:
                self.image_annotations[ann['image_id']].append({
                    'category_id': ann['category_id'],
                    'bbox': ann['bbox'],  # [x, y, width, height]
                    'score': ann.get('score', 1.0),
                    'id': ann['id']
                })
                
            # Loaded dataset
            self.loaded_dataset = True

            # Reset loaded image
            self.loaded_current_image = False

            # Set image list for navigation
            self.image_list = list(self.images.keys())
            self.current_image_index = 0
            
            # Update UI
            self.load_current_image()
        except Exception as e:
            # Failed to load dataset
            self.loaded_dataset = False
            self.loaded_current_image = False

            # Create error popup
            error_popup = ctk.CTkToplevel(self)
            error_popup.title("Dataset Loading Error")
            error_popup.geometry("400x200")
            error_popup.attributes('-topmost', True)  # Keep window on top
            error_popup.grab_set()  # Prevent interaction with main window until popup is closed
            
            # Error message label
            ctk.CTkLabel(
                error_popup, 
                text=f"Error loading dataset:\n\n{str(e)}",
                wraplength=350
            ).pack(pady=20, padx=20)
            
            # OK button to close popup
            ctk.CTkButton(
                error_popup, 
                text="OK", 
                command=error_popup.destroy
            ).pack(pady=10)
        
    def update_class_checkboxes(self):
        # Clear existing checkboxes
        for widget in self.sidebar.winfo_children():
            widget.destroy()
        
        # Get current image annotations
        current_image_id = self.image_list[self.current_image_index]
        current_anns = self.image_annotations[current_image_id]
        
        # Count annotations per class for current image
        class_counts = defaultdict(int)
        for ann in current_anns:
            class_counts[ann['category_id']] += 1
        
        # Create new checkboxes
        for cat_id, cat_info in self.categories.items():
            count = class_counts[cat_id]
            if count == 0:
                continue
            var = tk.BooleanVar(value=count > 0)
            
            checkbox = ctk.CTkCheckBox(
                self.sidebar,
                text=f"{cat_info['name']} ({count})",
                text_color=self.get_color(cat_id),
                variable=var,
                command=lambda cid=cat_id: self.toggle_class_visibility(cid),
                state="normal" if count > 0 else "disabled"
            )
            checkbox.pack(pady=2, anchor="w")
            self.class_checkboxes[cat_id] = var
            
            if count > 0:
                self.visible_classes.add(cat_id)
            else:
                self.visible_classes.discard(cat_id)
    
    def toggle_class_visibility(self, class_idx):
        if self.class_checkboxes[class_idx].get():
            self.visible_classes.add(class_idx)
        else:
            self.visible_classes.remove(class_idx)
        self.draw_image_and_annotations()
        
    def draw_image_and_annotations(self):
        if not self.current_image:
            return
            
        # Clear canvas
        self.canvas.delete("all")
        
        # Calculate center position with pan offset
        cx = self.canvas.winfo_width()//2 - self.current_image.width//2 + self.pan_offset_x
        cy = self.canvas.winfo_height()//2 - self.current_image.height//2 + self.pan_offset_y
        
        # Draw image
        self.canvas.create_image(
            cx + self.current_image.width//2,
            cy + self.current_image.height//2,
            image=self.photo_image,
            anchor="center"
        )
        
        # Draw annotations
        if self.image_list:
            current_image_id = self.image_list[self.current_image_index]
            current_anns = self.image_annotations[current_image_id]
            
            for ann in current_anns:
                if ann['category_id'] not in self.visible_classes:
                    continue
                    
                # Convert COCO bbox [x, y, width, height] to [x1, y1, x2, y2]
                x, y, w, h = ann['bbox']
                x1, y1 = x * self.zoom_factor * self.resize_factor, y * self.zoom_factor * self.resize_factor
                x2, y2 = (x + w) * self.zoom_factor * self.resize_factor, (y + h) * self.zoom_factor * self.resize_factor
                
                # Create unique tag for this box
                box_tag = f"box_{ann['category_id']}_{ann['id']}"
                
                # Draw box with pan offset
                self.canvas.create_rectangle(
                    x1 + cx, y1 + cy, x2 + cx, y2 + cy,
                    outline=self.get_color(ann['category_id']),
                    width=2,
                    tags=("box", box_tag)                
                )
                
                # Draw label with pan offset
                category_name = self.categories[ann['category_id']]['name']
                self.canvas.create_text(
                    x1 + cx, y1 + cy - 5,
                    text=f"{category_name} ({ann['category_id']})",
                    fill=self.get_color(ann['category_id']),
                    anchor="sw",
                    tags=("box", box_tag)
                )

    def load_current_image(self):
        if not self.image_list:
            return
        
        # Load image if it is not yet loaded
        if not self.loaded_current_image:
            current_image_id = self.image_list[self.current_image_index]
            image_info = self.images[current_image_id]
            
            # Load image file
            image_path = os.path.join(self.image_path, image_info['file_name'])
            self._current_image = Image.open(image_path)

            # Resize the image to a minimum size
            w, h = self._current_image.size
            self.resize_factor = max(1.0 , min(self._image_min_height / h, self._image_min_width / w))
            
            # Reset pan offset when loading new image
            self.reset_pan()
            
            # Set loaded current image
            self.loaded_current_image = True
            
        # Apply zoom
        new_size = tuple(int(dim * self.zoom_factor * self.resize_factor) for dim in self._current_image.size)
        self.current_image = self._current_image.resize(new_size)
        
        self.photo_image = ImageTk.PhotoImage(self.current_image)

        # Update class checkboxes
        self.update_class_checkboxes()
        
        # Draw image and annotations
        self.draw_image_and_annotations()
        

    # Metadata functions
    def hide_box_metadata(self):
        # Hide the metadata popup if it exists
        if self.metadata_popup is not None:
            self.metadata_popup.destroy()
            self.metadata_popup = None

    def show_box_metadata(self, box_tag):  
              
        _, category_id, ann_id = box_tag.split("_")
        category_id = int(category_id)
        ann_id = int(ann_id)
        
        # Find annotation
        current_image_id = self.image_list[self.current_image_index]
        ann = next(a for a in self.image_annotations[current_image_id] 
                  if a['id'] == ann_id)
        
        # Create popup window
        self.metadata_popup = ctk.CTkToplevel(self)
        self.metadata_popup.title("Box Metadata")
        self.metadata_popup.geometry("300x200")
        self.metadata_popup.attributes('-topmost', True)  # Keep window on top
        
        # Add metadata
        ctk.CTkLabel(self.metadata_popup, text=f"Category: {self.categories[category_id]['name']}").pack(pady=5)
        ctk.CTkLabel(self.metadata_popup, text=f"Bbox: {[round(x, 2) for x in ann['bbox']]}").pack(pady=5)
        ctk.CTkLabel(self.metadata_popup, text=f"Annotation ID: {ann_id}").pack(pady=5)
        
    # Event functions
    def next_image(self, event=None):
        if self.current_image_index < len(self.image_list) - 1:
            self.current_image_index += 1
            self.loaded_current_image = False
            self.reset_zoom_factor()
            self.reset_pan()
            self.load_current_image()
            
    def prev_image(self, event=None):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.loaded_current_image = False
            self.reset_zoom_factor()
            self.reset_pan()
            self.load_current_image()

    def on_mousewheel(self, event):
        if not self.loaded_dataset:
            return
        # Zoom in/out with mouse wheel
        if event.delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor *= 0.9
        self.load_current_image()

    def reset_zoom_factor(self):
        self.zoom_factor = 1.0

    def on_canvas_motion(self, event):
        if not self.loaded_dataset:
            return
        
        # Find hovered box
        hovered_items = self.canvas.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)
        hovered_box = None
        for item in hovered_items:
            tags = self.canvas.gettags(item)
            if "box" in tags:
                hovered_box = tags[1]
                break
        
        # If the hovered box has changed
        # Lock to avoid race condition, where the window is changed before destroy 
        # when mouse hovers rapidly across multipl boxes
        if self.popup_lock.acquire(False):
            if hovered_box != self.hovered_box:
                # Hide current metadata popup
                self.hide_box_metadata()
                self.hovered_box = hovered_box
                # Show new metadata popup if hovering over a box
                if hovered_box:
                    self.show_box_metadata(hovered_box)
            self.popup_lock.release()

    def start_pan(self, event):
        if not self.loaded_dataset:
            return
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def pan(self, event):
        if not self.is_panning:
            return
            
        # Calculate the distance moved
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        
        # Update the offset
        self.pan_offset_x += dx
        self.pan_offset_y += dy
        
        # Update start position for next movement
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        
        # Redraw the image and annotations
        self.draw_image_and_annotations()

    def stop_pan(self, event):
        self.is_panning = False

    def reset_pan(self):
        self.pan_offset_x = 0
        self.pan_offset_y = 0
    

    # Export functions
    def export_annotations(self):
        if not self.image_list:
            return
            
        def on_filter_complete(filtered_categories):
            def on_merge_complete(merge_groups):
                # Open file dialog
                filename = tk.filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json")]
                )
                
                if not filename:
                    return
                    
                # Create category mapping for merged categories
                category_mapping = {}
                old_categories = filtered_categories.copy()
                new_categories = {}
                next_category_id = 0
                
                # Add merged categories
                for group in merge_groups:
                    for old_cat_id in group['categories']:
                        category_mapping[old_cat_id] = next_category_id
                        # Remove old category if it's being merged
                        old_categories.remove(old_cat_id)
                    new_categories[next_category_id] = group['new_name']
                    next_category_id += 1

                # Filtered categories that are not merged
                for old_cat_id in old_categories:
                    category_mapping[old_cat_id] = next_category_id # continue with new category id
                    new_categories[next_category_id] = self.categories[old_cat_id]['name']
                    next_category_id += 1
                
                # Create COCO format data with merged and filtered categories
                export_data = {
                    'images': [
                        {
                            'id': img_id,
                            'file_name': img_info['file_name'],
                            'width': img_info['width'],
                            'height': img_info['height']
                        }
                        for img_id, img_info in self.images.items()
                    ],
                    'categories': [
                        {
                            'id': cat_id,
                            'name': cat_name
                        }
                        for cat_id, cat_name in new_categories.items()
                    ],
                    'annotations': [
                        {
                            'id': ann['id'], # should be changed to continuos id after filtering and merging
                            'image_id': img_id,
                            'category_id': category_mapping[ann['category_id']],
                            'bbox': ann['bbox'],
                            'score': ann['score']
                        }
                        for img_id, anns in self.image_annotations.items()
                        for ann in anns
                        if ann['category_id'] in category_mapping
                    ]
                }
                
                # Save to file
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
            
            # Show merge dialog after filtering
            merge_dialog = MergeDialog(self, self.categories, filtered_categories, on_merge_complete)
            merge_dialog.grab_set()
        
        # Show filter dialog first
        filter_dialog = FilterDialog(self, self.categories, on_filter_complete)
        filter_dialog.grab_set()

    def save_current_image(self):
        if not self.current_image:
            return
            
        # Open file dialog
        filename = tk.filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if not filename:
            return
            
        # Create new image with annotations
        img_draw = self._current_image.copy()
        draw = ImageDraw.Draw(img_draw)
        
        current_image_id = self.image_list[self.current_image_index]
        current_anns = self.image_annotations[current_image_id]
        
        for ann in current_anns:
            if ann['category_id'] not in self.visible_classes:
                continue
                
            x, y, w, h = ann['bbox']
            color = self.get_color(ann['category_id'])
            
            # Draw rectangle
            draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
            
            # Draw label
            category_name = self.categories[ann['category_id']]['name']
            draw.text((x, y - 10), f"{category_name} ({ann['category_id']})", fill=color)
            
        # Save image
        img_draw.save(filename)


    # Color functions
    def get_color(self, category_id):
        # Generate consistent color for each category
        colors = [
            "#FF3838",
            "#FF9D97",
            "#FF701F",
            "#FFB21D",
            "#CFD231",
            "#48F90A",
            "#92CC17",
            "#3DDB86",
            "#1A9334",
            "#00D4BB",
            "#2C99A8",
            "#00C2FF",
            "#344593",
            "#6473FF",
            "#0018EC",
            "#8438FF",
            "#520085",
            "#CB38FF",
            "#FF95C8",
            "#FF37C7"
            ]
        return colors[category_id % len(colors)]

if __name__ == "__main__":
    app = ObjectDetectionViewer()
    app.mainloop()