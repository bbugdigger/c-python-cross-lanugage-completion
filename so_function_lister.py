import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def list_functions(so_path: str) -> Optional[List[str]]:
    path = Path(so_path)
    
    if not path.exists():
        print(f"Error: File not found: {so_path}")
        return None
    
    # Binaries on Linux are ELF files. So we need to check for the ELF magic number for verification
    try:
        with open(path, 'rb') as f:
            if f.read(4) != b'\x7fELF':
                print(f"Error: Not a valid ELF file: {so_path}")
                return None
    except Exception as e:
        print(f"Error: Cannot read file: {e}")
        return None
    
    try:
        result = subprocess.run(
            ['nm', '-D', '--defined-only', str(path)],
            capture_output=True,
            text=True,
            check=True
        )
    except FileNotFoundError:
        print("Error: nm command not found. Install binutils.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to read symbols: {e}")
        return None
    
    # Since nm command returns a lot of information, we need to parse the output and extract the exported functions only (type 'T')
    functions = set()
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            symbol_type = parts[1] if len(parts) >= 3 else parts[0]
            symbol_name = parts[2] if len(parts) >= 3 else parts[1]
            if symbol_type == 'T':
                # Strip version information (e.g., "symbol@@VERSION" -> "symbol")
                if '@@' in symbol_name:
                    symbol_name = symbol_name.split('@@')[0]
                if '@' in symbol_name and not symbol_name.startswith('@'):
                    symbol_name = symbol_name.split('@')[0]
                functions.add(symbol_name)
    
    return sorted(functions)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <shared_object.so>")
        return 1
    
    functions = list_functions(sys.argv[1])
    if functions is None:
        return 1
    
    for func in functions:
        print(func)
    return 0


if __name__ == '__main__':
    sys.exit(main())

