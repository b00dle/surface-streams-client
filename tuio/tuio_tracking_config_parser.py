import json
import os
from typing import Dict
from tuio.tuio_elements import TuioImagePattern, TuioPointer
from tuio.tuio_tracking_info import TuioTrackingInfo


class TuioTrackingConfigParser(object):
    def __init__(self, config_path=""):
        self._patterns = {}
        self._pattern_tracking_info = {}
        self._pointers = {}
        self._pointer_tracking_info = {}
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

    def get_pointers(self) -> Dict[str, TuioPointer]:
        return self._pointers

    def get_pointer(self, pointer_s_id: int) -> TuioPointer:
        return self._pointers[pointer_s_id]

    def get_pattern_tracking_info(self, pattern_s_id: int) -> TuioTrackingInfo:
        return self._pattern_tracking_info[pattern_s_id]

    def get_pointer_tracking_info(self, pattern_s_id: int) -> TuioTrackingInfo:
        return self._pointer_tracking_info[pattern_s_id]

    def get_default_matching_scale(self) -> float:
        return self._default_matching_scale

    def parse(self):
        """ Reads data from json formatted config file. """
        self._patterns = {}
        self._pattern_tracking_info = {}
        self._pointers = {}
        self._pointer_tracking_info = {}
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
            if not self._parse_add_element(p_desc["type"], p_desc["data"]):
                print("FAILURE: couldn't add pattern")
                print("  > type", p_desc["type"])
                print("  > data", p_desc["data"])

        self._default_matching_scale = float(json_data["default_matching_scale"])

    def _parse_add_element(self, p_type, p_data):
        info = None
        if "tracking_info" in p_data:
            info = TuioTrackingInfo(**p_data["tracking_info"])
        else:
            return False

        if p_type == "image":
            elmt = TuioImagePattern()
            self._patterns[elmt.get_s_id()] = elmt
            self._pattern_tracking_info[elmt.get_s_id()] = info
        elif p_type == "pen":
            elmt = TuioPointer(tu_id=TuioPointer.tu_id_pen)
            self._pointers[elmt.s_id] = elmt
            self._pointer_tracking_info[elmt.s_id] = info
        elif p_type == "pointer":
            elmt = TuioPointer(tu_id=TuioPointer.tu_id_pointer)
            self._pointers[elmt.s_id] = elmt
            self._pointer_tracking_info[elmt.s_id] = info
        elif p_type == "eraser":
            elmt = TuioPointer(tu_id=TuioPointer.tu_id_eraser)
            self._pointers[elmt.s_id] = elmt
            self._pointer_tracking_info[elmt.s_id] = info
        else:
            return False

        return True

    @staticmethod
    def validate_root_structure(json_data):
        required_keys = ["patterns", "default_matching_scale"]
        for rk in required_keys:
            if rk not in json_data:
                return False
        return True

    @staticmethod
    def read_json(config_path):
        file_content = open(config_path).read()
        return json.loads(file_content)