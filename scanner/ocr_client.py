import requests
import base64
from PIL import Image
import io

OCR_SERVER_URL = "https://ezpage-global-money-scanner.onrender.com/predict"  # OCR 서버 주소

def send_image_to_ocr(image_path):
    try:
        with open(image_path, "rb") as f:
            files = {"image": f}
            response = requests.post(OCR_SERVER_URL, files=files)

        if response.status_code == 200:
            result = response.json()
            
            # Ensure the response has all required fields
            return {
                "total": result.get("total", 0.0),
                "currency_symbol": result.get("currency_symbol", "$"),
                "detected": result.get("detected", {}),
                "converted_total_krw": result.get("converted_total_krw", 0.0),
                "image_base64": result.get("image_base64", "")
            }
        else:
            return {
                "error": f"OCR 서버 호출 실패 (상태 코드: {response.status_code})",
                "total": 0.0,
                "currency_symbol": "$",
                "detected": {},
                "converted_total_krw": 0.0,
                "image_base64": ""
            }
    except Exception as e:
        return {
            "error": f"OCR 처리 중 오류 발생: {str(e)}",
            "total": 0.0,
            "currency_symbol": "$",
            "detected": {},
            "converted_total_krw": 0.0,
            "image_base64": ""
        }
