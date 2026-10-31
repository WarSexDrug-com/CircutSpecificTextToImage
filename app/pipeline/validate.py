import xml.etree.ElementTree as ET
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    is_valid: bool = True
    warnings: list[str] = field(default_factory=list)

    def warn(self, msg: str):
        self.warnings.append(msg)

    def fail(self, msg: str):
        self.is_valid = False
        self.warnings.append(f"ERROR: {msg}")


def validate_svg(svg_content: str) -> ValidationResult:
    result = ValidationResult()

    if len(svg_content.encode("utf-8")) > 5 * 1024 * 1024:
        result.fail("SVG exceeds 5MB file size limit")

    try:
        root = ET.fromstring(svg_content)
    except ET.ParseError as e:
        result.fail(f"Invalid XML: {e}")
        return result

    ns = {"svg": "http://www.w3.org/2000/svg"}

    if root.tag != "{http://www.w3.org/2000/svg}svg" and root.tag != "svg":
        result.fail("Root element is not <svg>")

    viewbox = root.get("viewBox")
    if not viewbox:
        result.fail("Missing viewBox attribute")

    for img in root.iter("{http://www.w3.org/2000/svg}image"):
        result.fail("Contains embedded <image> element")
    for img in root.iter("image"):
        result.fail("Contains embedded <image> element")

    for tag in ("linearGradient", "radialGradient", "pattern", "filter"):
        for _ in root.iter(f"{{{ns['svg']}}}{tag}"):
            result.fail(f"Contains <{tag}> element (not Cricut-compatible)")
        for _ in root.iter(tag):
            result.fail(f"Contains <{tag}> element (not Cricut-compatible)")

    for script in root.iter("{http://www.w3.org/2000/svg}script"):
        result.fail("Contains <script> element")
    for script in root.iter("script"):
        result.fail("Contains <script> element")

    for style in root.iter("{http://www.w3.org/2000/svg}style"):
        result.fail("Contains <style> element")
    for style in root.iter("style"):
        result.fail("Contains <style> element")

    for path in list(root.iter("{http://www.w3.org/2000/svg}path")) + list(root.iter("path")):
        d = path.get("d", "")
        if d and not d.strip().upper().endswith("Z"):
            result.warn(f"Unclosed path detected (d ends with '{d.strip()[-10:]}')")

    return result
