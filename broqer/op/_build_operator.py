def build_operator(operator_cls):
  def _op(*args, **kwargs):
    def _build(publisher):
      return operator_cls(publisher, *args, **kwargs)
    return _build
  return _op