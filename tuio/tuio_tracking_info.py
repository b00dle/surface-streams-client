class TuioTrackingInfo(object):
    def __init__(self, matching_resource="", varying_upload_resource="", matching_scale=-1.0):
        self.matching_resource = matching_resource
        self.varying_upload_resource = varying_upload_resource
        self.matching_scale = float(matching_scale)