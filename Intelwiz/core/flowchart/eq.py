# -*- coding: utf-8 -*-
from numpy import ndarray, bool_
from pyqtgraph.metaarray import MetaArray
import torch
def eq(a, b):
    """The great missing equivalence function: Guaranteed evaluation to a single bool value."""
    if (isinstance(a,dict) and ('value' in a.keys()) and  isinstance(a['value'],torch.Tensor) and (isinstance(b,dict) and ('value' in b.keys()) and  isinstance(b['value'],torch.Tensor))):
         if a['value'].shape != b['value'].shape:
                return False 
         else:
            return (a['value']==b['value']).all()
    else:
        if isinstance(a,dict) and ('value' in a.keys()) and  isinstance(a['value'],torch.Tensor):
            return False
        if (isinstance(b,dict) and ('value' in b.keys()) and  isinstance(b['value'],torch.Tensor)):
            return False
    if a is b:
        return True
        
    try:
        e = a==b
    except ValueError:
        return False
    except AttributeError: 

        return False
    except:
        print("a:", str(type(a)), str(a))
        print("b:", str(type(b)), str(b))
        raise
    t = type(e)
    if t is bool:
        return e
    elif t is bool_:
        return bool(e)
    elif isinstance(e, ndarray) or isinstance(e, torch.Tensor) or (hasattr(e, 'implements') and e.implements('MetaArray')):
        try:   ## disaster: if a is an empty array and b is not, then e.all() is True
            if a.shape != b.shape:
                return False
        except:
            return False
        if (hasattr(e, 'implements') and e.implements('MetaArray')):
             return e.asarray().all()
        else:
            return e.all()
    else:
        raise Exception("== operator returned type %s" % str(type(e)))
