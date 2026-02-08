#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick test to see what text_arabic produces"""

import arabic_reshaper
from bidi.algorithm import get_display

def test_simple():
    original = "بيضاء"
    
    # Step 1: Reshape
    reshaped = arabic_reshaper.reshape(original)
    print(f"Original: {original}")
    print(f"After reshape: {reshaped}")
    
    # Step 2: BiDi
    final = get_display(reshaped)
    print(f"After bidi: {final}")
    
    # Check if they're different
    print(f"\nOriginal bytes: {original.encode('utf-8')}")
    print(f"Reshaped bytes: {reshaped.encode('utf-8')}")
    print(f"Final bytes: {final.encode('utf-8')}")

if __name__ == "__main__":
    test_simple()
