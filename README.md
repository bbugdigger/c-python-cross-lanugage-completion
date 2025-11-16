# C/Python cross lanugage completion

A Python tool to extract and list exported functions from Linux shared object (.so) files. Implemented with two different approaches to demonstrate understanding of both high-level system tools and low-level binary format parsing.

This project provides two implementations for listing exported functions from ELF shared objects:

1. **`so_function_lister.py`** - Uses the `nm` command (simple, robust)
2. **`so_function_lister_elf.py`** - Direct ELF binary parsing (no external dependencies)

Both implementations produce identical output, making them interchangeable depending on the environment and requirements.

## Usage

Both implementations have identical interfaces:

```
# Basic usage
python so_function_lister.py <path-to-library.so>
python so_function_lister_elf.py <path-to-library.so>

# Example with custom library
python so_function_lister.py libexample64.so
```

