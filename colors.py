class ColorResult:
    def __init__(self, hex, w3c, value):
        self.hex = hex
        self.name = w3c.name
        self.w3c_hex = w3c.hex
        self.prevalence = value
    
    def __str__(self):
        return f"{self.name} ({self.hex})"