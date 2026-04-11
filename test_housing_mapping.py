import json
import os
from mappers.housing_mapper import HousingMapper

def test_mapping():
    sample_file = "housing_details_sample.json"
    if not os.path.exists(sample_file):
        print(f"Error: {sample_file} not found.")
        return

    with open(sample_file, "r") as f:
        sample_data = json.load(f)
    
    # Wrap in item structure
    item = {"p_data": sample_data}
    
    # Debug: Check overviewPoints
    details = sample_data.get("propertyDetails", {}).get("details", {})
    ops = details.get("overviewPoints", [])
    print(f"Found {len(ops)} overviewPoints")
    for p in ops:
        print(f"ID: {p.get('id')}, Desc: {p.get('description')}")
    
    mapped = HousingMapper.map(item, "rent")
    
    print(json.dumps(mapped, indent=2))
    
    # Verification
    print("\n--- Verification ---")
    rd = mapped.get("rent_details", {})
    pd = mapped.get("property_details", {})
    
    print(f"Rent: {rd.get('rent')}")
    print(f"Deposit: {rd.get('deposit')} (Expected: 550000)")
    print(f"Property Size: {pd.get('property_size')} (Expected: 900)")
    print(f"Floor Number: {pd.get('floor_number')} (Expected: 5)")
    print(f"Total Floor: {pd.get('total_floor')} (Expected: 12)")
    print(f"Property Age: {pd.get('property_age')} (Expected: 2 years)")
    print(f"Parking Number: {pd.get('parking_number')} (Expected: 1)")

if __name__ == "__main__":
    test_mapping()
