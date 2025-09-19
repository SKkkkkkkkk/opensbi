#!/usr/bin/env python3
import argparse
import binascii
import struct
import hashlib
import os
from ecdsa import SigningKey
from ecdsa.util import sigencode_string

def generate_signature_for_data(data, private_key_file):
    """
    Generate ECC signature for data using private key
    Returns 64-byte signature or None if signing fails
    """
    if not os.path.exists(private_key_file):
        print(f"Error: Private key file '{private_key_file}' not found")
        return None
    
    try:
        # Read private key
        with open(private_key_file, "rb") as f:
            key_pem = f.read()
        
        # Create signing key from private key
        key = SigningKey.from_pem(key_pem)
        
        # Generate signature using SHA256 hash and string encoding
        signature = key.sign_deterministic(data, hashfunc=hashlib.sha256, sigencode=sigencode_string)
        
        # Ensure signature is exactly 64 bytes (pad or truncate if necessary)
        if len(signature) < 64:
            signature = signature + b'\x00' * (64 - len(signature))
        elif len(signature) > 64:
            signature = signature[:64]
            
        return signature
        
    except Exception as e:
        print(f"Error generating signature: {e}")
        return None


def patch_binary_payload(bin_filename, private_key_file=None, sign_only=False, entrypoint=None):
    """
    Patch image_size field, entrypoint, and optionally generate signature for image_hdr_t in place in binary
    
    Args:
        bin_filename: Path to the binary image file
        private_key_file: Optional path to private key file for signature generation
        sign_only: If True, only update signature field (don't update image_size or entrypoint)
        entrypoint: Optional new entrypoint address to set in the header
        
    Raise exception if binary is not a supported type
    """
    IMAGE_HDR_SIZE_BYTES = 96  # Updated to include 64-byte ECC signature
    IMAGE_HDR_MAGIC = 0x9ca3
    IMAGE_HDR_VERSION = 1

    with open(bin_filename, "rb") as f:
        image_hdr = f.read(IMAGE_HDR_SIZE_BYTES)
        data = f.read()

    image_magic, image_hdr_version = struct.unpack("<HH", image_hdr[0:4])

    if image_magic != IMAGE_HDR_MAGIC:
        raise Exception(
            "Unsupported Binary Type. Expected 0x{:02x} Got 0x{:02x}".format(
                IMAGE_HDR_MAGIC, image_magic
            )
        )

    if image_hdr_version != IMAGE_HDR_VERSION:
        raise Exception(
            "Unsupported Image Header Version. Expected 0x{:02x} Got 0x{:02x}".format(
                IMAGE_HDR_VERSION, image_hdr_version
            )
        )

    data_size = len(data)
    
    # Generate signature for the image data if private key is provided
    signature = None
    if private_key_file:
        print(f"Generating signature using private key: {private_key_file}")
        signature = generate_signature_for_data(data, private_key_file)
        if signature:
            print(f"Signature generated successfully (64 bytes)")
        else:
            print("Warning: Failed to generate signature, signature field will remain unchanged")

    # Prepare updates
    image_hdr_data_size = struct.pack("<L", data_size)
    
    print(f"Patching binary '{bin_filename}':")
    print(f"  Data size: {data_size} bytes")
    if entrypoint is not None:
        print(f"  Entry point: 0x{entrypoint:016x}")
    if signature:
        print(f"  Signature: {signature[:8].hex()}... (64 bytes total)")
    
    with open(bin_filename, "r+b") as f:
        # Update image_size field (unless sign_only mode)
        if not sign_only:
            f.seek(4)  # Seek to beginning of "uint32_t image_size"
            f.write(image_hdr_data_size)
            print("  Image size field updated")
        
        # Update entrypoint field if provided (unless sign_only mode)
        if not sign_only and entrypoint is not None:
            f.seek(8)  # Seek to beginning of "uintptr_t image_entrypoint"
            entrypoint_bytes = struct.pack("<Q", entrypoint)  # 64-bit little-endian
            f.write(entrypoint_bytes)
            print("  Entry point field updated")
        
        # Update signature field if signature was generated
        if signature:
            f.seek(24)  # Seek to beginning of signature field (offset 24)
            f.write(signature)
            print("  Signature field updated in binary")


