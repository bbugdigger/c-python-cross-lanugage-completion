import struct
import sys
from pathlib import Path
from typing import List, Optional


# ELF constants
ELF_MAGIC = b'\x7fELF'
ELFCLASS64 = 2
ELFDATA2LSB = 1

# Section header types
SHT_SYMTAB = 2
SHT_DYNSYM = 11
SHT_STRTAB = 3

# Symbol binding and type
STB_GLOBAL = 1
STT_FUNC = 2


def read_elf_header(f):
    """Read and parse ELF header."""
    f.seek(0)
    elf_ident = f.read(16)
    
    if len(elf_ident) < 16:
        print("Error: File too small to be an ELF file")
        return None
    
    if elf_ident[:4] != ELF_MAGIC:
        return None
    
    elf_class = elf_ident[4]
    if elf_class == 1:
        print("Error: 32-bit ELF files are not supported (only 64-bit)")
        return None
    elif elf_class != ELFCLASS64:
        print(f"Error: Unknown ELF class: {elf_class}")
        return None
    
    # Read rest of ELF header (64-bit)
    header_data = f.read(48)
    if len(header_data) < 48:
        print("Error: Incomplete ELF header")
        return None
    
    elf_header = struct.unpack('<HHIQQQIHHHHHH', header_data)
    
    # ELF64 header layout after e_ident:
    # e_type(H), e_machine(H), e_version(I), e_entry(Q), e_phoff(Q), e_shoff(Q),
    # e_flags(I), e_ehsize(H), e_phentsize(H), e_phnum(H), e_shentsize(H), e_shnum(H), e_shstrndx(H)
    
    header_info = {
        'e_shoff': elf_header[5],      # Section header table offset
        'e_shentsize': elf_header[10], # Section header entry size (was wrong: was 9, should be 10)
        'e_shnum': elf_header[11],     # Number of section headers (was wrong: was 10, should be 11)
        'e_shstrndx': elf_header[12],  # Section header string table index (was wrong: was 11, should be 12)
    }
    
    # Sanity check: 64-bit ELF section headers should be 64 bytes
    if header_info['e_shentsize'] != 64:
        print(f"Warning: Unexpected section header size: {header_info['e_shentsize']} (expected 64)")
        print(f"Debug info: e_shoff={header_info['e_shoff']}, e_shnum={header_info['e_shnum']}")
    
    return header_info


def read_section_headers(f, elf_header):
    """Read all section headers."""
    sections = []
    f.seek(elf_header['e_shoff'])
    
    for i in range(elf_header['e_shnum']):
        sh_data = f.read(elf_header['e_shentsize'])
        
        if len(sh_data) < 64:
            print(f"Error: Section header {i} is incomplete (got {len(sh_data)} bytes, expected 64)")
            return None
        
        sh = struct.unpack('<IIQQQQIIQQ', sh_data)
        
        sections.append({
            'sh_name': sh[0],
            'sh_type': sh[1],
            'sh_offset': sh[4],
            'sh_size': sh[5],
            'sh_link': sh[6],
            'sh_entsize': sh[9],
        })
    
    return sections


def read_string_table(f, section):
    """Read string table from a section."""
    f.seek(section['sh_offset'])
    return f.read(section['sh_size'])


def read_symbols(f, symtab_section, strtab_data):
    """Read symbols from symbol table section."""
    functions = []
    
    f.seek(symtab_section['sh_offset'])
    num_symbols = symtab_section['sh_size'] // symtab_section['sh_entsize']
    
    for i in range(num_symbols):
        sym_data = f.read(symtab_section['sh_entsize'])
        sym = struct.unpack('<IBBHQQ', sym_data)
        
        st_name = sym[0]
        st_info = sym[1]
        st_value = sym[4]
        st_size = sym[5]
        
        # Extract binding and type from st_info
        st_bind = st_info >> 4
        st_type = st_info & 0xf
        
        # Only interested in global function symbols
        if st_bind == STB_GLOBAL and st_type == STT_FUNC and st_value != 0:
            # Get function name from string table
            name_end = strtab_data.find(b'\x00', st_name)
            if name_end != -1:
                name = strtab_data[st_name:name_end].decode('utf-8', errors='ignore')
                if name:
                    functions.append(name)
    
    return functions


def list_functions(so_path: str) -> Optional[List[str]]:
    path = Path(so_path)
    
    if not path.exists():
        print(f"Error: File not found: {so_path}")
        return None
    
    try:
        with open(path, 'rb') as f:
            # Read ELF header
            elf_header = read_elf_header(f)
            if not elf_header:
                print(f"Error: Not a valid 64-bit ELF file: {so_path}")
                return None
            
            # Read section headers
            sections = read_section_headers(f, elf_header)
            if sections is None:
                return None
            
            # Find dynamic symbol table (.dynsym) and its string table
            dynsym_section = None
            strtab_section = None
            
            for section in sections:
                if section['sh_type'] == SHT_DYNSYM:
                    dynsym_section = section
                    # The string table index is in sh_link
                    strtab_section = sections[section['sh_link']]
                    break
            
            if not dynsym_section:
                print(f"Error: No dynamic symbol table found in {so_path}")
                return None
            
            # Read string table
            strtab_data = read_string_table(f, strtab_section)
            
            # Read and parse symbols
            functions = read_symbols(f, dynsym_section, strtab_data)
            
            return sorted(set(functions))
            
    except Exception as e:
        print(f"Error: Failed to parse ELF file: {e}")
        return None


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

