'''
By considering the terms in the Fibonacci sequence whose values do not exceed four million, find the sum of the even-valued terms.
'''

a, b, sum = 0, 1, 0
while b < 4000000:
    sum += b if (b % 2 == 0) else 0
    a, b = b, a + b
    
print(sum)
