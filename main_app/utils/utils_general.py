
def _n_group(l, n):
    return [ l[i:i+n] for i in range(0, len(l), n) ]

def strip_string_or_none(string):
	if string is None:
		return None

	if string.strip() == '':
		return None

	return string.strip()
