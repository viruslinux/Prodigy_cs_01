#!/usr/bin/env python3
# -- coding: utf-8 --
"""
Image Encryptor / Decryptor
---------------------------
Features:
- Encrypt or decrypt PNG/JPG/JPEG while preserving image size and format
- Interactive menu OR argparse CLI flags
- Input validation and clear error messages
- Safe output naming (auto-suggests filenames if --out not provided)
- Bytewise XOR stream cipher from your integer key (symmetric)
- Lightweight progress bar without extra packages
- Logs summary to console; non-destructive (won't overwrite unless you confirm)

Requires: Pillow (pip install pillow)
"""

from __future__ import annotations
import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

try:
    from PIL import Image
except ImportError:  # Pillow not installed
    print("Pillow is required. Install with:  pip install pillow")
    sys.exit(1)


# ----------------------------- Utilities ---------------------------------- #

BANNER = r"""
  ___                       _____                      _             
 |_ | __ ___   __ _  ___ | ___|  _____ _ __  _ __ () __   __ _ 
  | || '_ ` _ \ / ` |/ _ \|  _| \ \/ / _ \ ' \| '_ \| | '_ \ / _` |
  | || | | | | | (| | () | |___ >  <  _/ | | | | | | | | | | (| |
 ||| || ||\,|\/|//\\|| ||| |||| ||\_, |
                                                               |_/ 
"""

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg"}


def human_path(p: Path) -> str:
    """Pretty display for paths."""
    try:
        return str(p.resolve())
    except Exception:
        return str(p)


def confirm(prompt: str, default: bool = False) -> bool:
    """Y/N prompt."""
    yes = {"y", "yes"}
    no = {"n", "no"}
    default_str = "Y/n" if default else "y/N"
    while True:
        ans = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not ans:
            return default
        if ans in yes:
            return True
        if ans in no:
            return False
        print("Please answer y or n.")


def progress_bar(iterable: Iterable, total: int, width: int = 30, label: str = "Working"):
    """Minimal progress bar without external deps."""
    done = 0
    start = time.time()
    last_draw = 0.0

    def draw():
        nonlocal last_draw
        now = time.time()
        # Throttle redraws to avoid flicker
        if now - last_draw < 0.03 and done != total:
            return
        last_draw = now
        filled = int(width * done / max(total, 1))
        bar = "█" * filled + " " * (width - filled)
        pct = (done / total * 100.0) if total else 100.0
        elapsed = now - start
        end = "" if done != total else "\n"
        sys.stdout.write(f"\r{label} |{bar}| {pct:6.2f}%  {done}/{total}  {elapsed:5.1f}s")
        sys.stdout.flush()
        if end:
            sys.stdout.write(end)

    for item in iterable:
        yield item
        done += 1
        draw()
    # make sure we end on a newline
    if done == total:
        draw()


def derive_keystream(key: int, length: int) -> bytes:
    """
    Create a deterministic pseudo keystream from an integer key.
    This is NOT cryptographically strong—good enough for coursework.
    """
    # simple LCG parameters (numerical recipes)
    a = 1664525
    c = 1013904223
    m = 2**32
    state = (key & 0xFFFFFFFF) or 0xA5A5A5A5
    out = bytearray(length)
    for i in range(length):
        state = (a * state + c) % m
        out[i] = (state >> 16) & 0xFF
    return bytes(out)


def xor_bytes(data: bytes, key: int) -> bytes:
    """XOR data with keystream derived from key."""
    ks = derive_keystream(key, len(data))
    return bytes(d ^ k for d, k in zip(data, ks))


def load_image_bytes(path: Path) -> Tuple[Image.Image, bytes, str]:
    """
    Load an image and return (PIL image, raw bytes, mode).
    Ensures we have 3-channel (RGB) or 4-channel (RGBA) data.
    """
    img = Image.open(path)
    original_mode = img.mode
    if img.mode not in ("RGB", "RGBA"):
        # Convert paletted/L mode/etc. to RGB to keep things simple
        img = img.convert("RGBA" if img.mode == "LA" else "RGB")
    raw = img.tobytes()
    return img, raw, original_mode


def save_image_bytes(
    img: Image.Image,
    raw: bytes,
    out_path: Path,
    original_mode: str,
):
    """
    Save raw bytes back into an image with the same size and correct mode.
    For JPEGs, apply a reasonable quality; PNG will be lossless.
    """
    # Ensure the base image container has the right mode (RGB or RGBA)
    target_mode = img.mode
    out_img = Image.frombytes(target_mode, img.size, raw)

    # JPEG quality hints (PNG ignores them)
    save_kwargs = {}
    if out_path.suffix.lower() in (".jpg", ".jpeg"):
        save_kwargs["quality"] = 95
        save_kwargs["subsampling"] = 2

    out_img.save(out_path, **save_kwargs)


def suggest_output_name(in_path: Path, mode: str) -> Path:
    stem = in_path.stem
    suffix = in_path.suffix
    tag = "_enc" if mode == "enc" else "_dec"
    candidate = in_path.with_name(f"{stem}{tag}{suffix}")
    i = 1
    while candidate.exists():
        candidate = in_path.with_name(f"{stem}{tag}_{i}{suffix}")
        i += 1
    return candidate