def add_image_header(bin_filename, output_filename=None, entrypoint=0, git_sha="", private_key_file=None):
    """
    Add image header to a binary file that doesn't have one
    
    Args:
        bin_filename: Path to the binary file without header
        output_filename: Optional output filename (defaults to bin_filename with .img extension)
        entrypoint: Entry point address for the binary
        git_sha: Git SHA string (up to 7 characters, null-terminated within 8 bytes)
        private_key_file: Optional path to private key file for signature generation
    """
    IMAGE_HDR_SIZE_BYTES = 96
    IMAGE_HDR_MAGIC = 0x9ca3
    IMAGE_HDR_VERSION = 1
    
    # Read the original binary data
    with open(bin_filename, "rb") as f:
        data = f.read()
    
    data_size = len(data)
    
    # Prepare git_sha (truncate to max 7 chars to ensure null termination)
    git_sha_bytes = git_sha.encode('ascii')[:7]  # Max 7 chars to leave room for null terminator
    git_sha_bytes = git_sha_bytes.ljust(8, b'\x00')  # Pad to 8 bytes with null bytes
    
    # Generate signature for the data if private key is provided
    signature = b'\x00' * 64  # Default to zeros
    if private_key_file:
        print(f"Generating signature using private key: {private_key_file}")
        signature = generate_signature_for_data(data, private_key_file)
        if signature:
            print(f"Signature generated successfully (64 bytes)")
        else:
            print("Warning: Failed to generate signature, using zero signature")
            signature = b'\x00' * 64
    
    # Build the image header
    header = struct.pack("<HHLQ", IMAGE_HDR_MAGIC, IMAGE_HDR_VERSION, data_size, entrypoint)
    header += git_sha_bytes
    header += signature
    
    # Pad header to ensure it's exactly 96 bytes
    if len(header) < IMAGE_HDR_SIZE_BYTES:
        header += b'\x00' * (IMAGE_HDR_SIZE_BYTES - len(header))
    
    # Determine output filename
    if output_filename is None:
        base, ext = os.path.splitext(bin_filename)
        output_filename = base + ".img"
    
    # Write the new image file with header + data
    with open(output_filename, "wb") as f:
        f.write(header)
        f.write(data)
    
    print(f"Image header added successfully:")
    print(f"  Input file: {bin_filename}")
    print(f"  Output file: {output_filename}")
    print(f"  Data size: {data_size} bytes")
    print(f"  Entry point: 0x{entrypoint:016x}")
    print(f"  Git SHA: {git_sha}")
    if private_key_file:
        zero_signature = b'\x00' * 64
        print(f"  Signature: {'Generated' if signature != zero_signature else 'Zero (failed to generate)'}")
    print(f"  Total file size: {IMAGE_HDR_SIZE_BYTES + data_size} bytes")


