import base64
import io
import sys
from typing import Annotated

import numpy as np
from pydantic import BeforeValidator, PlainSerializer


def nd_array_custom_before_validator(v):
    if isinstance(v, str):
        arr_bytes = base64.b64decode(v.encode("utf-8"))
        buffer = io.BytesIO(arr_bytes)
        return np.load(buffer)
    if isinstance(v, list):
        return np.array(v)
    if not isinstance(v, np.ndarray):
        raise TypeError("list or ndarray required")
    return v


def nd_array_custom_serializer(x: np.ndarray):
    buffer = io.BytesIO()
    np.save(buffer, x)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


NdArray = Annotated[
    np.ndarray,
    BeforeValidator(nd_array_custom_before_validator),
    PlainSerializer(nd_array_custom_serializer, return_type=str),
]


def decode_array_to_text(encoded_str: str, format_style="compact") -> str:
    """
    Decode a base64-encoded numpy array to human-readable text.

    Args:
        encoded_str: Base64 encoded array string from your Pydantic model
        format_style: "compact", "pretty", or "full"
    """
    try:
        arr_bytes = base64.b64decode(encoded_str.encode("utf-8"))
        buffer = io.BytesIO(arr_bytes)
        arr = np.load(buffer)

        if format_style == "compact":
            return f"Array{arr.shape} {arr.dtype}:\n{np.array2string(arr, precision=3, suppress_small=True)}"

        elif format_style == "pretty":
            return f"""Shape: {arr.shape}
Dtype: {arr.dtype}
Size: {arr.size} elements
Data:
{np.array2string(arr, precision=4, suppress_small=True, separator=', ')}"""

        elif format_style == "full":
            return f"""Shape: {arr.shape}
Dtype: {arr.dtype} 
Size: {arr.size} elements
Min: {arr.min():.4f}, Max: {arr.max():.4f}, Mean: {arr.mean():.4f}
Data:
{np.array2string(arr, threshold=np.inf, precision=4)}"""

    except Exception as e:
        return f"Error decoding array: {e}"


def cli_decode_array():
    """CLI function to decode array from command line argument"""
    if len(sys.argv) < 2:
        print("Usage: python your_utils_file.py <base64_encoded_array> [format_style]")
        print("Format styles: compact (default), pretty, full")
        sys.exit(1)

    encoded_str = sys.argv[1]
    format_style = sys.argv[2] if len(sys.argv) > 2 else "compact"

    if format_style not in ["compact", "pretty", "full"]:
        print("Invalid format style. Use: compact, pretty, or full")
        sys.exit(1)

    result = decode_array_to_text(encoded_str, format_style)
    print(result)


if __name__ == "__main__":
    cli_decode_array()
