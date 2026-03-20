#!/usr/bin/env python3
"""
compress_pdf.py — Compress image-heavy PDFs locally, with a target file-size cap.

Usage:
    python compress_pdf.py input.pdf                        # default quality, 7 MB cap
    python compress_pdf.py input.pdf -o output.pdf          # custom output path
    python compress_pdf.py input.pdf -q 60                  # starting JPEG quality 1–95
    python compress_pdf.py input.pdf --max-dpi 150          # downsample images
    python compress_pdf.py input.pdf --max-size 5           # cap in MB (default 7)
    python compress_pdf.py input.pdf --no-size-cap          # disable the cap

Dependencies:
    pip install pikepdf Pillow
"""

import argparse
import io
import os
import sys
from pathlib import Path

try:
    import pikepdf
    from pikepdf import Pdf, PdfImage, Name
    from PIL import Image
except ImportError:
    print("Missing dependencies. Run:  pip install pikepdf Pillow")
    sys.exit(1)


# ── quality ladder used when auto-shrinking ───────────────────────────────────
# Script walks down this list until the file fits under the size cap.
QUALITY_LADDER = [75, 65, 55, 45, 35, 25, 15]
DPI_LADDER     = [300, 250, 200, 150]


def _compress_once(
    input_path: str,
    output_path: str,
    jpeg_quality: int,
    max_dpi: int | None,
    verbose: bool = True,
) -> dict:
    """Single compression pass. Returns stats dict."""
    total_images = 0
    compressed_images = 0

    with Pdf.open(input_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            for name, xobj in page.images.items():
                total_images += 1

                try:
                    pdfimage = PdfImage(xobj)
                    pil_img  = pdfimage.as_pil_image()
                except Exception as exc:
                    if verbose:
                        print(f"  Page {page_num:>3} | {name:<8}  ⚠  skipped ({exc})")
                    continue

                orig_w, orig_h = pil_img.size

                # ── optional downsampling ─────────────────────────────────────
                if max_dpi:
                    mb = page.mediabox
                    page_w_in = float(mb[2] - mb[0]) / 72
                    page_h_in = float(mb[3] - mb[1]) / 72
                    x_dpi = orig_w / page_w_in if page_w_in > 0 else 0
                    y_dpi = orig_h / page_h_in if page_h_in > 0 else 0
                    if x_dpi > max_dpi or y_dpi > max_dpi:
                        scale = min(
                            max_dpi / x_dpi if x_dpi > 0 else 1,
                            max_dpi / y_dpi if y_dpi > 0 else 1,
                            1.0,
                        )
                        pil_img = pil_img.resize(
                            (max(1, int(orig_w * scale)), max(1, int(orig_h * scale))),
                            Image.LANCZOS,
                        )

                if pil_img.mode not in ("RGB", "L"):
                    pil_img = pil_img.convert("RGB")

                buf = io.BytesIO()
                pil_img.save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
                new_bytes = buf.getvalue()

                try:
                    orig_size = len(bytes(xobj.read_raw_bytes()))
                except Exception:
                    orig_size = 0

                if orig_size and len(new_bytes) >= orig_size:
                    continue   # already optimal at this quality

                xobj.write(new_bytes, filter=Name.DCTDecode)
                compressed_images += 1

                if verbose:
                    saving = (1 - len(new_bytes) / orig_size) * 100 if orig_size else 0
                    print(
                        f"  Page {page_num:>3} | {name:<8} "
                        f"{orig_w}×{orig_h}  "
                        f"{orig_size/1024:>7.1f} KB → "
                        f"{len(new_bytes)/1024:>7.1f} KB  "
                        f"({saving:.0f}% smaller)"
                    )

        pdf.save(output_path, compress_streams=True)

    in_size  = os.path.getsize(input_path)
    out_size = os.path.getsize(output_path)
    return {
        "total_images":       total_images,
        "compressed_images":  compressed_images,
        "input_size_kb":      in_size  / 1024,
        "output_size_kb":     out_size / 1024,
        "overall_saving_pct": (1 - out_size / in_size) * 100 if in_size else 0,
    }


def compress_pdf(
    input_path: str,
    output_path: str,
    jpeg_quality: int = 75,
    max_dpi: int | None = None,
    max_size_mb: float | None = 7.0,
) -> dict:
    """
    Compress a PDF, auto-reducing quality/DPI if the result exceeds max_size_mb.
    """
    max_size_bytes = int(max_size_mb * 1024 * 1024) if max_size_mb else None

    # ── initial pass (verbose) ────────────────────────────────────────────────
    print(f"  [Pass 1]  quality={jpeg_quality}  max_dpi={max_dpi or 'none'}")
    stats = _compress_once(input_path, output_path, jpeg_quality, max_dpi, verbose=True)

    if not max_size_bytes:
        return stats

    out_bytes = int(stats["output_size_kb"] * 1024)
    if out_bytes <= max_size_bytes:
        return stats

    # ── auto-reduction loop ───────────────────────────────────────────────────
    # Build a combined ladder: first reduce quality, then also reduce DPI
    attempts = []
    for q in QUALITY_LADDER:
        if q < jpeg_quality:                     # only go lower than starting q
            attempts.append((q, max_dpi))
    for dpi in DPI_LADDER:
        for q in QUALITY_LADDER:
            attempts.append((q, dpi))

    seen = set()
    for q, dpi in attempts:
        key = (q, dpi)
        if key in seen:
            continue
        seen.add(key)

        print(
            f"\n  ⚠  Output is {out_bytes/1024/1024:.2f} MB — "
            f"target is {max_size_mb} MB. Retrying…"
        )
        print(f"  [Retry]   quality={q}  max_dpi={dpi or 'none'}")
        stats = _compress_once(input_path, output_path, q, dpi, verbose=False)
        out_bytes = int(stats["output_size_kb"] * 1024)
        print(f"            → {out_bytes/1024/1024:.2f} MB")

        if out_bytes <= max_size_bytes:
            # Report the final settings used
            stats["final_quality"] = q
            stats["final_max_dpi"] = dpi
            return stats

    # Exhausted all options
    print(
        f"\n  ⚠  Could not compress below {max_size_mb} MB. "
        f"Best achieved: {out_bytes/1024/1024:.2f} MB"
    )
    stats["final_quality"] = q
    stats["final_max_dpi"] = dpi
    return stats


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Compress image-heavy PDFs locally with an optional size cap.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input",  help="Path to the source PDF")
    parser.add_argument("-o", "--output", default=None,
                        help="Output path (default: input_compressed.pdf)")
    parser.add_argument("-q", "--quality", type=int, default=75,
                        help="Starting JPEG quality 1-95 (default: 75).")
    parser.add_argument("--max-dpi", type=int, default=None,
                        help="Downsample images above this DPI.")
    parser.add_argument("--max-size", type=float, default=6.0, metavar="MB",
                        help="Target output size cap in MB (default: 7). "
                             "Script auto-reduces quality until it fits.")
    parser.add_argument("--no-size-cap", action="store_true",
                        help="Disable the size cap entirely.")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}")
        sys.exit(1)

    output_path = args.output or str(
        Path(args.input).with_stem(Path(args.input).stem + "_compressed")
    )
    quality   = max(1, min(95, args.quality))
    max_size  = None if args.no_size_cap else args.max_size

    print(f"\n📄  Input    : {args.input}")
    print(f"💾  Output   : {output_path}")
    print(f"🎨  Quality  : {quality}  |  Max DPI: {args.max_dpi or 'no limit'}")
    print(f"📏  Size cap : {'disabled' if max_size is None else f'{max_size} MB (UKVCAS ILR limit)'}\n")

    stats = compress_pdf(args.input, output_path, quality, args.max_dpi, max_size)

    final_q   = stats.get("final_quality", quality)
    final_dpi = stats.get("final_max_dpi", args.max_dpi)

    print("\n── Summary ──────────────────────────────────────────────────────────")
    print(f"  Images found      : {stats['total_images']}")
    print(f"  Images compressed : {stats['compressed_images']}")
    print(f"  Input size        : {stats['input_size_kb']/1024:.2f} MB  ({stats['input_size_kb']:.1f} KB)")
    print(f"  Output size       : {stats['output_size_kb']/1024:.2f} MB  ({stats['output_size_kb']:.1f} KB)")
    print(f"  Overall saving    : {stats['overall_saving_pct']:.1f}%")
    if stats.get("final_quality"):
        print(f"  Final settings    : quality={final_q}  max_dpi={final_dpi or 'none'}")
    print(f"\n✅  Saved to: {output_path}\n")


if __name__ == "__main__":
    main()
