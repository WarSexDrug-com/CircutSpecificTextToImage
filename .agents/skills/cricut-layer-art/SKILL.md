---
name: cricut-layer-art
description: Design multi-layer Cricut and vinyl-cut artwork from text prompts. Use this skill whenever the user asks for a Cricut design, layered paper craft, cut-ready SVG, or text-to-image artwork with clean lines, a specific layer count, or a limited/selected palette. Aim for clean, aligned, cuttable layers with exactly the requested number of colors, and do not require an OpenAI API key or a particular image-generation provider.
---

# Cricut Layer Art

Turn a user's idea into simple, attractive artwork that can be separated by color and cut on a Cricut. The result should be useful for making something, not merely a pretty raster preview.

## Choose the best way to create it

- Use an available native image-generation tool when the user asks to see generated artwork. Do not assume a particular provider or ask for an API key just to write a design prompt.
- Treat generated raster art as a concept image. Image models often add stray colors, soft edges, gradients, or details that are difficult to cut. For a cut-ready deliverable, convert or recreate the design as vector shapes and check the final palette.
- Prefer native SVG for the final cutting design when a workspace file is appropriate. If image generation or vector conversion is unavailable, still help: write a ready-to-use generation prompt, a layer plan, or SVG markup instead of stopping at an API-key requirement.
- If the user asks specifically for an image prompt, return the prompt; do not silently create files. If they ask to make the artwork or give a file destination, create the appropriate artifact there.

## Lock the palette and layer count

1. Read the requested layer/color count and exact palette from the user's instructions or active design controls. Respect their count. If no count is specified, ask one concise question only when it materially changes the deliverable; otherwise use a small craft-friendly default such as 4 colors and state it.
2. Keep the palette to exactly the requested number of distinct solid colors. Do not introduce extra colors for outlines, highlights, shadows, background, antialiasing, or decoration. Use the selected palette values exactly when supplied.
3. If no palette was supplied, choose a cohesive, high-contrast palette with the requested number of colors and show it alongside the result.
4. Keep the background transparent/absent unless the user explicitly asks for a background layer. If they request a background layer, count it as one of the selected layers/colors.
5. For an SVG, use one named group per palette color, with fill values limited to that palette. Avoid gradients, filters, masks, embedded images, CSS color effects, and accidental default black fills.
6. If a raster generation tool creates off-palette pixels, quantize to the selected palette before tracing. Inspect/verify distinct colors after conversion. If exact palette enforcement cannot be done with available tools, label the image as a concept preview and provide a prompt or vector plan that can meet the constraint; never claim it has exactly K colors without checking.

## Make shapes cut cleanly

- Use bold, closed, simple silhouettes with smooth contours and clear negative space.
- Build separate color layers that align when stacked. Extend lower/base shapes slightly under upper shapes to prevent visible gaps from hand placement.
- Prefer a few larger shapes to many tiny islands. Avoid hairline bridges, pinholes, tiny text, isolated specks, and fragile slivers that are hard to weed.
- Use cutout holes only when they are large enough to cut reliably. Keep text short, bold, and legible; ask for wording if the design depends on exact text and it is missing.
- Do not draw decorative strokes as if they were filled cut regions. Create outlines from closed shapes in one of the selected colors.
- Avoid overlap that makes the stack obscure important details. Keep each layer's silhouette understandable when previewed alone.

## SVG deliverable

When creating a cut-ready SVG:

- Use a square canvas by default unless the user specifies dimensions. Keep all paths inside the viewBox.
- Group paths as `Layer_1_<color-name>`, `Layer_2_<color-name>`, and so on; set each group's solid `fill` to one selected hex value.
- Use only closed vector paths with simple fills. Do not embed a PNG/JPEG or include gradients, filters, scripts, or unnecessary CSS.
- Keep a stable shared coordinate system for all color groups so the design remains aligned when layers are separated.
- Provide one combined layered SVG. If individual color files are useful and file creation is available, also export one aligned SVG per layer without changing its canvas or coordinates.
- Include a small layer legend listing order, color, and what each layer forms. The legend is explanatory and must not add colors or marks to the cut file.

## Prompt template for image generators

When the user wants a prompt rather than a finished SVG, adapt this template and replace the bracketed details:

> Create a clean, flat, layered paper-cut illustration of [SUBJECT]. Use exactly [K] solid colors: [PALETTE]. No other colors. Transparent or plain white empty background [unless a background layer is explicitly requested]. Bold, smooth, closed-edged shapes with crisp boundaries; clear separation between color regions; simple silhouettes designed for stacked cardstock/vinyl cutting. Keep all important details large, connected where practical, and easy to weed. No gradients, shading, shadows, texture, glow, sketch lines, photorealism, or tiny specks. Center the whole design with comfortable margins. [Exact required text, if any.]

Explain briefly that some image generators may add colors or fuzzy edges, so exact Cricut layers require palette quantization/vector cleanup after generation.

## Finish and communicate

- State the palette and layer count in the response, and link any created files.
- Be clear whether the output is a concept image, a prompt, or an inspected cut-ready SVG.
- If exact wording, palette, or dimensions are missing, make a sensible assumption and state it, unless the missing choice would cause substantial rework.
