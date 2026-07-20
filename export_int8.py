from ultralytics import YOLO

def export_model():
    print("Loading YOLO model...")
    model = YOLO("yolov8_trash.pt")
    
    print("Exporting to TFLite (INT8)...")
    # TFLite export will use INT8 by default if int8=True is passed
    model.export(format="tflite", int8=True)
    print("Export finished!")

if __name__ == "__main__":
    export_model()
