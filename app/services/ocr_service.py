import easyocr

reader = easyocr.Reader(["en"])

def extract_text(image):
    result = reader.readtext(image.read(), detail=0)
    return " ".join(result)
