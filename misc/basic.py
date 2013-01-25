import math

def chunks(l, n):
    """ Yield successive n-sized chunks from l
        as described in:
        http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
    """
    if n != math.ceil(n):
        n = math.ceil(n)
    
    n = int(n)

    for i in range(0, len(l), n):
        yield l[i:i+n]


if __name__ == "__main__":
    """ testing chunks function """
    import pprint
    pprint.pprint(list(chunks(range(10, 75), 10)))
    pprint.pprint(list(chunks(range(1,100), 100/3.0)))

