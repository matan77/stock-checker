import requests
import json
import re

URL = "https://www.terminalx.com/w327090004?color=10"
HEADERS = {"User-Agent": "Mozilla/5.0"}
TARGET_SIZES = {"43", "44", "45"}


def extract_product_json(html):
    matches = re.findall(r'\{.*\}', html, re.DOTALL)
    for m in matches:
        try:
            data = json.loads(m)
            if "variants" in str(data):
                return data
        except:
            pass
    return None


def check_stock():
    res = requests.get(URL, headers=HEADERS, timeout=10)
    res.raise_for_status()

    product = extract_product_json(res.text)
    if not product:
        raise Exception("Could not find product data")

    report = {}
    found = False

    for variant in product.get("variants", []):
        color = variant.get("option1")
        size = str(variant.get("option2"))
        available = variant.get("available", False)

        if color not in report:
            report[color] = {"43": False, "44": False, "45": False}

        if size in TARGET_SIZES and available:
            report[color][size] = True
            found = True

    return found, report


def format_report(report):
    lines = []
    for color, sizes in report.items():
        available_sizes = [s for s, ok in sizes.items() if ok]
        if available_sizes:
            lines.append(f"🟢 {color}: sizes {', '.join(available_sizes)}")
        else:
            lines.append(f"🔴 {color}: none (43–45)")
    return "\n".join(lines)


if __name__ == "__main__":
    found, report = check_stock()
    report_text = format_report(report)

    # Print everything in logs
    print(report_text)

    # Raise exception if stock found
    if found:
        raise SystemExit("🚨 ITEM IN STOCK — check logs above!")
