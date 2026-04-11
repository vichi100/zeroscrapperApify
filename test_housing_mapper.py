import json
from mappers.housing_mapper import HousingMapper

def test_mapper():
    with open("housing_details_sample.json", "r") as f:
        p_data = json.load(f)
    
    item = {"p_data": p_data}
    result = HousingMapper.map(item, "rent")
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_mapper()
