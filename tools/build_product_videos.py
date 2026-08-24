"""Build short product walkthrough MP4s from captured app screenshots."""
from __future__ import annotations

from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("web/public/marketing")
FRAMES = ROOT / "frames"
OUT = ROOT / "videos"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1280, 720
FPS = 24

VIDEOS = [
    {
        "id": "research",
        "title": "Market Research",
        "subtitle": "Generate sourced reports from your niche",
        "steps": [
            "Open Market Research and pick your project",
            "Set topic, industry, and market",
            "Choose report depth and click Generate report",
            "Download Markdown or read the report in-app",
        ],
        "shots": ["research2.png", "research.png"],
    },
    {
        "id": "plan",
        "title": "Business Planning",
        "subtitle": "Turn research into an investor-ready plan",
        "steps": [
            "Open Business Plan on the same project",
            "Use latest research or add notes",
            "Click Build Agentic Business Plan",
            "Read Plan Output and export when ready",
        ],
        "shots": ["plan.png", "howto.png"],
    },
    {
        "id": "execute",
        "title": "Employee OS",
        "subtitle": "AI employees execute with your approval",
        "steps": [
            "Open Employee OS and save workspace scope",
            "Build checklist from your plan",
            "Run next task or full office day",
            "Approve external actions before send",
        ],
        "shots": ["execute.png"],
    },
    {
        "id": "automate",
        "title": "Automation",
        "subtitle": "Build and run CRM / outreach workflows",
        "steps": [
            "Open Automation builder",
            "Pick steps or ask Taylor to find leads",
            "Connect apps under Integrations",
            "Run steps with credits and review outputs",
        ],
        "shots": ["automate.png", "howto.png"],
    },
    {
        "id": "mentor",
        "title": "Mentor",
        "subtitle": "Coach grounded in your project memory",
        "steps": [
            "Open Mentor with your project selected",
            "Review org memory, research, and goals",
            "Ask what to finish this week",
            "Hand work to Taylor when ready to execute",
        ],
        "shots": ["mentor.png"],
    },
    {
        "id": "brand",
        "title": "Brand & Deliverables",
        "subtitle": "Package research and plans for stakeholders",
        "steps": [
            "Export reports and plans from the workspace",
            "Use Reference tools for decks and one-pagers",
            "Share bank- or board-ready outputs",
            "Keep brand assets in one project vault",
        ],
        "shots": ["howto.png", "research.png"],
    },
]


def font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def solid(color=(8, 14, 28)):
    return Image.new("RGB", (W, H), color)


def fit_shot(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGB")
    # cover resize
    scale = max(W / im.width, H / im.height)
    nw, nh = int(im.width * scale), int(im.height * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - W) // 2
    top = (nh - H) // 2
    return im.crop((left, top, left + W, top + H))


def title_card(title: str, subtitle: str) -> Image.Image:
    img = solid()
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 8), fill=(11, 95, 255))
    draw.text((64, 220), "IIDATECH", font=font(28, True), fill=(120, 170, 255))
    draw.text((64, 280), title, font=font(64, True), fill=(255, 255, 255))
    draw.text((64, 370), subtitle, font=font(30), fill=(180, 196, 220))
    draw.text((64, 640), "Product walkthrough", font=font(22), fill=(100, 120, 150))
    return img


def steps_card(title: str, steps: list[str]) -> Image.Image:
    img = solid()
    draw = ImageDraw.Draw(img)
    draw.text((64, 80), title, font=font(42, True), fill=(255, 255, 255))
    draw.text((64, 140), "How it works in the app", font=font(26), fill=(120, 170, 255))
    y = 220
    for i, step in enumerate(steps, 1):
        draw.ellipse((64, y + 6, 96, y + 38), fill=(11, 95, 255))
        draw.text((72, y + 8), str(i), font=font(18, True), fill=(255, 255, 255))
        draw.text((120, y), step, font=font(28), fill=(230, 236, 245))
        y += 70
    return img


def overlay_caption(base: Image.Image, text: str) -> Image.Image:
    img = base.copy()
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle((0, H - 110, W, H), fill=(0, 0, 0, 170))
    draw.text((40, H - 72), text, font=font(28, True), fill=(255, 255, 255, 255))
    return img.convert("RGB")


def hold(frames: list, img: Image.Image, seconds: float):
    arr = np.asarray(img)
    for _ in range(int(seconds * FPS)):
        frames.append(arr)


def ken_burns(frames: list, img: Image.Image, seconds: float = 3.0):
    n = max(1, int(seconds * FPS))
    # slight zoom
    for i in range(n):
        t = i / max(1, n - 1)
        scale = 1.0 + 0.06 * t
        nw, nh = int(W * scale), int(H * scale)
        zoomed = img.resize((nw, nh), Image.Resampling.LANCZOS)
        left = (nw - W) // 2
        top = int((nh - H) * 0.35 * t)
        crop = zoomed.crop((left, top, left + W, top + H))
        frames.append(np.asarray(crop))


def build_one(spec: dict):
    frames: list = []
    hold(frames, title_card(spec["title"], spec["subtitle"]), 2.2)
    hold(frames, steps_card(spec["title"], spec["steps"]), 4.0)
    for idx, shot_name in enumerate(spec["shots"]):
        path = FRAMES / shot_name
        if not path.exists():
            continue
        shot = fit_shot(path)
        caption = spec["steps"][min(idx, len(spec["steps"]) - 1)]
        ken_burns(frames, overlay_caption(shot, caption), 3.2)
    hold(frames, title_card(spec["title"], "Try it free on iidatech.biz"), 2.0)
    out = OUT / f"{spec['id']}.mp4"
    imageio.mimsave(
        out,
        frames,
        fps=FPS,
        codec="libx264",
        quality=7,
        pixelformat="yuv420p",
        macro_block_size=1,
    )
    print("wrote", out, "frames", len(frames), "bytes", out.stat().st_size)


def main():
    for spec in VIDEOS:
        build_one(spec)
    print("done")


if __name__ == "__main__":
    main()
