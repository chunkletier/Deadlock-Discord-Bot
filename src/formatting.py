def pad_string(input, width: int = 10) -> str:
    pad_length = width - len(str(input)) if len(str(input)) <= width else 0
    return str(input).ljust(pad_length)
