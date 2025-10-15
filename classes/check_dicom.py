import pydicom

dcm_path = "Data/DICOM/P0000001/ST000002/SE000003/IN000001"   # 改成你的路径
ds = pydicom.dcmread(dcm_path)

fields = [
    "PixelSpacing",
    "ImagerPixelSpacing",
    "DistanceSourceToDetector",
    "DistanceSourceToPatient",
    "KVP",
    "ExposureTime",
    "XRayTubeCurrent",
    "Exposure",
    "BodyPartExamined",
    "ViewPosition",
]

for f in fields:
    if f in ds:
        print(f"{f}: {ds.get(f)}")

# 额外打印图像大小
print(f"Rows: {ds.Rows}, Columns: {ds.Columns}")
