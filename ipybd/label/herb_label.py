"""
Author: M Maher

Date: 20171130

Python class to define a herbarium label, to be produced from Dict -> Mustache template -> HTML.

"""


class HerbLabel(object):
    # object initialized from a dictionary
    def __init__(self, *initial_data, **kwargs):
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])
