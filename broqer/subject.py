from broqer import Publisher, Subscriber


class Subject(Publisher, Subscriber):
  emit=Publisher._emit