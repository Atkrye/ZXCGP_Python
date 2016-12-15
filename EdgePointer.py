#Stores information about an edge
class EPointer:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    #X coordinate
    def get_x(self):
        return self.x

    #Y coordinate
    def get_y(self):
        return self.y

    #Which I/O on the target is used
    def get_z(self):
        return self.z

    def __str__(self):
        return str(self.x) + ":" + str(self.y) + " - " + str(self.z)

