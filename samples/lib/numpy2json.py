# Jsonエンコーダクラス
import quaternion
import numpy as np
import json
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, quaternion.quaternion):
            return quaternion.as_float_array(obj)
        else:
            return super(NumpyEncoder, self).default(obj)
