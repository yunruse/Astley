'''Method for displaying a function signature.'''

def reprSignature(args, argDefaults, argRest, kwArgs, kwDefaults, kwRest, *a, **q):
    n_required = len(args) - len(argDefaults)
    words = []
    
    def argify(variables, defaults, isKwargsOnly):
        for n, (name, ann) in enumerate(variables):

            defa = None
            
            if isKwargsOnly:
                defa = defaults[n]
            elif defaults:
                # __defaults__ applies to the tail of the variables
                dindex = n - n_required
                if dindex >= 0:
                    defa = defaults[dindex]
            
            isAnnotated = ann and ann != 'object'

            if isAnnotated and defa:
                words.append('{}: {} = {}'.format(name, ann, defa))
            elif isAnnotated:
                words.append('{}: {}'.format(name, ann))
            elif defa:
                words.append('{}={}'.format(name, defa))
            else:
                words.append(name)

    argify(args, argDefaults, False)
    
    if argRest:
        words.append('*' + str(argRest))
    elif kwArgs:
        words.append('*')

    argify(kwArgs, kwDefaults, True)

    if kwRest:
        words.append('**' + str(kwRest))

    return ', '.join(words)

def funcSignature(f):
    '''Return arguments from compiled function.'''
    c = f.__code__
    n = c.co_argcount
    n_k = c.co_kwonlyargcount
    
    hasKwargs = (c.co_flags & 0b0001000) >> 3
    hasArgs = (c.co_flags & 0b0000100) >> 2
    
    notate = lambda q: [(name, f.__annotations__.get(name, object).__name__) for name in q]
    args = notate(c.co_varnames[:n])
    kwArgs = notate(c.co_varnames[n:n+n_k])
    
    argRest = c.co_varnames[n+1] if hasArgs else None
    kwRest = c.co_varnames[n+1+hasArgs] if hasKwargs else None
    
    argDefaults = f.__defaults__ or tuple()
    kwDefaults = f.__kwdefaults__ or tuple()

    return reprSignature(args, argDefaults, argRest, kwArgs, kwDefaults, kwRest)
