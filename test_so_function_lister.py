import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import so_function_lister as nm_version
import so_function_lister_elf as elf_version


# Get test library from command line or use default
TEST_LIBRARY = sys.argv.pop(1) if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else 'libexample64.so'

# Expected functions in libexample64.so (used only if testing the example library)
EXPECTED_FUNCTIONS_EXAMPLE = [
    'add',
    'average',
    'divide',
    'factorial',
    'is_even',
    'multiply',
    'print_hello',
    'reverse_string',
    'string_length',
    'subtract',
    'sum_array',
]


class TestNMVersion(unittest.TestCase):
    """Test cases for nm-based function lister."""
    
    def test_library(self):
        """Test with the specified library."""
        if not os.path.exists(TEST_LIBRARY):
            self.skipTest(f"{TEST_LIBRARY} not found")
        
        functions = nm_version.list_functions(TEST_LIBRARY)
        self.assertIsNotNone(functions, f"Failed to list functions from {TEST_LIBRARY}")
        self.assertGreater(len(functions), 0, f"No functions found in {TEST_LIBRARY}")
        
        # If testing with libexample64.so, verify expected functions
        if 'libexample' in TEST_LIBRARY:
            for func in EXPECTED_FUNCTIONS_EXAMPLE:
                self.assertIn(func, functions, f"Expected function '{func}' not found")
        
        print(f"\nnm-based version found {len(functions)} functions in {TEST_LIBRARY}")
    
    def test_nonexistent_file(self):
        """Test that None is returned for non-existent files."""
        result = nm_version.list_functions('/nonexistent/path/to/file.so')
        self.assertIsNone(result)
    
    def test_invalid_file(self):
        """Test that None is returned for invalid files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.so', delete=False) as f:
            f.write("Not an ELF file")
            temp_file = f.name
        
        try:
            result = nm_version.list_functions(temp_file)
            self.assertIsNone(result)
        finally:
            os.unlink(temp_file)
    
    def test_cli_basic(self):
        """Test CLI invocation."""
        if not os.path.exists(TEST_LIBRARY):
            self.skipTest(f"{TEST_LIBRARY} not found")
        
        result = subprocess.run(
            [sys.executable, 'so_function_lister.py', TEST_LIBRARY],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertGreater(len(result.stdout.strip().split('\n')), 0)
    
    def test_cli_nonexistent_file(self):
        """Test CLI with non-existent file."""
        result = subprocess.run(
            [sys.executable, 'so_function_lister.py', '/nonexistent/file.so'],
            capture_output=True,
            text=True
        )
        
        self.assertNotEqual(result.returncode, 0)


class TestELFVersion(unittest.TestCase):
    """Test cases for ELF-parsing function lister."""
    
    def test_library(self):
        """Test with the specified library."""
        if not os.path.exists(TEST_LIBRARY):
            self.skipTest(f"{TEST_LIBRARY} not found")
        
        functions = elf_version.list_functions(TEST_LIBRARY)
        self.assertIsNotNone(functions, f"Failed to list functions from {TEST_LIBRARY}")
        self.assertGreater(len(functions), 0, f"No functions found in {TEST_LIBRARY}")
        
        # If testing with libexample64.so, verify expected functions
        if 'libexample' in TEST_LIBRARY:
            for func in EXPECTED_FUNCTIONS_EXAMPLE:
                self.assertIn(func, functions, f"Expected function '{func}' not found")
        
        print(f"\nELF-based version found {len(functions)} functions in {TEST_LIBRARY}")
    
    def test_nonexistent_file(self):
        """Test that None is returned for non-existent files."""
        result = elf_version.list_functions('/nonexistent/path/to/file.so')
        self.assertIsNone(result)
    
    def test_invalid_file(self):
        """Test that None is returned for invalid files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.so', delete=False) as f:
            f.write("Not an ELF file")
            temp_file = f.name
        
        try:
            result = elf_version.list_functions(temp_file)
            self.assertIsNone(result)
        finally:
            os.unlink(temp_file)
    
    def test_cli_basic(self):
        """Test CLI invocation."""
        if not os.path.exists(TEST_LIBRARY):
            self.skipTest(f"{TEST_LIBRARY} not found")
        
        result = subprocess.run(
            [sys.executable, 'so_function_lister_elf.py', TEST_LIBRARY],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertGreater(len(result.stdout.strip().split('\n')), 0)
    
    def test_cli_nonexistent_file(self):
        """Test CLI with non-existent file."""
        result = subprocess.run(
            [sys.executable, 'so_function_lister_elf.py', '/nonexistent/file.so'],
            capture_output=True,
            text=True
        )
        
        self.assertNotEqual(result.returncode, 0)


class TestBothVersions(unittest.TestCase):
    """Compare both implementations to ensure they produce the same results."""
    
    def test_same_results(self):
        """Both implementations should return the same functions."""
        if not os.path.exists(TEST_LIBRARY):
            self.skipTest(f"{TEST_LIBRARY} not found")
        
        nm_functions = nm_version.list_functions(TEST_LIBRARY)
        elf_functions = elf_version.list_functions(TEST_LIBRARY)
        
        self.assertIsNotNone(nm_functions)
        self.assertIsNotNone(elf_functions)
        
        # Both should find the same set of functions
        nm_set = set(nm_functions)
        elf_set = set(elf_functions)
        
        self.assertEqual(nm_set, elf_set,
                        f"nm-based and ELF-based versions found different functions.\n"
                        f"Only in nm: {nm_set - elf_set}\n"
                        f"Only in ELF: {elf_set - nm_set}")
        
        print(f"\nBoth versions found identical {len(nm_functions)} functions in {TEST_LIBRARY}")


if __name__ == '__main__':
    print(f"Testing with: {TEST_LIBRARY}")
    print("=" * 60)
    unittest.main(verbosity=2)
