#!/usr/bin/env python3
"""
onepdfshrink - A Python script to reduce PDF file size

This script compresses PDF files by removing metadata, optimizing images,
and applying various compression techniques.
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import PyPDF2
except ImportError:
    print("Error: PyPDF2 is required. Install it with: pip install PyPDF2")
    sys.exit(1)

try:
    from PIL import Image
    import io
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL/Pillow not available. Image compression will be limited.")
    print("Install with: pip install Pillow")


def get_file_size(file_path):
    """Get file size in bytes."""
    return os.path.getsize(file_path)


def format_file_size(size_bytes):
    """Convert bytes to human readable format."""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f}{size_names[i]}"


def decode_pdf_image(obj):
    """
    Decode image data from PDF object.
    
    Args:
        obj: PDF image object
    
    Returns:
        bytes: Decoded image data or None if decoding fails
    """
    try:
        # Get filter information
        filters = obj.get('/Filter')
        if filters is None:
            return obj._data
        
        # Handle single filter or array of filters
        if not isinstance(filters, list):
            filters = [filters]
        
        data = obj._data
        
        for filter_type in filters:
            filter_name = str(filter_type)
            
            if '/FlateDecode' in filter_name:
                import zlib
                data = zlib.decompress(data)
            elif '/DCTDecode' in filter_name:
                # JPEG data - already compressed
                return data
            elif '/CCITTFaxDecode' in filter_name:
                # TIFF/Fax compression - skip for now
                return None
            elif '/JBIG2Decode' in filter_name:
                # JBIG2 compression - skip for now
                return None
            elif '/JPXDecode' in filter_name:
                # JPEG2000 compression - skip for now
                return None
        
        return data
        
    except Exception as e:
        return None


def compress_image(image_data, quality=30, max_width=800, max_height=600):
    """
    Compress image data using PIL/Pillow.
    
    Args:
        image_data (bytes): Original image data
        quality (int): JPEG quality (1-100, lower = more compression)
        max_width (int): Maximum width for resizing
        max_height (int): Maximum height for resizing
    
    Returns:
        bytes: Compressed image data
    """
    if not PIL_AVAILABLE or image_data is None:
        return image_data
    
    try:
        # Open image from bytes
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary (for JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background for transparent images
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode in ('RGBA', 'LA'):
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize image if it's too large
        original_size = img.size
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Save compressed image to bytes
        output_buffer = io.BytesIO()
        img.save(output_buffer, format='JPEG', quality=quality, optimize=True)
        compressed_data = output_buffer.getvalue()
        
        # Only return compressed version if it's actually smaller
        if len(compressed_data) < len(image_data):
            return compressed_data
        else:
            return image_data
            
    except Exception as e:
        # Don't print warnings for every failed image - too verbose
        return image_data


def extract_and_compress_images(pdf_reader, pdf_writer, compression_level="medium"):
    """
    Extract images from PDF pages and compress them.
    
    Args:
        pdf_reader: PyPDF2 PdfReader object
        pdf_writer: PyPDF2 PdfWriter object
        compression_level (str): Compression level
    """
    quality_map = {
        "low": 70,
        "medium": 50,
        "high": 20  # More aggressive compression
    }
    
    size_map = {
        "low": (1200, 900),
        "medium": (800, 600),
        "high": (400, 300)  # More aggressive resizing
    }
    
    quality = quality_map.get(compression_level, 50)
    max_width, max_height = size_map.get(compression_level, (800, 600))
    
    images_processed = 0
    images_compressed = 0
    
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        
        # Process images in the page
        if '/Resources' in page and '/XObject' in page['/Resources']:
            try:
                xobjects = page['/Resources']['/XObject']
                for obj_name in list(xobjects.keys()):
                    obj = xobjects[obj_name]
                    if obj.get('/Subtype') == '/Image':
                        try:
                            images_processed += 1
                            
                            # Remove the image if --remove-images is set
                            if args.remove_images:
                                del xobjects[obj_name]
                                continue
                            
                            # Decode image data properly
                            image_data = decode_pdf_image(obj)
                            
                            if image_data is None:
                                continue
                            
                            # Compress the image
                            compressed_data = compress_image(
                                image_data, quality, max_width, max_height
                            )
                            
                            # Replace image data if compression was successful
                            if compressed_data != image_data and compressed_data is not None and PIL_AVAILABLE:
                                # Update the PDF object with compressed data
                                obj._data = compressed_data
                                obj[PyPDF2.generic.NameObject('/Length')] = PyPDF2.generic.NumberObject(len(compressed_data))
                                obj[PyPDF2.generic.NameObject('/Filter')] = PyPDF2.generic.NameObject('/DCTDecode')
                                obj[PyPDF2.generic.NameObject('/ColorSpace')] = PyPDF2.generic.NameObject('/DeviceRGB')
                                
                                # Remove other image-specific parameters that might conflict
                                for key in ['/DecodeParms', '/SMask', '/Mask']:
                                    if key in obj:
                                        del obj[key]
                                
                                images_compressed += 1
                                
                        except Exception as e:
                            # Skip problematic images
                            continue
            except Exception as e:
                # Skip problematic pages
                continue
        
        pdf_writer.add_page(page)
    
    if images_processed > 0:
        print(f"Processed {images_processed} images, compressed {images_compressed}")


def compress_pdf(input_path, output_path, compression_level="medium", remove_images=False, chunk_size=None):
    """
    Compress PDF file using PyPDF2 with aggressive image compression.
    
    Args:
        input_path (str): Path to input PDF file
        output_path (str): Path to output PDF file
        compression_level (str): Compression level ("low", "medium", "high")
        remove_images (bool): Flag to remove all images from the PDF
        chunk_size (float): Size in MB to split output into chunks
    """
    global args
    args = argparse.Namespace(remove_images=remove_images, chunk_size=chunk_size)
    
    try:
        with open(input_path, 'rb') as input_file:
            pdf_reader = PyPDF2.PdfReader(input_file)
            pdf_writer = PyPDF2.PdfWriter()
            
            # Extract and compress/remove images, then add pages
            extract_and_compress_images(pdf_reader, pdf_writer, compression_level)
            
            # Remove metadata for all compression levels
            pdf_writer.add_metadata({})
            
            # Apply additional compression
            if hasattr(pdf_writer, 'compress_identical_objects'):
                pdf_writer.compress_identical_objects()
            
            # Write compressed PDF
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            # If chunking is enabled, split the output file
            if chunk_size:
                split_pdf_by_size(str(output_path), chunk_size)
                
            return True
            
    except Exception as e:
        print(f"Error compressing PDF: {e}")
        return False


def split_pdf_by_size(input_path, size_mb):
    """
    Split a PDF file into smaller chunks based on file size.
    
    Args:
        input_path (str): Path to the input PDF file.
        size_mb (float): Desired size of each chunk in megabytes.
    """
    size_bytes = size_mb * 1024 * 1024
    
    try:
        with open(input_path, 'rb') as input_file:
            pdf_reader = PyPDF2.PdfReader(input_file)
            total_pages = len(pdf_reader.pages)
            
            current_chunk_writer = PyPDF2.PdfWriter()
            chunk_number = 1
            temp_filename = None
            pages_in_current_chunk = 0
            
            for page_number in range(total_pages):
                page = pdf_reader.pages[page_number]
                
                # Create a test writer with the current page added
                test_writer = PyPDF2.PdfWriter()
                
                # Add all pages currently in the chunk
                for i in range(pages_in_current_chunk):
                    test_writer.add_page(pdf_reader.pages[page_number - pages_in_current_chunk + i])
                
                # Add the new page
                test_writer.add_page(page)
                
                # Create a temporary file to check the size
                base_path = Path(input_path)
                temp_filename = f"{base_path.stem}_temp_chunk.pdf"
                
                with open(temp_filename, 'wb') as temp_file:
                    test_writer.write(temp_file)
                
                test_size = get_file_size(temp_filename)
                
                # Check if adding this page would exceed the size limit
                if test_size > size_bytes and pages_in_current_chunk > 0:
                    # Write the current chunk without this page
                    chunk_filename = f"{base_path.stem}_part{chunk_number:02d}{base_path.suffix}"
                    
                    chunk_writer = PyPDF2.PdfWriter()
                    for i in range(pages_in_current_chunk):
                        chunk_writer.add_page(pdf_reader.pages[page_number - pages_in_current_chunk + i])
                    
                    with open(chunk_filename, 'wb') as chunk_file:
                        chunk_writer.write(chunk_file)
                    
                    chunk_size = get_file_size(chunk_filename)
                    print(f"Chunk {chunk_number} written to {chunk_filename} ({format_file_size(chunk_size)})")
                    
                    # Start a new chunk with the current page
                    chunk_number += 1
                    pages_in_current_chunk = 1
                    
                else:
                    # Add the page to the current chunk
                    pages_in_current_chunk += 1
                
                # If this is the last page, write the final chunk
                if page_number == total_pages - 1:
                    chunk_filename = f"{base_path.stem}_part{chunk_number:02d}{base_path.suffix}"
                    
                    chunk_writer = PyPDF2.PdfWriter()
                    for i in range(pages_in_current_chunk):
                        chunk_writer.add_page(pdf_reader.pages[page_number - pages_in_current_chunk + 1 + i])
                    
                    with open(chunk_filename, 'wb') as chunk_file:
                        chunk_writer.write(chunk_file)
                    
                    chunk_size = get_file_size(chunk_filename)
                    print(f"Chunk {chunk_number} written to {chunk_filename} ({format_file_size(chunk_size)})")
                
                # Clean up temp file
                if temp_filename and os.path.exists(temp_filename):
                    try:
                        os.remove(temp_filename)
                    except:
                        pass
        
        # Remove the original file after successful splitting only if we created multiple chunks
        if chunk_number > 1:
            os.remove(input_path)
            print(f"Original file removed. Created {chunk_number} chunks.")
        else:
            print(f"File is already smaller than {size_mb}MB, no splitting needed.")
            
    except Exception as e:
        print(f"Error splitting PDF: {e}")
        # Clean up temp file on error
        if temp_filename and os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="Reduce PDF file size by applying compression techniques",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python onepdfshrink.py document.pdf
  python onepdfshrink.py document.pdf -o compressed.pdf
  python onepdfshrink.py document.pdf -c high
  python onepdfshrink.py document.pdf -c low -o output.pdf
  python onepdfshrink.py document.pdf -ri
  python onepdfshrink.py document.pdf -ri -c high
  python onepdfshrink.py document.pdf -s 10
        """
    )
    
    parser.add_argument("input", help="Input PDF file path")
    parser.add_argument("-o", "--output", help="Output PDF file path (default: adds '_compressed' suffix)")
    parser.add_argument("-c", "--compression", 
                       choices=["low", "medium", "high"], 
                       default="medium",
                       help="Compression level (default: medium)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output file if it exists")
    
    parser.add_argument("-ri", "--remove-images", action="store_true",
                       help="Remove all images from the PDF")
    parser.add_argument("-s", "--split-size", type=float, help="Split output into chunks of specified size in MB")
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' does not exist.")
        sys.exit(1)
    
    if not input_path.suffix.lower() == '.pdf':
        print(f"Error: Input file must be a PDF file.")
        sys.exit(1)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        suffix = "_ri_compressed" if args.remove_images else "_compressed"
        output_path = input_path.parent / f"{input_path.stem}{suffix}{input_path.suffix}"
    
    # Check if output file exists
    if output_path.exists() and not args.overwrite:
        response = input(f"Output file '{output_path}' already exists. Overwrite? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Operation cancelled.")
            sys.exit(0)
    
    # Get original file size
    original_size = get_file_size(input_path)
    
    if args.verbose:
        print(f"Input file: {input_path}")
        print(f"Output file: {output_path}")
        print(f"Original size: {format_file_size(original_size)}")
        print(f"Compression level: {args.compression}")
        if args.remove_images:
            print("Removing all images...")
        else:
            print("Compressing...")
    
    # Compress the PDF
    success = compress_pdf(str(input_path), str(output_path), args.compression, args.remove_images, args.split_size)
    
    if success:
        if args.split_size and not output_path.exists():
            # File was split into chunks, calculate total size of all chunks
            chunk_files = list(output_path.parent.glob(f"{output_path.stem}_part*.pdf"))
            compressed_size = sum(get_file_size(chunk) for chunk in chunk_files)
            print(f"✓ PDF processed and split successfully!")
            print(f"Original size: {format_file_size(original_size)}")
            print(f"Total size of chunks: {format_file_size(compressed_size)}")
            print(f"Size reduction: {((original_size - compressed_size) / original_size) * 100:.1f}%")
            print(f"Created {len(chunk_files)} chunks")
        else:
            compressed_size = get_file_size(output_path)
            reduction_percent = ((original_size - compressed_size) / original_size) * 100
            
            print(f"✓ PDF processed successfully!")
            print(f"Original size: {format_file_size(original_size)}")
            print(f"Processed size: {format_file_size(compressed_size)}")
            print(f"Size reduction: {reduction_percent:.1f}%")
            print(f"Output saved to: {output_path}")
            
            if reduction_percent < 5:
                print("\nNote: Small reduction achieved. The PDF may already be optimized,")
                print("or try a higher compression level with -c high")
                if not PIL_AVAILABLE:
                    print("Install Pillow for better image compression: pip install Pillow")
    else:
        print("✗ Failed to compress PDF")
        sys.exit(1)


if __name__ == "__main__":
    main()
