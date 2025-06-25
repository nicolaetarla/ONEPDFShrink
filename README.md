# onepdfshrink

A powerful Python script to reduce PDF file sizes through intelligent compression, image optimization, and file splitting capabilities.

## 🚀 Features

- **Smart Image Compression**: Automatically detects and compresses images within PDFs using advanced algorithms
- **Image Removal**: Complete removal of all images for maximum size reduction
- **Multiple Compression Levels**: Choose from low, medium, or high compression levels
- **File Chunking**: Split large PDFs into smaller chunks with customizable size limits
- **Metadata Removal**: Strips unnecessary metadata to reduce file size
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Intelligent Image Decoding**: Handles various PDF image formats (JPEG, PNG, FlateDecode, etc.)

## 📋 Requirements

- Python 3.6 or higher
- PyPDF2 library
- Pillow (PIL) library (optional, for advanced image compression)

## 🔧 Installation

1. **Clone or download the script**:
   ```bash
   git clone <repository-url>
   cd onepdfshrink
   ```

2. **Install required dependencies**:
   ```bash
   pip install PyPDF2 Pillow
   ```

3. **Make the script executable** (optional):
   ```bash
   chmod +x onepdfshrink.py
   ```

## 📖 Usage

### Basic Syntax

```bash
python onepdfshrink.py [input_file] [options]
```

### Command Line Arguments

| Argument | Short | Long | Type | Description |
|----------|-------|------|------|-------------|
| `input` | - | - | `str` | **Required.** Path to the input PDF file |
| `-o` | `--output` | `str` | Output PDF file path (default: adds suffix to input filename) |
| `-c` | `--compression` | `str` | Compression level: `low`, `medium` (default), or `high` |
| `-v` | `--verbose` | `flag` | Show detailed processing information |
| `--overwrite` | - | `flag` | Overwrite output file if it exists without prompting |
| `-ri` | `--remove-images` | `flag` | Remove all images from the PDF |
| `-s` | `--split-size` | `float` | Split output into chunks of specified size (in MB) |

### Compression Levels

| Level | Image Quality | Max Resolution | Description |
|-------|---------------|----------------|-------------|
| `low` | 70% | 1200×900 | Light compression, good quality retention |
| `medium` | 50% | 800×600 | **Default.** Balanced compression and quality |
| `high` | 20% | 400×300 | Aggressive compression, smaller files |

## 📚 Examples

### Basic Usage

**Simple compression with default settings:**
```bash
python onepdfshrink.py document.pdf
# Output: document_compressed.pdf
```

**Specify output filename:**
```bash
python onepdfshrink.py document.pdf -o compressed_document.pdf
```

**Verbose output for detailed information:**
```bash
python onepdfshrink.py document.pdf -v
```

### Compression Levels

**Light compression (better quality):**
```bash
python onepdfshrink.py document.pdf -c low
```

**High compression (smaller size):**
```bash
python onepdfshrink.py document.pdf -c high
```

### Image Management

**Remove all images (maximum size reduction):**
```bash
python onepdfshrink.py document.pdf -ri
# Output: document_ri_compressed.pdf
```

**Combine image removal with high compression:**
```bash
python onepdfshrink.py document.pdf -ri -c high
```

### File Splitting

**Split into 10MB chunks:**
```bash
python onepdfshrink.py document.pdf -s 10
# Output: document_compressed_part01.pdf, document_compressed_part02.pdf, etc.
```

**Remove images and split into 5MB chunks:**
```bash
python onepdfshrink.py document.pdf -ri -s 5
# Output: document_ri_compressed_part01.pdf, document_ri_compressed_part02.pdf, etc.
```

### Advanced Examples

**Complete workflow with all options:**
```bash
python onepdfshrink.py large_document.pdf -c high -ri -s 15 -v --overwrite
```

**Process multiple files with a script:**
```bash
for file in *.pdf; do
    python onepdfshrink.py "$file" -c medium -v
done
```

## 📊 Output Examples

### Standard Compression
```
✓ PDF processed successfully!
Original size: 25.4MB
Processed size: 12.1MB
Size reduction: 52.4%
Output saved to: document_compressed.pdf
```

### Image Removal
```
✓ PDF processed successfully!
Original size: 25.4MB
Processed size: 8.2MB
Size reduction: 67.7%
Output saved to: document_ri_compressed.pdf
Processed 45 images, compressed 0
```

### File Splitting
```
Chunk 1 written to document_compressed_part01.pdf (9.98MB)
Chunk 2 written to document_compressed_part02.pdf (9.50MB)
Chunk 3 written to document_compressed_part03.pdf (2.63MB)
Original file removed. Created 3 chunks.
✓ PDF processed and split successfully!
Original size: 25.4MB
Total size of chunks: 22.11MB
Size reduction: 13.0%
Created 3 chunks
```

## ⚡ Performance Tips

1. **For maximum compression**: Use `-ri -c high` to remove images and apply high compression
2. **For quality retention**: Use `-c low` to maintain better image quality
3. **For large files**: Use `-s` to split into manageable chunks
4. **Batch processing**: Create shell scripts to process multiple files
5. **Test first**: Always test with a copy of important documents

## 🔍 Technical Details

### Image Processing

The script intelligently handles various image formats found in PDFs:

- **JPEG (DCTDecode)**: Already compressed, minimal processing
- **PNG/Compressed (FlateDecode)**: Decompressed and recompressed as JPEG
- **Other formats**: Skipped to avoid corruption

### Chunking Algorithm

When splitting files:
1. Processes pages sequentially
2. Tests file size after adding each page
3. Creates chunk when size limit is approached
4. Ensures no chunk exceeds the specified limit
5. Removes original file after successful splitting

### Memory Optimization

- Processes images individually to minimize memory usage
- Uses temporary files for size testing during chunking
- Cleans up temporary files automatically

## 🚨 Important Notes

- **Backup originals**: Always keep backups of original files
- **Test results**: Verify that compressed PDFs open correctly
- **Large files**: Processing very large PDFs may take significant time
- **Complex PDFs**: Some PDFs with complex structures may not compress significantly
- **Pillow dependency**: Install Pillow for best image compression results

## 🐛 Troubleshooting

### Common Issues

**"PyPDF2 is required" error:**
```bash
pip install PyPDF2
```

**"PIL/Pillow not available" warning:**
```bash
pip install Pillow
```

**Small compression ratio:**
- PDF may already be optimized
- Try higher compression levels (`-c high`)
- Consider image removal (`-ri`)

**Memory errors with large files:**
- Use file splitting (`-s`) to create smaller chunks
- Process on a machine with more RAM

### Error Messages

| Error | Solution |
|-------|----------|
| `Input file does not exist` | Check file path and permissions |
| `Input file must be a PDF file` | Ensure file has .pdf extension |
| `Error compressing PDF` | File may be corrupted or encrypted |

## 📄 License

This project is open source. Feel free to modify and distribute according to your needs.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## 📞 Support

If you encounter issues or have questions:
1. Check the troubleshooting section above
2. Ensure all dependencies are installed correctly
3. Verify your input file is a valid PDF
4. Try with a smaller test file first

---

**Made with ❤️ for efficient PDF processing**
