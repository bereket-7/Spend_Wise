class CalculatorService:
    @staticmethod
    def add(x, y):
        return x + y

    @staticmethod
    def subtract(x, y):
        return x - y

    @staticmethod
    def multiply(x, y):
        return x * y

    @staticmethod
    def divide(x, y):
        if y == 0:
            raise ValueError("Division by zero is not allowed")
        return x / y
    
    @staticmethod
    def power(x, y):
        return x ** y

    @staticmethod
    def absolute_value(x):
        return abs(x)

    @staticmethod
    def square_root(x):
        if x < 0:
            raise ValueError("Square root of a negative number is not allowed")
        return x ** 0.5

    @staticmethod
    def factorial(x):
        if x < 0:
            raise ValueError("Factorial of a negative number is not defined")
        if x == 0:
            return 1
        result = 1
        for i in range(1, x + 1):
            result *= i
        return result
