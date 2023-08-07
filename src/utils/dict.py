from typing import Dict, TypeVar, Union


K = TypeVar('K')
V = TypeVar('V')


def safe_get(d: Dict[K, V], k: K) -> Union[V, None]:
    if d is None or not isinstance(d, dict): return None
    if k in d.keys(): return d[k]