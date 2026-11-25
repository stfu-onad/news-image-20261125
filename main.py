"""Publish the finished front page for 25 November 2026.

This file is the whole entry program for the news-image-20261125
bounty. It does not draw anything and it does not fetch anything.
The finished picture already exists next to this file as entry.png:
a one-page newspaper front page that sums up Wednesday 25 November
2026 in a single image. All this program has to do is prove that
the shipped picture is a well-formed PNG inside the bounty limits,
then place an exact copy of it where the grader looks for it.

The four stories on the page are the ones that defined the day.
Ukraine's president confirmed two sinkings at sea, one cargo ship
in the Gulf of Finland and one warship off Benghazi, while Moscow
called the attacks terrorism. The COP31 climate talks in Antalya
collapsed without a deal after oil and gas producers blocked any
fossil-fuel phaseout wording. Houthi strikes hit the tallest tower
in Riyadh, wounding eleven people, as the rebels pushed towards
Aden. And in Washington, Donald Trump gave Rudy Giuliani the Medal
of Freedom. A ticker along the bottom carries the rest of the day:
Sarkozy ordered to trial, NATO jets for Poland, tankers hit in the
Strait of Hormuz, the Gaza death toll, a new estimate of Russian
losses, and England's win in the second T20.

The hero picture in the middle of the page -- a burning cargo ship
at dusk, a drone overhead, a warship going down in the distance --
was made during the build session and carries no words of its own.
Every headline, the date line and the captions were drawn on top
of it afterwards with PIL and DejaVu fonts, so the text stays sharp
instead of smearing the way text inside a generated picture does.

Running this program is deliberately boring, and that is the point.
It reads the shipped bytes, walks the PNG chunk by chunk, checks
the signature, the header, the size, the dimensions and the chunk
checksums, and only then writes those exact same bytes out to the
output directory. No timestamps are stamped in, no random numbers
are used, nothing is downloaded, so running it twice gives the
grader two identical files. If any check fails the program stops
with a clear error instead of handing over a broken picture.
"""

import hashlib
import os
import struct
import sys
import zlib
from pathlib import Path

# Name of the shipped picture, sitting next to this file.
IMAGE_NAME = "entry.png"

# Bounty limits for the shipped picture. The page is 1024 by 1024
# pixels and well under a megabyte, so both limits have headroom.
MAX_BYTES = 1_048_576
MAX_SIDE_PIXELS = 1024
MAX_TOTAL_PIXELS = MAX_SIDE_PIXELS * MAX_SIDE_PIXELS

# Every PNG file starts with these eight bytes, no exceptions.
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# A chunk is: 4 bytes of length, 4 bytes of type, the data itself,
# then 4 bytes of CRC. So the overhead around the data is 12 bytes.
CHUNK_OVERHEAD = 12
IHDR_DATA_LENGTH = 13

# Colour type numbers from the PNG specification, with the plain
# English name each one means. The shipped page is truecolour.
COLOUR_TYPE_NAMES = {
    0: "greyscale",
    2: "truecolour",
    3: "indexed-colour",
    4: "greyscale with alpha",
    6: "truecolour with alpha",
}

# Bit depths the PNG specification allows at all. Which of them a
# given colour type may use is checked separately, below.
ALLOWED_BIT_DEPTHS = (1, 2, 4, 8, 16)

# Bit depths each colour type is allowed to use, per the spec.
# Keeping this table here means a corrupt header that claims, say,
# 4-bit truecolour is caught instead of slipping through.
BIT_DEPTHS_BY_COLOUR_TYPE = {
    0: (1, 2, 4, 8, 16),
    2: (8, 16),
    3: (1, 2, 4, 8),
    4: (8, 16),
    6: (8, 16),
}


class ImageProblem(ValueError):
    """Raised when the shipped picture fails any validation check."""

    pass


def describe_colour_type(code):
    """Return a short human name for a PNG colour type number."""
    return COLOUR_TYPE_NAMES.get(code, "unknown colour type %d" % code)


def check_signature(blob, path):
    """Reject anything that does not start with the PNG signature."""
    if len(blob) < len(PNG_SIGNATURE):
        raise ImageProblem(
            "shipped file too short to be a PNG (%d bytes): %s"
            % (len(blob), path)
        )
    if blob[:8] != PNG_SIGNATURE:
        raise ImageProblem(
            "shipped file is not a PNG (bad signature): %s" % path
        )


def check_file_size(blob, path):
    """Reject a shipped picture over the one-megabyte bounty limit."""
    if len(blob) > MAX_BYTES:
        raise ImageProblem(
            "shipped file over 1 MiB limit: %d bytes: %s"
            % (len(blob), path)
        )
    if len(blob) < 8 + CHUNK_OVERHEAD + IHDR_DATA_LENGTH:
        raise ImageProblem(
            "shipped file too short to hold a PNG header: %s" % path
        )


