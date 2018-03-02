try:
    import broqer.utils.rx_extension
    # this is needed to register the class and object extensions to rx.Observable
except ImportError:
    pass