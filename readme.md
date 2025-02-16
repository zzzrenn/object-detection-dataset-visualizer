# Object Detection Dataset Visualization Tool

A minimalistic visualization tool for object detection datasets with features to filter and merge classes into new desired classes, and export the new annotations into COCO or YOLO format.

## Description

This visualization tool is designed to streamline the process of managing and visualizing object detection datasets. This tool provides a user-friendly interface for viewing images and their corresponding annotations, making it easier to understand and analyze the dataset. Key features include the ability to filter and merge classes into new desired classes, which is particularly useful for refining and customizing datasets to meet specific project requirements. Once the desired modifications are made, the tool allows users to export the updated annotations in popular formats such as COCO or YOLO, ensuring compatibility with various machine learning frameworks. This tool is ideal for data scientists, machine learning engineers, and researchers who need an efficient way to manage and preprocess object detection datasets for training and evaluation purposes.



## Getting Started

### Installing
```
pip install -r requirements.txt
```

### Executing program
* Start the GUI 
    ```
    python app.py
    ```
* ![app_image](https://raw.githubusercontent.com/zzzrenn/object-detection-dataset-visualizer/master/.images/app.png)
#### Image visualization feature
* Load the dataset by selecting the image folder path and the corresponding annotation file and then clicking the load dataset button.
* Use the left and right buttons on the keyboard to view the previous or next image.
* Scroll to zoom in and out, click, and drag to pan around the image.
* Hover the mouse over the drawn boxes to view their metadata.

#### Export features
* Click export dataset to filter and merge existing classes into new self-defined classes.
* ![filter_class](https://raw.githubusercontent.com/zzzrenn/object-detection-dataset-visualizer/master/.images/filter.png)
* ![merge_class](https://raw.githubusercontent.com/zzzrenn/object-detection-dataset-visualizer/master/.images/merge.png)

### TODO
- [ ] Support YOLO format
- [ ] Support VOC format