def parse_header(blob, path):
    """Read and validate the IHDR chunk at the start of the file.

    Returns a dict with width, height, bit depth, colour type and
    the compression, filter and interlace bytes. The IHDR chunk
    must be the first chunk, must be exactly 13 bytes of data, and
    must describe a picture inside the dimension limits.
    """
    first_length = struct.unpack(">I", blob[8:12])[0]
    first_type = blob[12:16]
    if first_type != b"IHDR":
        raise ImageProblem(
            "first PNG chunk is %r, expected IHDR: %s"
            % (first_type, path)
        )
    if first_length != IHDR_DATA_LENGTH:
        raise ImageProblem(
            "IHDR chunk has %d bytes of data, expected 13: %s"
            % (first_length, path)
        )
    data = blob[16:29]
    width, height = struct.unpack(">II", data[0:8])
    bit_depth = data[8]
    colour_type = data[9]
    compression = data[10]
    filter_method = data[11]
    interlace = data[12]
    if width == 0 or height == 0:
        raise ImageProblem(
            "shipped image has a zero dimension: %dx%d: %s"
            % (width, height, path)
        )
    if width > MAX_SIDE_PIXELS or height > MAX_SIDE_PIXELS:
        raise ImageProblem(
            "shipped image over 1024x1024: %dx%d: %s"
            % (width, height, path)
        )
    if width * height > MAX_TOTAL_PIXELS:
        raise ImageProblem(
            "shipped image has too many pixels: %dx%d: %s"
            % (width, height, path)
        )
    if bit_depth not in ALLOWED_BIT_DEPTHS:
        raise ImageProblem(
            "shipped image has impossible bit depth %d: %s"
            % (bit_depth, path)
        )
    if colour_type not in COLOUR_TYPE_NAMES:
        raise ImageProblem(
            "shipped image has unknown colour type %d: %s"
            % (colour_type, path)
        )
    allowed = BIT_DEPTHS_BY_COLOUR_TYPE[colour_type]
    if bit_depth not in allowed:
        raise ImageProblem(
            "bit depth %d is not allowed for %s images: %s"
            % (bit_depth, describe_colour_type(colour_type), path)
        )
    if compression != 0:
        raise ImageProblem(
            "shipped image uses unknown compression method %d: %s"
            % (compression, path)
        )
    if filter_method != 0:
        raise ImageProblem(
            "shipped image uses unknown filter method %d: %s"
            % (filter_method, path)
        )
    if interlace not in (0, 1):
        raise ImageProblem(
            "shipped image uses unknown interlace method %d: %s"
            % (interlace, path)
        )
    return {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "colour_type": colour_type,
        "compression": compression,
        "filter_method": filter_method,
        "interlace": interlace,
    }


def walk_chunks(blob, path):
    """Walk every chunk, checking lengths, types and CRCs.

    Returns the list of chunk type names in file order. A chunk
    must fit inside the file, its stored CRC must match the CRC
    computed over its type plus its data, and the file must end
    with exactly one IEND chunk and nothing after it. The walk
    also insists on at least one IDAT chunk, because a PNG with
    no image data is not a picture at all.
    """
    types = []
    offset = 8
    seen_idat = False
    seen_iend = False
    while offset < len(blob):
        if seen_iend:
            raise ImageProblem(
                "trailing bytes after IEND chunk: %s" % path
            )
        if offset + 8 > len(blob):
            raise ImageProblem(
                "truncated chunk header at byte %d: %s" % (offset, path)
            )
        length = struct.unpack(">I", blob[offset:offset + 4])[0]
        chunk_type = blob[offset + 4:offset + 8]
        try:
            type_name = chunk_type.decode("ascii")
        except UnicodeDecodeError:
            raise ImageProblem(
                "chunk at byte %d has a non-ASCII type: %s"
                % (offset, path)
            )
        if not type_name.isalpha() or not type_name.isascii():
            raise ImageProblem(
                "chunk at byte %d has a bad type %r: %s"
                % (offset, type_name, path)
            )
        end = offset + CHUNK_OVERHEAD + length
        if end > len(blob):
            raise ImageProblem(
                "chunk %s at byte %d claims %d bytes but the file "
                "ends first: %s" % (type_name, offset, length, path)
            )
        data = blob[offset + 8:offset + 8 + length]
        stored_crc = struct.unpack(
            ">I", blob[offset + 8 + length:end]
        )[0]
        actual_crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        if stored_crc != actual_crc:
            raise ImageProblem(
                "chunk %s at byte %d has a bad CRC: %s"
                % (type_name, offset, path)
            )
        types.append(type_name)
        if type_name == "IDAT":
            seen_idat = True
        if type_name == "IEND":
            if length != 0:
                raise ImageProblem(
                    "IEND chunk must be empty, has %d bytes: %s"
                    % (length, path)
                )
            seen_iend = True
        offset = end
    if not seen_iend:
        raise ImageProblem("shipped PNG has no IEND chunk: %s" % path)
    if not seen_idat:
        raise ImageProblem("shipped PNG has no IDAT chunk: %s" % path)
    if types[0] != "IHDR":
        raise ImageProblem("first chunk is not IHDR: %s" % path)
    return types


