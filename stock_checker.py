import requests
import json
import re

URL = "https://www.terminalx.com/w327090004?color=10"
HEADERS = {"User-Agent": "Mozilla/5.0"}
TARGET_SIZES = {"43", "44", "45"}


def extract_product_json(html):
    # Find the "variants":[ section and extract the array
    variants_start = html.find('"variants":[')
    if variants_start == -1:
        return None
    
    # Start from the [ after "variants":
    start = html.find('[', variants_start)
    if start == -1:
        return None
    
    # Find the matching closing bracket by counting brackets
    bracket_count = 0
    end = start
    for i in range(start, len(html)):
        if html[i] == '[':
            bracket_count += 1
        elif html[i] == ']':
            bracket_count -= 1
            if bracket_count == 0:
                end = i + 1
                break
    
    try:
        variants = json.loads(html[start:end])
        return {"variants": variants}
    except:
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
        # Extract color and size from attributes array
        attributes = variant.get("attributes", [])
        color = None
        size = None
        
        for attr in attributes:
            if attr.get("code") == "color":
                color = attr.get("label")
            elif attr.get("code") == "size":
                size = str(attr.get("label"))
        
        # Check stock status
        available = variant.get("product", {}).get("stock_status2") == "IN_STOCK"

        if color and size:
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
