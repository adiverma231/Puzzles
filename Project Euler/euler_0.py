'''
A number is a perfect square, or a square number, if it is the square of a positive integer.
For example, 25 is a square number because 5*5=25; it is also an odd square.

The first 5 square numbers are: 1, 4, 9, 16, 25, and the sum of the odd squares is 35.

Among the first 624 thousand square numbers, what is the sum of all the odd squares?
'''

n = 312000 #624000 / 2 gives odd numbers in range [1, 623999]
print(n * (2*n - 1) * (2*n + 1) // 3)
