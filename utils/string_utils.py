def is_partial_match(input_string, string_list):
    input_lower = input_string.lower()
    eval1 = any(input_lower in s.lower() for s in string_list)
    eval2 = any(s.lower() in input_lower for s in string_list)
    return eval1 or eval2