import copy


class TuioSessionId(object):
    _current = 0
    _existing = []

    @staticmethod
    def get(keep_current=False):
        s_id = TuioSessionId._current
        if not keep_current:
            TuioSessionId._current += 1
            if s_id in TuioSessionId._existing:
                s_id = TuioSessionId.get()
            TuioSessionId._existing.append(s_id)
        return s_id

    @staticmethod
    def get_existing():
        return copy.deepcopy(TuioSessionId._existing)

    @staticmethod
    def add_existing(s_id):
        if s_id not in TuioSessionId._existing:
            TuioSessionId._existing.append(s_id)


class TuioSessionElement(object):
    def __init__(self, s_id=-1):
        self.s_id = s_id
        if self.s_id == -1:
            self.s_id = TuioSessionId().get()

    def is_empty(self):
        return self.s_id == -1

    def __str__(self):
        s = "<TuioSessionElement s_id="+str(self.s_id)+">"
        return s

    def __repr__(self):
        return self.__str__()


class TuioBounds(object):
    def __init__(self, x_pos=0.0, y_pos=0.0, angle=0.0, width=0.0, height=0.0):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.angle = angle
        self.width = width
        self.height = height

    def is_empty(self):
        return self.width <= 0 or self.height <= 0

    def normalized(self, h, w):
        return TuioBounds(self.x_pos / w, self.y_pos / h, self.angle, self.width / w, self.height / h)

    def scaled(self, h, w):
        return TuioBounds(self.x_pos * w, self.y_pos * h, self.angle, self.width * w, self.height * h)

    def __str__(self):
        s = "<TuioBounds x_pos="+str(self.x_pos)+" y_pos="+str(self.y_pos)+" "
        s += "angle="+str(self.angle)+" width="+str(self.width)+" "
        s += "height="+str(self.height)+">"
        return s

    def __repr__(self):
        return self.__str__()


class TuioSymbol(object):
    def __init__(self, uuid=None, tu_id=-1, c_id=-1):
        self.tu_id = tu_id
        self.c_id = c_id
        self.uuid = uuid

    def is_empty(self):
        return self.uuid is None

    def __eq__(self, other):
        return self.uuid == other.uuid and \
               self.tu_id == other.tu_id and \
               self.c_id == other.c_id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        s = "<TuioSymbol uuid="+str(self.uuid)+" "
        s += "tu_id="+str(self.tu_id)+" c_id="+str(self.c_id)+">"
        return s

    def __repr__(self):
        return self.__str__()


class TuioPointer(TuioSessionElement):
    tu_id_pointer = 0
    tu_id_pen = 1
    tu_id_eraser = 2

    def __init__(self, s_id=-1, u_id=-1, tu_id=-1, c_id=-1, x_pos=0.0, y_pos=0.0, radius=0.0, press=False):
        super().__init__(s_id=s_id)
        self.tu_id = tu_id
        self.c_id = c_id
        self.u_id = u_id
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.radius = radius
        self.press = press

    def refresh_s_id(self):
        self.s_id = TuioSessionId.get()

    def key(self):
        return TuioPointer.calc_key(self.s_id, self.u_id, self.c_id)

    @staticmethod
    def calc_key(s_id, u_id, c_id):
        return str(s_id) + "_" + str(u_id) + "_" + str(c_id)

    def __eq__(self, other):
        return self.key() == other.key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        s = "<TuioPointer s_id="+str(self.s_id)+" "
        s += "u_id="+str(self.u_id)+" tu_id="+str(self.tu_id)+ " "
        s += "c_id="+str(self.c_id)+" x_pos="+str(self.x_pos)+ " "
        s += "y_pos="+str(self.y_pos)+" radius="+str(self.radius)+ " "
        s += "press="+str(self.press)+">"
        return s

    def __repr__(self):
        return self.__str__()


class TuioImagePattern(TuioSessionElement):
    def __init__(self, s_id=-1, bnd=None, sym=None, u_id=-1):
        super().__init__(s_id=s_id)
        self._bnd = bnd
        if self._bnd is None:
            self._bnd = TuioBounds()
        self._sym = sym
        if self._sym is None:
            self._sym = TuioSymbol()
        self._u_id = u_id # user_id

    def __str__(self):
        s = "<TuioPattern s_id="+str(self.s_id)+" "+"u_id="+str(self._u_id)+" "
        s += "bnd="+str(self._bnd)+" sym="+str(self._sym)+">"
        return s

    def __repr__(self):
        return self.__str__()

    def is_valid(self):
        return not self._bnd.is_empty() and not self._sym.is_empty()

    def get_s_id(self):
        return self.s_id

    def get_u_id(self):
        return self._u_id

    def get_bnd(self):
        return self._bnd

    def get_sym(self):
        return self._sym

    def set_bnd(self, bnd):
        self._bnd = bnd

    def set_sym(self, sym):
        self._sym = sym

    def set_x_pos(self, x_pos):
        self._bnd.x_pos = x_pos

    def set_y_pos(self, y_pos):
        self._bnd.y_pos = y_pos

    def set_angle(self, angle):
        self._bnd.angle = angle

    def set_width(self, width):
        self._bnd.width = width

    def set_height(self, height):
        self._bnd.width = height

    def set_uuid(self, uuid):
        self._sym.uuid = uuid

    def set_tu_id(self, tu_id):
        self._sym.tu_id = tu_id

    def set_c_id(self, c_id):
        self._sym.c_id = c_id
