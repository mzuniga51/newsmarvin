#!/usr/bin/env python3
"""Generate NewsMarvin logo using Gemini image generation."""

import base64
import sys
from pathlib import Path
from google import genai
from google.genai import types

API_KEY = "AIzaSyCfzoRdugHvrl9FzGseYNZkGLD4OkC0Yhw"
SOURCE_PHOTO = Path.home() / "Desktop" / "IMG_0443.JPG"
OUTPUT_DIR = Path(__file__).parent / "logos"

PROMPTS = [
    {
        "name": "minimal-bw",
        "prompt": (
            "Create a minimal black and white logo icon based on this photo of a small pomeranian dog wearing sunglasses/goggles. "
            "The logo should be a clean, simple silhouette style - just the dog's head in profile/front view with the distinctive sunglasses. "
            "Black on white background. No text. Suitable for a favicon and website header. "
            "Think tech startup logo - clean, modern, memorable. Square format."
        ),
    },
    {
        "name": "stylized-color",
        "prompt": (
            "Create a stylized cartoon logo icon based on this photo of a pomeranian dog wearing sunglasses/goggles. "
            "Use a limited color palette: black, tan/gold, and white. "
            "The dog should look cool and confident with the sunglasses. Minimal detail, bold shapes. "
            "No text. No background. Square format. Suitable for a website logo and favicon."
        ),
    },
    {
        "name": "badge-style",
        "prompt": (
            "Create a circular badge/emblem logo based on this photo of a pomeranian dog wearing sunglasses. "
            "The dog's face should be centered in the circle, stylized and simplified. "
            "Black and gold/amber color scheme. Bold, graphic style. "
            "No text inside the logo. Transparent or white background. Think news agency emblem."
        ),
    },
]


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    client = genai.Client(api_key=API_KEY)

    # Read source photo
    photo_bytes = SOURCE_PHOTO.read_bytes()
    photo_part = types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg")

    for variant in PROMPTS:
        name = variant["name"]
        prompt = variant["prompt"]
        print(f"\nGenerating '{name}'...")

        try:
            # Try Imagen 4.0 (text-to-image, no reference image support)
            response = client.models.generate_images(
                model="imagen-4.0-generate-001",
                prompt=prompt.replace("based on this photo of", "of"),
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                ),
            )

            if response.generated_images:
                img = response.generated_images[0]
                out_path = OUTPUT_DIR / f"logo-{name}.png"
                out_path.write_bytes(img.image.image_bytes)
                print(f"  Saved: {out_path}")
            else:
                print(f"  No images generated")

        except Exception as e:
            print(f"  Imagen error: {e}")
            # Fallback to Gemini Flash image generation
            try:
                print(f"  Trying Gemini Flash fallback...")
                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[photo_part, prompt],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE", "TEXT"],
                    ),
                )
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                        ext = part.inline_data.mime_type.split("/")[1]
                        out_path = OUTPUT_DIR / f"logo-{name}.{ext}"
                        out_path.write_bytes(part.inline_data.data)
                        print(f"  Saved: {out_path}")
                        break
                else:
                    print(f"  No image in fallback response")
            except Exception as e2:
                print(f"  Fallback error: {e2}")


if __name__ == "__main__":
    main()
