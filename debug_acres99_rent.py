import json

with open("acres99_details_raw.json", "r") as f:
    data = json.load(f)

for item in data:
    p_data = item.get("data", {}).get("p_data", {})
    if p_data:
        pd = p_data.get("pd", {})
        page_data = pd.get("pageData", {})
        prop_details = page_data.get("propertyDetails", {})
        prop_data = prop_details.get("prop_data", {})
        print("Prop Data Keys:", prop_data.keys())
        for k, v in prop_data.items():
            if "100000" in str(v) or v == 100000:
                print(f"FOUND 100000 in key: {k}")
