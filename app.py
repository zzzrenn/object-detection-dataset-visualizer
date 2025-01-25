import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import json
import os
from collections import defaultdict

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
        self.current_image = None
        self.photo_image = None
        self.zoom_factor = 1.0
        self.class_checkboxes = {}
        self.visible_classes = set()
        self.selected_box = None

        # dataset info
        self.dataset_format_options = ["COCO"]
        self.image_path = None
        self.annotation_path = None
        
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
        self.canvas.bind('<ButtonPress-1>', self.on_canvas_click)
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)

    def on_canvas_click(self, event):
        # Find clicked box and show metadata
        clicked_items = self.canvas.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)
        for item in clicked_items:
            tags = self.canvas.gettags(item)
            if "box" in tags:
                # Show metadata in a popup
                self.show_box_metadata(tags[1])
                break

    def on_mousewheel(self, event):
        # Zoom in/out with mouse wheel
        if event.delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor *= 0.9
        self.load_current_image()

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
        load_btn = ctk.CTkButton(
            self.load_frame, 
            text="Load Dataset", 
            width=100,
            command=self.load_dataset
        )
        load_btn.grid(row=0, column=8, padx=5, pady=5)

        # Save and export frame
        self.save_frame = ctk.CTkFrame(self)
        self.save_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=5, pady=5)

        # Save current image button
        save_btn = ctk.CTkButton(
            self.save_frame, 
            text="Save Current Image", 
            command=self.save_current_image
        )
        save_btn.pack(side="left", padx=5)
        
        # Export button
        export_btn = ctk.CTkButton(
            self.save_frame, 
            text="Export COCO Annotations", 
            command=self.export_annotations
        )
        export_btn.pack(side="left", padx=5)

        # Configure column weights for responsive layout
        self.load_frame.grid_columnconfigure(4, weight=1)
        self.load_frame.grid_columnconfigure(7, weight=1)   

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
        
    def load_dataset(self):     
        assert self.image_path and self.annotation_path, "Missing image path and/or annotation path!"
            
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
            
        # Set image list for navigation
        self.image_list = list(self.images.keys())
        self.current_image_index = 0
        
        # Update UI
        self.update_class_checkboxes()
        self.load_current_image()
        
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
            var = tk.BooleanVar(value=count > 0)
            
            checkbox = ctk.CTkCheckBox(
                self.sidebar,
                text=f"{cat_info['name']} ({count})",
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
        self.draw_annotations()
        
    def load_current_image(self):
        if not self.image_list:
            return
            
        current_image_id = self.image_list[self.current_image_index]
        image_info = self.images[current_image_id]
        
        # Load image file
        image_path = os.path.join(self.image_path, image_info['file_name'])
        try:
            self.current_image = Image.open(image_path)
        except:
            self.current_image = Image.new('RGB', (800, 600), 'gray')
            
        # Apply zoom
        new_size = tuple(int(dim * self.zoom_factor) for dim in self.current_image.size)
        self.current_image = self.current_image.resize(new_size, Image.Resampling.LANCZOS)
        
        self.photo_image = ImageTk.PhotoImage(self.current_image)
        
        # Update canvas
        self.canvas.delete("all")
        self.canvas.create_image(
            self.canvas.winfo_width()//2,
            self.canvas.winfo_height()//2,
            image=self.photo_image,
            anchor="center"
        )
        
        # Update class checkboxes and draw annotations
        self.update_class_checkboxes()
        self.draw_annotations()
        
    def draw_annotations(self):
        self.canvas.delete("box")
        
        if not self.image_list:
            return
            
        current_image_id = self.image_list[self.current_image_index]
        current_anns = self.image_annotations[current_image_id]
        
        # Calculate canvas center offset
        cx = self.canvas.winfo_width()//2 - self.current_image.width//2
        cy = self.canvas.winfo_height()//2 - self.current_image.height//2
        
        for ann in current_anns:
            if ann['category_id'] not in self.visible_classes:
                continue
                
            # Convert COCO bbox [x, y, width, height] to [x1, y1, x2, y2]
            x, y, w, h = ann['bbox']
            x1, y1 = x * self.zoom_factor, y * self.zoom_factor
            x2, y2 = (x + w) * self.zoom_factor, (y + h) * self.zoom_factor
            
            # Create unique tag for this box
            box_tag = f"box_{ann['category_id']}_{ann['id']}"
            
            # Draw box
            self.canvas.create_rectangle(
                x1 + cx, y1 + cy, x2 + cx, y2 + cy,
                outline=self.get_color(ann['category_id']),
                width=2,
                tags=("box", box_tag)
            )
            
            # Draw label
            category_name = self.categories[ann['category_id']]['name']
            self.canvas.create_text(
                x1 + cx, y1 + cy - 5,
                text=f"{category_name} ({ann['score']:.2f})",
                fill="white",
                anchor="sw",
                tags=("box", box_tag)
            )
            
    def get_color(self, category_id):
        # Generate consistent color for each category
        colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF']
        return colors[category_id % len(colors)]
        
    def show_box_metadata(self, box_tag):
        _, category_id, ann_id = box_tag.split("_")
        category_id = int(category_id)
        ann_id = int(ann_id)
        
        # Find annotation
        current_image_id = self.image_list[self.current_image_index]
        ann = next(a for a in self.image_annotations[current_image_id] 
                  if a['id'] == ann_id)
        
        # Create popup window
        popup = ctk.CTkToplevel(self)
        popup.title("Box Metadata")
        popup.geometry("300x200")
        
        # Add metadata
        ctk.CTkLabel(popup, text=f"Category: {self.categories[category_id]['name']}").pack(pady=5)
        ctk.CTkLabel(popup, text=f"Confidence: {ann['score']:.3f}").pack(pady=5)
        ctk.CTkLabel(popup, text=f"Bbox: {[round(x, 2) for x in ann['bbox']]}").pack(pady=5)
        ctk.CTkLabel(popup, text=f"Annotation ID: {ann_id}").pack(pady=5)
        
    def next_image(self, event=None):
        if self.current_image_index < len(self.image_list) - 1:
            self.current_image_index += 1
            self.load_current_image()
            
    def prev_image(self, event=None):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_current_image()
            
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
        img_draw = self.current_image.copy()
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
            draw.text((x, y - 10), f"{category_name} ({ann['score']:.2f})", fill=color)
            
        # Save image
        img_draw.save(filename)
        
    def export_annotations(self):
        if not self.image_list:
            return
            
        # Open file dialog
        filename = tk.filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if not filename:
            return
            
        # Create COCO format data
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
                    'name': cat_info['name']
                }
                for cat_id, cat_info in self.categories.items()
            ],
            'annotations': [
                {
                    'id': ann['id'],
                    'image_id': img_id,
                    'category_id': ann['category_id'],
                    'bbox': ann['bbox'],
                    'score': ann['score']
                }
                for img_id, anns in self.image_annotations.items()
                for ann in anns
            ]
        }
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)

if __name__ == "__main__":
    app = ObjectDetectionViewer()
    app.mainloop()