def display_image_header(bin_filename):
    """
    Display the complete header information from the image file
    """
    IMAGE_HDR_SIZE_BYTES = 96  # Updated to include 64-byte ECC signature
    IMAGE_HDR_MAGIC = 0x9ca3
    IMAGE_HDR_VERSION = 1

    try:
        with open(bin_filename, "rb") as f:
            # First read just enough to check the magic number
            magic_bytes = f.read(2)
            if len(magic_bytes) < 2:
                print(f"Error: File '{bin_filename}' is too small to contain a valid header")
                return
                
            image_magic = struct.unpack("<H", magic_bytes)[0]
            
            # Validate magic number before proceeding
            if image_magic != IMAGE_HDR_MAGIC:
                print(f"Error: Invalid magic number 0x{image_magic:04x}, expected 0x{IMAGE_HDR_MAGIC:04x}")
                print(f"File '{bin_filename}' is not a valid image file")
                return
                
            # Rewind and read the full header
            f.seek(0)
            image_hdr = f.read(IMAGE_HDR_SIZE_BYTES)
            data = f.read()

        # Parse according to image.h structure:
        # typedef struct __attribute__((packed, aligned(16))) {
        #     uint16_t image_hdr_magic;
        #     uint16_t image_hdr_version;
        #     uint32_t image_size;
        #     uintptr_t image_entrypoint; // implies the start address of the image payload
        #     char git_sha[8];
        #     uint8_t signature[64]; // ecc secp256k1 signature
        # } image_hdr_t;
        
        image_magic, image_hdr_version, data_size, image_entrypoint = struct.unpack("<HHLQ", image_hdr[0:16])
        git_sha = image_hdr[16:24]
        signature = image_hdr[24:88]  # 64 bytes signature
        
        # Verify header version
        if image_hdr_version != IMAGE_HDR_VERSION:
            print(f"Warning: Unexpected header version {image_hdr_version}, expected {IMAGE_HDR_VERSION}")

        print("=== Image Header Information ===")
        print(f"Magic:          0x{image_magic:04x}")
        print(f"Header Version: {image_hdr_version}")
        print(f"Data Size:      {data_size} bytes")
        print(f"Entry Point:    0x{image_entrypoint:016x}")
        
        # Convert binary git_sha to string, stopping at null terminator if present
        git_sha_str = ""
        for b in git_sha:
            if b == 0:
                break
            git_sha_str += chr(b)
            
        print(f"Git SHA:        {git_sha_str}")
        
        # Display signature info (first 8 bytes for brevity)
        sig_preview = signature[:8] if len(signature) >= 8 else signature
        sig_hex = ' '.join(f'{b:02x}' for b in sig_preview)
        print(f"Signature:      {sig_hex}... (64 bytes total)")
        print(f"Total File Size: {len(image_hdr) + len(data)} bytes")
    
    except Exception as e:
        print(f"Error reading image header: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Patch image header and optionally generate ECC signature

Examples:
  %(prog)s firmware.bin                           # Patch image size only
  %(prog)s firmware.bin -k private_key.pem       # Patch image size and generate signature
  %(prog)s firmware.bin --entrypoint 0x40020000  # Patch image size and update entrypoint
  %(prog)s firmware.bin -k private_key.pem -s    # Only generate and update signature
  %(prog)s firmware.bin -i                       # Display image header information
  %(prog)s raw_binary.bin --add-header --entrypoint 0x80000000 --git-sha abcd123 -k private_key.pem  # Add header to raw binary
  %(prog)s raw_binary.bin --add-header -o output.img  # Add header and save to specific output file
""", 
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("bin", action="store", help="Binary image file")
    parser.add_argument("-i", "--info", action="store_true", help="Display image header information")
    parser.add_argument("-k", "--key", action="store", metavar="PRIVATE_KEY", 
                        help="Private key file for signature generation (PEM format)")
    parser.add_argument("-s", "--sign-only", action="store_true", 
                        help="Only generate and update signature (requires -k)")
    parser.add_argument("--add-header", action="store_true", 
                        help="Add image header to a binary file that doesn't have one")
    parser.add_argument("-o", "--output", action="store", metavar="OUTPUT_FILE",
                        help="Output filename (only used with --add-header)")
    parser.add_argument("--entrypoint", action="store", type=lambda x: int(x, 0), default=None,
                        help="Entry point address for the binary (hex or decimal)")
    parser.add_argument("--git-sha", action="store", default="", metavar="SHA",
                        help="Git SHA string (up to 7 characters, null-terminated, default: empty)")
    args = parser.parse_args()

    if args.info:
        display_image_header(args.bin)
    elif args.add_header:
        # Add header mode
        entrypoint = args.entrypoint if args.entrypoint is not None else 0
        add_image_header(args.bin, args.output, entrypoint, args.git_sha, args.key)
    elif args.sign_only:
        if not args.key:
            print("Error: --sign-only requires --key argument")
            exit(1)
        # For sign-only mode, we still call patch_binary_payload but it will only update signature
        patch_binary_payload(args.bin, args.key, sign_only=True, entrypoint=args.entrypoint)
    else:
        patch_binary_payload(args.bin, args.key, entrypoint=args.entrypoint)
