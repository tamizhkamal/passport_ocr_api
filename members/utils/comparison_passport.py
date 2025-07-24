def merge_passport_data(data1, data2):
    final_result = {}
    
    for key in data1.keys():
        value1 = data1.get(key)
        value2 = data2.get(key)

        # If both same or only one exists, pick confidently
        if value1 == value2:
            final_result[key] = value1
        elif value1 and not value2:
            final_result[key] = value1
        elif value2 and not value1:
            final_result[key] = value2
        else:
            # If mismatch, choose the longest non-null OR keep both
            if isinstance(value1, str) and isinstance(value2, str):
                final_result[key] = value1 if len(value1) >= len(value2) else value2
            else:
                final_result[key] = value1 or value2  # fallback

    return final_result
