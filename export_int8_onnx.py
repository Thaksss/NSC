from ultralytics import YOLO

def export_model():
    print("Loading YOLO model...")
    model = YOLO("yolov8_trash.pt")
    
    print("Exporting to ONNX (INT8)...")
    model.export(format="onnx", int8=True)
    print("Export finished!")

if __name__ == "__main__":
    export_model()
