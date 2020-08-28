from ipybd import PlantSpecimenTerms

class A(type):
    def __init__(cls, name, base, dic):
        def init(self):
            test(self)

        def test(self):
            for v in cls.s:
                self.__dict__[v.name] = v.value

        cls.__init__ = init

class B(metaclass=A):
    s = PlantSpecimenTerms


if __name__ == "__main__":

    b = B()
    print(b.__dict__)



