class ColorResult:
    def __init__(self, hex, w3c, value):
        self.hex = hex
        self.name = w3c.name
        self.w3c_hex = w3c.hex
        self.prevalence = value
    
    def __str__(self):
        return f"{self.name} ({self.hex})"

class RegionResult:
    def __init__(self, id, rect):
        self.id = id
        self.rect = rect
        self.concepts = []
    
    def addConcept(self, concept):
        self.concepts.append(concept)
    
    def __str__(self):
        return f"{self.id} ({self.rect})"
    
class Concept:
    def __init__(self, id, name, value):
        self.id = id
        self.name = name
        self.confidence = value

    def __str__(self):
        return f"{self.name} ({self.id})"