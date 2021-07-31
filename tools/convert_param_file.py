import json
import yaml
import os
import csv
from typing import Dict, List, Union
import pandas as pd
import numpy as np
import argparse


def poler2rect(magnitude:float, theta:float)->List[float]:
    deg2rad = np.pi / 180
    rad = theta*deg2rad
    e2w = float(round(-magnitude*np.sin(rad), 4))
    n2s = float(round(-magnitude*np.cos(rad), 4))
    return [e2w, n2s, 0]


def convert_str(string:str):
    try:
        return float(string)
    except ValueError:
        lower = string.strip().lower()
        if lower == 'true':
            return True
        elif lower == 'false':
            return False
        else:
            return string


JSON_KEY_TO_CSV_KEY = {
    'simulation': {
        't_max': 't_max',
    },
    'rocket':{
        'height': 'rocket_height',
        'diameter': 'rocket_diameter',
        'mass_dry': 'm_dry',
        'CG_dry': 'CG_dry',
        'CG_prop': 'CG_prop',
        'MOI_dry': ['MOI_dry_x', 'MOI_dry_y', 'MOI_dry_z'],
        'lug_1st': 'lug_1st',
        'lug_2nd': 'lug_2nd',
        'Cd0': 'Cd0',
        'Clalpha': 'Cl_alpha',
        'Cm': [0, 'Cmq', 'Cmq'],
        'CP': 'CP_body',
    },
    'engine': {
        'MOI_prop': ['MOI_prop_x', 'MOI_prop_y', 'MOI_prop_z'],
        'mass_prop': 'm_prop',
        'thrust_curve_csv': 'thrust_filename',
        'thrust_dt': 'thrust_dt'
    },
    'environment': {
        'alt_launcher': 0.0
    },
    'launcher': {
        'elev_angle': 'elev_angle',
        'azimuth': 'azimuth',
        'rail_length': 'rail_length',
    },
    'parachutes': {
        'drogue': {
            'enable': lambda param : bool(param['second_para']),
            'Cd': 'Cd_para',
            'S': 'S_para',
            'trigger': {
                'fall_time': 't_para_delay'
            },
        },
        'para': {
            'Cd': 'Cd_para_2',
            'S': 'S_para_2',
            'trigger': {
                'flight_time': 't_deploy_2',
                'altitude': 'alt_para_2'
            },
        }
    },
    'wind_model': 'wind_model',
    'wind_parameters': {
        'z0': 'wind_alt_std',
        'n': 'wind_power_coeff',
        'wind_std': lambda param: poler2rect(float(param['wind_speed']), float(param['wind_direction']))
    }
}


def format_csv_to_json(csv_param_dict:Dict[str, Union[str, float]]):
    def _recursive(key_mapping_dict:dict)->Dict[str, Union[str, float]]:
        json_dict = {}
        for json_key, val in key_mapping_dict.items():
            if isinstance(val, str):
                json_dict[json_key] = csv_param_dict[val]
            elif isinstance(val, dict):
                json_dict[json_key] = _recursive(val)
            elif isinstance(val, list):
                tmp_map = {}
                for i, v in enumerate(val):
                    tmp_map[i] = v
                json_dict[json_key] = list(_recursive(tmp_map).values())
            elif callable(val):
                json_dict[json_key] = val(csv_param_dict)
            else:
                json_dict[json_key] = val
        return json_dict
    return _recursive(JSON_KEY_TO_CSV_KEY)


def load_csv_params(input_path:str)->Dict[str, Union[str, float]]:
    params_df = pd.read_csv(input_path, comment='$', index_col=0, names=('parameters', 'values'), skip_blank_lines=True)
    params_df = params_df.dropna()
    _params_dict = params_df.to_dict(orient='dict')['values']
    params_dict = {}
    for key, val in _params_dict.items():
        val = val.strip()
        params_dict[key] = convert_str(val)
    return params_dict


def main(
        input_path:str,
        output_path:str
    ):

    input_ext = os.path.splitext(input_path)[1]
    if input_ext == '.csv':
        csv_params = load_csv_params(input_path)
        json_params = format_csv_to_json(csv_params)
        with open(output_path, 'w') as f:
            # json.dump(json_params, f, indent=4)
            yaml.dump(json_params, f, indent=4)
    elif input_ext == '.json':
        pass
    elif input_ext == '.yaml' or input_ext == '.yml':
        pass
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('-o', '--output', default='./params.yaml')
    args = parser.parse_args()

    main(input_path=args.input, output_path=args.output)
