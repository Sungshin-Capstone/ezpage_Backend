import requests

OCR_SERVER_URL = "https://ezpage-global-money-scanner.onrender.com/predict"  # OCR 서버 주소

def send_image_to_ocr(image_path):
    with open(image_path, "rb") as f:
        files = {"image": f}
        response = requests.post(OCR_SERVER_URL, files=files)

    if response.status_code == 200:
        return response.json()  # OCR 결과 반환
    else:
        return {"error": "OCR 서버 호출 실패"}
