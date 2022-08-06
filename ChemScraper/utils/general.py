import itertools
from datetime import datetime

import numpy as np
from monty.json import MSONable


def represent_nested_monty_json(o: MSONable, precision=5):
    s = "{}: ".format(o.__class__.__name__)
    for k, v in o.as_dict().items():
        if k.startswith("@"):
            continue
        if isinstance(v, float):
            v = round(v, precision)
        s += "{}={}\t".format(k, v)
    return s


def to_float(x):
    try:
        assert not np.isnan(x)
        return float(x)
    except (ValueError, AssertionError) as e:
        return None


def unison_shuffle(a, b, seed):
    assert len(a) == len(b)
    p = np.random.RandomState(seed=seed).permutation(len(a))
    return a[p], b[p]


def sort_and_group(data, keyf):
    groups = []
    unique_keys = []
    data = sorted(data, key=keyf)
    for k, g in itertools.groupby(data, keyf):
        groups.append(list(g))
        unique_keys.append(k)
    return unique_keys, groups


def is_close(a: float, b: float, eps=1e-5):
    return abs(a - b) < eps


def is_close_relative(a: float, b: float, eps=1e-5):
    aa = abs(a)
    bb = abs(b)
    return abs(a - b) / min([aa, bb]) < eps


def is_close_list(lst: list[float], eps=1e-5):
    for i, j in itertools.combinations(lst, 2):
        if is_close(i, j, eps):
            return True
    return False


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_timestamp():
    return int(datetime.now().timestamp() * 1000)
