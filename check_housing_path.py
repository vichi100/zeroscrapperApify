import json
import os

def check_keys():
    sample_file = "housing_details_sample.json"
    with open(sample_file, "r") as f:
        data = json.load(f)
    
    print("Top level keys:", list(data.keys()))
    if "propertyDetails" in data:
        print("propertyDetails keys:", list(data["propertyDetails"].keys()))
        if "details" in data["propertyDetails"]:
            print("propertyDetails.details keys:", list(data["propertyDetails"]["details"].keys()))
            if "overviewPoints" in data["propertyDetails"]["details"]:
                print("Found overviewPoints!")
                print("Count:", len(data["propertyDetails"]["details"]["overviewPoints"]))
    
    # Maybe it's nested differently
    # Let's search for overviewPoints in the whole dict
    def find_key(d, key, path=""):
        if isinstance(d, dict):
            for k, v in d.items():
                if k == key:
                    yield f"{path}.{k}"
                yield from find_key(v, key, f"{path}.{k}")
        elif isinstance(d, list):
            for i, item in enumerate(d):
                yield from find_key(item, key, f"{path}[{i}]")

    print("\nSearching for 'overviewPoints' path...")
    for p in find_key(data, "overviewPoints"):
        print(p)

if __name__ == "__main__":
    check_keys()
