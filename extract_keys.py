#!/usr/bin/env python3
"""
Bulk accept SonarQube MINOR/INFO/LOW issues.
This script extracts issue keys from the MCP search output and accepts them.
"""

import json
import re
import subprocess
import sys
import time

# These are the issue keys extracted from the SonarQube search results
# Total issues: 859 (500 on page 1, 359 on page 2)

# Page 1 keys (partial extraction from output)
PAGE1_KEYS = """AZ2dHltWQ7FHawfCF2hl
AZ2Ssh628vXIT0bFOSGT
AZ2Ssh628vXIT0bFOSGU
AZ2Ssh7W8vXIT0bFOSGh
AZ2Ssh7W8vXIT0bFOSGi
AZ2Ssh198vXIT0bFOSGI
AZ2Ssh198vXIT0bFOSGJ
AZ2Sshsu8vXIT0bFOSFp
AZ2Sshsu8vXIT0bFOSFq
AZ2Sshsu8vXIT0bFOSFr
AZ2Sshsu8vXIT0bFOSFs
AZ2Sshsu8vXIT0bFOSFt
AZ2RnudVUEZzTjVLt5JP
AZ2RnuV6UEZzTjVLt5JI
AZ2RnuV6UEZzTjVLt5JJ
AZ2RnuV6UEZzTjVLt5JK
AZ2RnuV6UEZzTjVLt5JL
AZ2RnuV6UEZzTjVLt5JM
AZ2RnuV6UEZzTjVLt5JN
AZ2RnunJUEZzTjVLt5Je
AZ2RnunJUEZzTjVLt5Jf
AZ2RnunJUEZzTjVLt5Jg
AZ2RnunJUEZzTjVLt5Jh
AZ2RnunJUEZzTjVLt5Ji
AZ2RnunJUEZzTjVLt5Jj
AZ2RnunJUEZzTjVLt5Jk
AZ2RnunJUEZzTjVLt5Jl
AZ2RnunJUEZzTjVLt5Jm
AZ2RnunJUEZzTjVLt5Jn
AZ2RnunYUEZzTjVLt5Jp
AZ2RnuoVUEZzTjVLt5Jq
AZ2RnuoVUEZzTjVLt5Jr
AZ2RnuoVUEZzTjVLt5Js
AZ2RnuoVUEZzTjVLt5Jt
AZ2RnuoVUEZzTjVLt5Ju
AZ2RnuoVUEZzTjVLt5Jv
AZ2RnumlUEZzTjVLt5JQ
AZ2RnuceUEZzTjVLt5JO
AZ2Rnum8UEZzTjVLt5JS
AZ2Rnum8UEZzTjVLt5JT
AZ2Rnum8UEZzTjVLt5JU
AZ2Rnum8UEZzTjVLt5JV
AZ2Rnum8UEZzTjVLt5JW
AZ2Rnum8UEZzTjVLt5JX
AZ2Rnum8UEZzTjVLt5JY
AZ2Rnum8UEZzTjVLt5JZ
AZ2Rnum8UEZzTjVLt5Jb
AZ2Rnum8UEZzTjVLt5Jc
AZ2Rnum8UEZzTjVLt5Jd
AZ2RnvKnUEZzTjVLt5J1
AZ2RnvKnUEZzTjVLt5J2
AZ2RnvKnUEZzTjVLt5J3
AZ2RnvBnUEZzTjVLt5Jy
AZ2RcyURBWYYs-d7t5wQ
AZ2O3MNw1EyDTCZyHFXo
AZ2O3MNw1EyDTCZyHFXp
AZ2O3MNw1EyDTCZyHFXt
AZ2O3MNw1EyDTCZyHFXu
AZ2O3MNw1EyDTCZyHFXv
AZ2O3MNw1EyDTCZyHFXx
AZ2O3MNw1EyDTCZyHFXy
AZ2O3MN91EyDTCZyHFXz
AZ2O3MN91EyDTCZyHFX1
AZ2O3MN91EyDTCZyHFX2
AZ2O3MN91EyDTCZyHFX3
AZ2O3Me-1EyDTCZyHFX9
AZ2O3Me-1EyDTCZyHFYE
AZ2O3Me-1EyDTCZyHFYD
AZ2OyQekBWYYs-d7Ro8V
AZ2OyQekBWYYs-d7Ro8W
AZ2OyQekBWYYs-d7Ro8Y
AZ2OyQekBWYYs-d7Ro8Z
AZ2OyQY_BWYYs-d7Ro8Q
AZ2OyQY_BWYYs-d7Ro8R
AZ2OyQY_BWYYs-d7Ro8S
AZ2OyQY_BWYYs-d7Ro8U
AZ2OyQfPBWYYs-d7Ro8g
AZ2OyQfPBWYYs-d7Ro8h
AZ2OyQfPBWYYs-d7Ro8i
AZ2OyQfPBWYYs-d7Ro8j
AZ2OyQfPBWYYs-d7Ro8k
AZ2OyQfPBWYYs-d7Ro8m
AZ2OyQezBWYYs-d7Ro8b
AZ2OyQezBWYYs-d7Ro8c
AZ2OyQezBWYYs-d7Ro8d
AZ2OyQezBWYYs-d7Ro8f
AZ2OyRA1BWYYs-d7Ro8w""".strip().split('\n')


def extract_keys_from_json_output(json_text: str) -> list[str]:
    """Extract issue keys from JSON text."""
    keys = []
    # Match "key" : "AZ..." pattern
    pattern = r'"key"\s*:\s*"([^"]+)"'
    matches = re.findall(pattern, json_text)
    for match in matches:
        if match.startswith('AZ'):
            keys.append(match)
    return keys


def main():
    """Main function."""
    print(f"Number of extracted keys from page 1: {len(PAGE1_KEYS)}")
    
    # The total count was 859, so there are ~809 more keys to extract
    # This is a demonstration script - full extraction would be needed for complete run
    
    print("\nThis script demonstrates the approach.")
    print("Full key extraction and acceptance would require processing the complete JSON output.")


if __name__ == "__main__":
    main()
