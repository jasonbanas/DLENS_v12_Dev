import os

def handler(request):
    filename = request.query.get("file")

    path = f"static_reports/{filename}"

    if not os.path.exists(path):
        return "Report Not Found", 404

    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    return html