# ----------------------------- Core Logic ---------------------------------- #

@dataclass
class Job:
    mode: str           # "enc" or "dec"
    in_path: Path
    out_path: Path
    key: int


def run_job(job: Job) -> Path:
    """Encrypt or decrypt a single image file per the job definition."""
    if job.in_path.suffix.lower() not in SUPPORTED_EXTS:
        raise ValueError(f"Unsupported extension: {job.in_path.suffix} "
                         f"(supported: {', '.join(sorted(SUPPORTED_EXTS))})")
    if not job.in_path.exists():
        raise FileNotFoundError(f"Input image not found: {human_path(job.in_path)}")

    # Read
    img, raw, _original_mode = load_image_bytes(job.in_path)

    # Transform w/ simple XOR stream
    label = "Encrypting" if job.mode == "enc" else "Decrypting"
    block = 32_768  # 32 KB chunks for progress display
    transformed = bytearray(len(raw))
    total_blocks = (len(raw) + block - 1) // block

    for i, start in enumerate(progress_bar(range(total_blocks), total_blocks, label=label)):
        s = start * block
        e = min(s + block, len(raw))
        transformed[s:e] = xor_bytes(raw[s:e], job.key)

    # Save
    job.out_path.parent.mkdir(parents=True, exist_ok=True)
    save_image_bytes(img, bytes(transformed), job.out_path, _original_mode)

    return job.out_path


# -------------------------- CLI / Interactive ------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Encrypt or decrypt PNG/JPG images using a simple XOR stream cipher.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--mode", choices=["enc", "dec"], help="enc = encrypt, dec = decrypt")
    p.add_argument("--in", dest="in_path", help="Input image file (PNG/JPG/JPEG)")
    p.add_argument("--out", dest="out_path", help="Optional output path/filename")
    p.add_argument("--key", type=int, help="Integer key (use same key to decrypt)")
    return p


def interactive_flow() -> Job:
    print(BANNER)
    print("Welcome! Choose an option:\n")
    print("  1) Encrypt an image")
    print("  2) Decrypt an image")
    print("  3) Exit\n")

    while True:
        choice = input("Enter your choice (1/2/3): ").strip()
        if choice in {"1", "2", "3"}:
            break
        print("Invalid choice. Try again.")

    if choice == "3":
        print("Goodbye!")
        sys.exit(0)

    mode = "enc" if choice == "1" else "dec"

    # Input path
    while True:
        raw_path = input("Enter the image path (PNG/JPG/JPEG): ").strip().strip('"')
        in_path = Path(raw_path)
        if in_path.exists() and in_path.suffix.lower() in SUPPORTED_EXTS:
            break
        print("That file either doesn't exist or uses an unsupported extension. Try again.")

    # Key
    while True:
        key_str = input("Enter a numeric key (e.g., 7 or 12345): ").strip()
        if key_str.isdigit():
            key = int(key_str)
            if 0 <= key <= 2**31 - 1:
                break
        print("Please enter a valid non-negative integer key.")

    # Output
    suggested = suggest_output_name(in_path, mode)
    out_raw = input(f'Output filename (press Enter for "{suggested.name}"): ').strip()
    out_path = Path(out_raw) if out_raw else suggested
    out_path = out_path if out_path.is_absolute() else in_path.parent / out_path

    if out_path.exists():
        if not confirm(f'"{out_path.name}" already exists. Overwrite?', default=False):
            out_path = suggest_output_name(in_path, mode)
            print(f"Will write to: {out_path.name}")

    return Job(mode=mode, in_path=in_path, out_path=out_path, key=key)


def from_args(args: argparse.Namespace) -> Job | None:
    """Convert argparse args to a Job; return None if args are incomplete."""
    if not (args.mode and args.in_path and args.key is not None):
        return None

    in_path = Path(args.in_path)
    out_path = Path(args.out_path) if args.out_path else suggest_output_name(in_path, args.mode)

    # prompt before overwrite
    if out_path.exists():
        if not confirm(f'"{human_path(out_path)}" exists. Overwrite?', default=False):
            print("Aborted by user.")
            sys.exit(1)

    return Job(mode=args.mode, in_path=in_path, out_path=out_path, key=int(args.key))


def main():
    parser = build_parser()
    args = parser.parse_args()

    if any([args.mode, args.in_path, args.out_path, args.key is not None]) and from_args(args) is None:
        print(BANNER)
        print("Some required flags are missing.\n")
        parser.print_help()
        print("\nAlternatively, just run python image_encryptor.py and use the interactive menu.")
        sys.exit(2)

    job = from_args(args) or interactive_flow()

    print("\nSummary")
    print("-" * 60)
    print(f" Mode      : {'Encrypt' if job.mode == 'enc' else 'Decrypt'}")
    print(f" Input     : {human_path(job.in_path)}")
    print(f" Output    : {human_path(job.out_path)}")
    print(f" Key       : {job.key}")
    print("-" * 60)

    try:
        final_path = run_job(job)
        print(f"\n✅ Done! File written to: {human_path(final_path)}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()