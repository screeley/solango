#
# Copyright 2008 Optaros, Inc.
#

from UserDict import UserDict

class InstanceDict(UserDict):
    
    def __getattr__(self, key):
        try:
            return self.__dict__[key]
        except KeyError:
            pass
        try:
            assert not key.startswith('_')
            return self.__getitem__(key)
        except:
            raise AttributeError("InstanceDict has no attribute %s" % key)

    def __setattr__(self, key, value):
        if key.startswith('_') or key == 'data':
            self.__dict__[key] = value
        else:
            return self.__setitem__(key, value)
    def __nonzero__(self):
        if len(self.data) is 0:
            return False
        else:
            return True
#Make it easier to call
idict = InstanceDict
