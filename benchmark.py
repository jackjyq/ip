import timeit

number_tests = 100000

print(
    number_tests
    / timeit.timeit(
        "get_ip_location('1.1.1.1')",
        setup="from main import get_ip_location",
        number=number_tests,
    )
)
