# FUNction searCH

A simpler version of [FunSearch](https://github.com/google-deepmind/funsearch).

Able to iteratively update a python program.
For example, we can use funch to guess a function
by directly providing the following code and waiting for an answer.

```python
@funch.run
def similarity(seed):
    dist = 0
    for i in range(10):
        dist += (guess(i) - target(i))**2
    return dist

@funch.evolve
def guess(x):
    return 0

def target(x):
    return 3*x + 2
```

## TODO

- [x] parse and run code
- [x] persistent storage
- [ ] LLM integration
- [ ] search the first function
- [ ] search with islands
- [ ] search with insights
- [ ] add some examples
- [ ] diff edit
- [ ] more...
