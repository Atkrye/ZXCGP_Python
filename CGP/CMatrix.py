import math
#Class for defining Complex Matrices
class CMatrix:
    #Parameter is raw 2D array of Complex values
    def __init__(self, init_data):
        self.raw_data = [[0 + 0j for y in range(len(init_data[0]))] for x in range(len(init_data))]
        for i in range(len(init_data)):
            for j in range(len(init_data[i])):
                self.raw_data[i][j] = init_data[i][j]

    #Gets raw representation of the instance
    def get_raw_data(self):
        return self.raw_data

    #Returns string form, reading row by row
    def __str__(self):
        raw_data = self.get_raw_data()
        s = ""
        for j in range(len(raw_data[0])):
            for i in range(len(raw_data)):
                s = s + raw_data[i][j].__str__() + ","
            if j != len(raw_data[0]) - 1:
                s = s + "\n"
        return s

    #Override add operator to perform Matrix addition
    def __add__(self, other):
        raw_data = self.get_raw_data()
        other_data = other.get_raw_data()
        new_data = [[0 + 0j for y in range(len(raw_data[0]))] for x in range(len(raw_data))]
        for i in range(len(raw_data)):
            for j in range(len(raw_data[i])):
                new_data[i][j] = raw_data[i][j] + other_data[i][j]
        return CMatrix(new_data)

    #Override subtraction operator to perform Matrix subtraction
    def __sub__(self, other):
        raw_data = self.get_raw_data()
        other_data = other.get_raw_data()
        new_data = [[0 + 0j for y in range(len(raw_data[0]))] for x in range(len(raw_data))]
        for i in range(len(raw_data)):
            for j in range(len(raw_data[i])):
                new_data[i][j] = raw_data[i][j] - other_data[i][j]
        return CMatrix(new_data)

    #Returns the same matrix with all elements * -1
    def negative(self):
        raw_data = self.get_raw_data()
        new_data = [[0 + 0j for y in range(len(raw_data[0]))] for x in range(len(raw_data))]
        for i in range(len(raw_data)):
            for j in range(len(raw_data[i])):
                new_data[i][j] = -raw_data[i][j]
        return CMatrix(new_data)

    #Performs conventional Matrix multiplication
    def __mul__(self, other):
        raw_data = self.get_raw_data()
        other_data = other.get_raw_data()
        new_data = [[0 + 0j for y in range(len(raw_data[0]))] for x in range(len(other_data))]
        for j in range(len(raw_data[0])):
            for i in range(len(other_data)):
                for k in range(len(raw_data)):
                    new_data[i][j] += raw_data[k][j] * other_data[i][k]
        return CMatrix(new_data)

    #Tensor operator
    def tensor(self, other):
        raw_data = self.get_raw_data()
        other_data = other.get_raw_data()
        other_width = len(other_data)
        other_height = len(other_data[0])
        new_data = [[0 + 0j for y in range(len(raw_data[0]) * other_height)] for x in range(len(raw_data) * other_width)]

        for i in range(len(raw_data)):
            for j in range(len(raw_data[0])):
                for k in range(other_width):
                    for l in range(other_height):
                        new_data[(i * other_width) + k][(j * other_height) + l] = raw_data[i][j] * other_data[k][l]
        return CMatrix(new_data)

    #Optional: Tensor can be used with division operator
    def __truediv__(self,other):
        return self.tensor(other)

w = CMatrix([[1 + 0j, 0 + 0j],[0 + 0j, 1 + 0j]])
h = CMatrix([[math.sqrt(1 / 2) + 0j,math.sqrt(1 / 2) + 0j],[math.sqrt(1 / 2) + 0j, -(math.sqrt(1 / 2)) + 0j]])
CNOT = CMatrix([[1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 1 + 0j, 0 + 0j, 0 + 0j],[0 + 0j, 0 + 0j, 0 + 0j, 1 + 0j],[0 + 0j, 0 + 0j, 1 + 0j, 0 + 0j]])

#print((h / w / w) * (CNOT / w) * (w / CNOT) * (w / h / w))