def check_palette_present(blob, chunk_types, header, path):
    """Check the PLTE rule for indexed-colour pictures.

    An indexed-colour PNG (colour type 3) must carry a PLTE chunk
    before its first IDAT chunk, because without the palette the
    pixel values in IDAT would be meaningless numbers. Other
    colour types may carry a PLTE chunk as a suggested palette,
    but they do not need one, so this check only complains when
    an indexed picture is missing it, or when a PLTE chunk turns
    up after the image data has already started, which the spec
    forbids. A PLTE chunk must also hold a whole number of RGB
    triples: its length has to be divisible by three.
    """
    if "PLTE" not in chunk_types:
        if header["colour_type"] == 3:
            raise ImageProblem(
                "indexed-colour image has no PLTE chunk: %s" % path
            )
        return
    if chunk_types.index("PLTE") > chunk_types.index("IDAT"):
        raise ImageProblem(
            "PLTE chunk comes after the first IDAT chunk: %s" % path
        )
    offset = 8
    while offset < len(blob):
        length = struct.unpack(">I", blob[offset:offset + 4])[0]
        chunk_type = blob[offset + 4:offset + 8]
        if chunk_type == b"PLTE":
            if length % 3 != 0:
                raise ImageProblem(
                    "PLTE chunk length %d is not a whole number of "
                    "RGB entries: %s" % (length, path)
                )
            if length == 0 or length > 768:
                raise ImageProblem(
                    "PLTE chunk has an impossible length %d: %s"
                    % (length, path)
                )
            return
        offset += CHUNK_OVERHEAD + length


def validate_image(path):
    """Read the shipped picture and run every check on it.

    Returns a dict describing the picture: its byte size, its
    dimensions, its bit depth and colour type, and the chunk
    types found in it, in order. Nothing here changes the file;
    this only reads it and complains if anything looks wrong.
    """
    if not path.is_file():
        raise FileNotFoundError("shipped image missing: %s" % path)
    blob = path.read_bytes()
    check_signature(blob, path)
    check_file_size(blob, path)
    header = parse_header(blob, path)
    chunk_types = walk_chunks(blob, path)
    check_palette_present(blob, chunk_types, header, path)
    return {
        "blob": blob,
        "size": len(blob),
        "width": header["width"],
        "height": header["height"],
        "bit_depth": header["bit_depth"],
        "colour_type": header["colour_type"],
        "chunk_types": chunk_types,
        "chunk_count": len(chunk_types),
    }


def resolve_output_dir():
    """Work out where the grader wants the finished picture.

    The bounty runner sets MAKEFUN_OUTPUT_DIR; without it the
    historical default is /output. Either way the directory is
    created if it is not there yet, so the copy never fails for
    want of a folder.
    """
    raw = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    target_dir = Path(raw)
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def sha256_hex(blob):
    """Return the hex SHA-256 digest of a block of bytes."""
    return hashlib.sha256(blob).hexdigest()


def publish_copy(info, source, target):
    """Write the validated bytes out and prove the copy matches.

    The target is written from the same bytes object that was
    validated, then read back and compared byte for byte, and
    its digest is compared too. Copying fixed shipped bytes with
    no timestamps and no randomness in the path is deterministic
    by construction, so a second run must produce identical bytes.
    """
    blob = info["blob"]
    target.write_bytes(blob)
    copied = target.read_bytes()
    if copied != blob:
        raise ImageProblem(
            "copied image differs from shipped image: %s" % target
        )
    if sha256_hex(copied) != sha256_hex(blob):
        raise ImageProblem(
            "copied image digest differs from shipped image: %s"
            % target
        )
    return sha256_hex(blob)


def report(info, target, digest):
    """Print one line summarising what was published, and how."""
    print(
        "wrote %s (%d bytes, %dx%d, %d-bit %s, %d chunks, "
        "sha256 %s)"
        % (
            target,
            info["size"],
            info["width"],
            info["height"],
            info["bit_depth"],
            describe_colour_type(info["colour_type"]),
            info["chunk_count"],
            digest,
        )
    )


def main(argv=None):
    """Validate the shipped picture and publish an exact copy.

    Returns 0 on success. Any validation failure raises an
    exception, which Python reports and turns into a non-zero
    exit code, so a broken picture can never pass silently.
    """
    here = Path(__file__).resolve().parent
    source = here / IMAGE_NAME
    info = validate_image(source)
    target_dir = resolve_output_dir()
    target = target_dir / IMAGE_NAME
    digest = publish_copy(info, source, target)
    report(info, target, digest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
