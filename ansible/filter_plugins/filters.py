#!/usr/bin/python
class FilterModule(object):
    def filters(self):
        return {
            'dictify': self.dictify,
        }

    def dictify(self, list_in):

        dict_out = {}

        for item in list_in:
            name = item.pop("name")
            dict_out[name] = item

        return dict_out