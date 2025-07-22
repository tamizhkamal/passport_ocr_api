from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import tempfile, cv2, pytesseract, re
from datetime import datetime
from passporteye import read_mrz

@csrf_exempt
def extract_passport(request):
    if request.method == 'POST':
        passport_file = request.FILES.get('passport_file')
        if not passport_file:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            for chunk in passport_file.chunks():
                tmp.write(chunk)
            temp_file_path = tmp.name
        
        # Extract MRZ data
        mrz_data = extract_mrz_from_image(temp_file_path)
        # print("MRZ Data:", mrz_data, "<------------ MRZ Extraction Output")

        # Build response
        passport_data = {
            "fullname": f"{mrz_data.get('names', '')} {mrz_data.get('surname', '')}".strip(),
            "surname": mrz_data.get('surname'),
            "middleName": None,
            "fatherName": None,
            "spouseName": None,
            "mothername": None,
            "placeOfBirth": None,
            "placeOfIssue": None,
            "passportType": mrz_data.get('mrz_type'),
            "country": mrz_data.get('country'),
            "passportNo": mrz_data.get('number'),
            "nationality": mrz_data.get('nationality'),
            "maritalStatus": None,
            "sex": mrz_data.get('sex'),
            "dateOfBirth": parse_mrz_date(mrz_data.get('date_of_birth')),
            "address": None,
            "profession": None,
            "dateOfExpiry": parse_mrz_date(mrz_data.get('expiration_date')),
            "dateOfIssue": None,
            "footerText": mrz_data.get('raw_text')
        }

        # ✅ MUST RETURN JsonResponse
        return JsonResponse(passport_data)

    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


def extract_mrz_from_image(image_path):

    mrz = read_mrz(image_path)
    if mrz is None:
        return {}
    return mrz.to_dict()


def parse_mrz_date(mrz_date):
    try:
        return datetime.strptime(mrz_date, "%y%m%d").strftime("%Y-%m-%d")
    except:
        return None
