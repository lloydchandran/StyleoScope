from PIL import Image, ImageDraw

class ColorResult:
    def __init__(self, hex, w3c, value):
        self.hex = hex
        self.name = w3c.name
        self.w3c_hex = w3c.hex
        self.prevalence = value
    
    def __str__(self):
        return f"{self.name} ({self.hex})"
    
class Concept:
    def __init__(self, id, name, value):
        self.id = id
        self.name = name
        self.confidence = value

    def __str__(self):
        return f"{self.name} ({self.id})"

class RegionResult:
    def __init__(self, id, rect):
        self.id = id
        self.rect = rect
        self.concepts = []
    
    def addConcept(self, concept):
        self.concepts.append(concept)

    def drawBoundingBox(self, image):
        # Draw a red rectangle around the region
        # Initialize a PIL ImageDraw object so we can draw on the image
        draw = ImageDraw.Draw(image)
        # Calculate the bounding box of the region
        left = image.width * self.rect.left_col
        top = image.height * self.rect.top_row
        right = image.width * self.rect.right_col
        bottom = image.height * self.rect.bottom_row
        # Draw the bounding box rectangle
        draw.rectangle(((left, top), (right, bottom)), outline="lime", width=5)
        # Return the annotated image
        return image
    
    def __str__(self):
        return f"{self.id} ({self.rect})"
