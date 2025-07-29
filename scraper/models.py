from dataclasses import dataclass

@dataclass
class Flower:
    botanical_name: str
    family: str
    url: str
    common_name: str
    description: str = None
    image1_url: str = None
    image2_url: str = None
    image3_url: str = None
    image4_url: str = None