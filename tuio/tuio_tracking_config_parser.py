import json
import os
from typing import Dict
from tuio.tuio_elements import TuioImagePattern
from tuio.tuio_tracking_info import TuioTrackingInfo


class TuioTrackingConfigParser(object):
    def __init__(self, config_path=""):
        self._patterns = {}
        self._tracking_info = {}
        self._default_matching_scale = 0.0
        self._config_path = config_path
        self.parse()

    def set_config_path(self, config_path):
        self._config_path = config_path
        self.parse()

    def get_patterns(self) -> Dict[str, TuioImagePattern]:
        return self._patterns

    def get_pattern(self, pattern_s_id: int) -> TuioImagePattern:
        return self._patterns[pattern_s_id]

    def get_tracking_info(self, pattern_s_id: int) -> TuioTrackingInfo:
        return self._tracking_info[pattern_s_id]

    def get_default_matching_scale(self) -> float:
        return self._default_matching_scale

    def parse(self):
        """ Reads data from json formatted config file. """
        self._patterns = {}
        self._tracking_info = {}
        self._default_matching_scale = 0.0
        if len(self._config_path) == 0:
            return

        if not os.path.isfile(self._config_path):
            raise ValueError("FAILURE: cannot read tuio config.\n  > specified path '"+self._config_path+"' is no file.")

        json_data = self.read_json(self._config_path)
        if not self.validate_root_structure(json_data):
            return

        for p_desc in json_data["patterns"]:
            if "type" not in p_desc or "data" not in p_desc:
                print("FAILURE: wrong format for pattern description.")
                print("  > parser expects definition for 'type' and 'data'")
                print("  > got", p_desc)
                print("  > skipping.")
                continue
            if not self._parse_add_pattern(p_desc["type"], p_desc["data"]):
                print("FAILURE: couldn't add pattern")
                print("  > type", p_desc["type"])
                print("  > data", p_desc["data"])

        self._default_matching_scale = float(json_data["default_matching_scale"])

    def _parse_add_pattern(self, p_type, p_data):
        p = self.create_pattern(p_type)
        p_tracking_info = self.create_tracking_info(p_data)

        if p is None or p_tracking_info is None:
            return False

        self._patterns[p.get_s_id()] = p
        self._tracking_info[p.get_s_id()] = p_tracking_info

        return True

    @staticmethod
    def validate_root_structure(json_data):
        required_keys = ["patterns", "default_matching_scale"]
        for rk in required_keys:
            if rk not in json_data:
                return False
        return True

    @staticmethod
    def create_pattern(p_type):
        if p_type == "image":
            return TuioImagePattern()
        return None

    @staticmethod
    def create_tracking_info(p_data):
        if "tracking_info" in p_data:
            return TuioTrackingInfo(**p_data["tracking_info"])
        return None

    @staticmethod
    def read_json(config_path):
        file_content = open(config_path).read()
        return json.loads(file_content)