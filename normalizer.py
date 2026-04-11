import os
import json
import logging
import uuid
from typing import List, Dict, Any, Optional, Type, Union
from datetime import datetime
from pydantic import BaseModel, ValidationError

# Unified Models
from models.residential_property_rent import ResidentialPropertyRent
from models.residential_property_sell import ResidentialPropertySell
from models.commercial_property_rent import CommercialPropertyRent
from models.commercial_property_sell import CommercialPropertySell

# Mappers
from mappers.nobroker_mapper import NoBrokerMapper
from mappers.magicbricks_mapper import MagicBricksMapper
from mappers.housing_mapper import HousingMapper
from mappers.acres99_mapper import Acres99Mapper

# Utils
from llm_utils import ollama_client, OLLAMA_MODEL, get_coordinates

logger = logging.getLogger(__name__)

class Normalizer:
    def __init__(self):
        self.mappers = {
            "nobroker": NoBrokerMapper.map,
            "magicbricks": MagicBricksMapper.map,
            "housing": HousingMapper.map,
            "99acres": Acres99Mapper.map
        }
        self.source_codes = {
            "magicbricks": "mb",
            "nobroker": "nb",
            "housing": "hs",
            "99acres": "99",
            "user": "mt"
        }

    def normalize_batch(self, raw_items: List[Dict[str, Any]], source: str, property_type: str = "residential", intent: str = "rent") -> List[Any]:
        normalized_results = []
        for item in raw_items:
            try:
                normalized = self.normalize(item, source, property_type, intent)
                if normalized:
                    normalized_results.append(normalized)
            except Exception as e:
                logger.error(f"Failed to normalize item from {source}: {e}")
        return normalized_results

    def normalize(self, item: Dict[str, Any], source: str, property_type: str, intent: str) -> Optional[BaseModel]:
        # Determine target model
        model_class = self._get_model_class(property_type, intent)
        
        # 1. Try Source-Specific Mapping
        mapping_func = self.mappers.get(source.lower())
        normalized_data = None
        if mapping_func:
            normalized_data = mapping_func(item, intent)
        
        # 2. Fallback to LLM Mapping if data is incomplete or source unknown
        if not isinstance(normalized_data, dict) or not normalized_data.get("property_id") or normalized_data.get("property_id") == "None":
            normalized_data = self.llm_normalize(item, model_class)

        # Final check if LLM or mapper returned a dict
        if not isinstance(normalized_data, dict):
            return None

        # 3. Geo-enrichment if missing or [0.0, 0.0]
        try:
            location_data = normalized_data.get("location")
            if not isinstance(location_data, dict):
                location_data = {}
                normalized_data["location"] = location_data

            coords = location_data.get("coordinates")
            is_invalid_coords = not coords or not isinstance(coords, list) or len(coords) < 2 or (coords[0] == 0.0 and coords[1] == 0.0)
            
            if is_invalid_coords:
                loc_name = normalized_data.get("property_address", {}).get("main_text")
                city = normalized_data.get("property_address", {}).get("city", "Mumbai")
                search_query = f"{loc_name}, {city}" if loc_name else city
                
                if search_query:
                    res_coords = get_coordinates(search_query)
                    if res_coords:
                        location_data["type"] = "Point"
                        location_data["coordinates"] = [res_coords["lon"], res_coords["lat"]]
        except Exception as e:
            logger.error(f"Error during geo-enrichment: {e}")

        # 4. Standardize common fields
        if not normalized_data.get("listing_source"):
            normalized_data["listing_source"] = self.source_codes.get(source.lower(), "mt")
             
        if not normalized_data.get("property_id") or normalized_data.get("property_id") == "None":
            normalized_data["property_id"] = str(uuid.uuid4())
        
        if not normalized_data.get("property_status"):
            normalized_data["property_status"] = "open"

        # 5. Validate with Pydantic
        try:
            return model_class(**normalized_data)
        except ValidationError as e:
            return None

    def _get_model_class(self, property_type: str, intent: str) -> Type[BaseModel]:
        if property_type == "residential":
            return ResidentialPropertyRent if intent == "rent" else ResidentialPropertySell
        else:
            return CommercialPropertyRent if intent == "rent" else CommercialPropertySell

    def llm_normalize(self, item: Dict[str, Any], model_class: Type[BaseModel]) -> Optional[Dict[str, Any]]:
        fields_info = {name: str(field.annotation) for name, field in model_class.model_fields.items()}
        prompt = (
            f"Map the following data into our JSON format.\n"
            f"Target Fields: {json.dumps(fields_info)}\n"
            f"Raw Data: {json.dumps(item)}\n"
            f"Return ONLY the JSON object."
        )
        try:
            response = ollama_client.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}], format="json")
            return json.loads(response['message']['content'])
        except Exception:
            return None
