#!/usr/bin/env python3
"""
Language File Validator
Validates that all language files have consistent keys
"""

import json
import sys
from pathlib import Path


def validate_json_files():
    """Validate JSON language files"""
    lang_dir = Path(__file__).parent / "lang"
    
    if not lang_dir.exists():
        print(f"Error: Language directory not found: {lang_dir}")
        return False
    
    json_files = list(lang_dir.glob("*.json"))
    
    if not json_files:
        print("Warning: No JSON language files found")
        return True
    
    # Load first file as reference
    reference_keys = None
    reference_file = None
    
    all_valid = True
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            keys = set(data.keys())
            
            if reference_keys is None:
                reference_keys = keys
                reference_file = json_file.name
                print(f"Reference file: {reference_file} ({len(keys)} keys)")
            else:
                # Compare keys
                missing = reference_keys - keys
                extra = keys - reference_keys
                
                if missing or extra:
                    print(f"\n❌ {json_file.name} has inconsistencies:")
                    if missing:
                        print(f"   Missing keys: {missing}")
                    if extra:
                        print(f"   Extra keys: {extra}")
                    all_valid = False
                else:
                    print(f"✓ {json_file.name} ({len(keys)} keys) - OK")
        
        except json.JSONDecodeError as e:
            print(f"❌ {json_file.name} - Invalid JSON: {e}")
            all_valid = False
        except Exception as e:
            print(f"❌ {json_file.name} - Error: {e}")
            all_valid = False
    
    return all_valid


def validate_nsh_files():
    """Validate NSH language files"""
    lang_dir = Path(__file__).parent / "lang"
    
    if not lang_dir.exists():
        print(f"Error: Language directory not found: {lang_dir}")
        return False
    
    nsh_files = list(lang_dir.glob("*.nsh"))
    
    if not nsh_files:
        print("Warning: No NSH language files found")
        return True
    
    reference_keys = None
    reference_file = None
    
    all_valid = True
    
    for nsh_file in nsh_files:
        try:
            keys = set()
            with open(nsh_file, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('LangString'):
                        parts = line.split(None, 2)
                        if len(parts) >= 2:
                            keys.add(parts[1])
            
            if reference_keys is None:
                reference_keys = keys
                reference_file = nsh_file.name
                print(f"Reference NSH file: {reference_file} ({len(keys)} keys)")
            else:
                # Compare keys
                missing = reference_keys - keys
                extra = keys - reference_keys
                
                if missing or extra:
                    print(f"\n❌ {nsh_file.name} has inconsistencies:")
                    if missing:
                        print(f"   Missing keys: {missing}")
                    if extra:
                        print(f"   Extra keys: {extra}")
                    all_valid = False
                else:
                    print(f"✓ {nsh_file.name} ({len(keys)} keys) - OK")
        
        except Exception as e:
            print(f"❌ {nsh_file.name} - Error: {e}")
            all_valid = False
    
    return all_valid


def main():
    print("=" * 60)
    print("TradeMind MT5 Language File Validator")
    print("=" * 60)
    
    print("\n--- Validating JSON Files ---")
    json_valid = validate_json_files()
    
    print("\n--- Validating NSH Files ---")
    nsh_valid = validate_nsh_files()
    
    print("\n" + "=" * 60)
    if json_valid and nsh_valid:
        print("✅ All language files are valid!")
        return 0
    else:
        print("❌ Some language files have issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())