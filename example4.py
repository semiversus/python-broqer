# using rxpy Observable from topic
# note: .publish is used without .propose

from broqer.hub import Hub
from rx import Observable

hub=Hub()

def on_result_change(msg):
    print('Topic "result" changed: %s'%msg)

hub['result'].subscribe(on_result_change)

message_observable=Observable.from_topic(hub['message'])
message_observable \
    .combine_latest(Observable.from_topic(hub['value']), lambda m,v:m+' '+str(v)) \
    .do_after_next(print) \
    .publish_topic(hub['result']) \
    .subscribe()

hub['message'].publish('The value is')
hub['value'].publish(5)
hub['value'].publish(7)
hub['message'].publish('So ya see')