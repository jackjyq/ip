import timeit

print(
    timeit.timeit(
        "get_ip_location('1.1.1.1')",
        setup="from main import get_ip_location",
        number=100000,
    )
)
