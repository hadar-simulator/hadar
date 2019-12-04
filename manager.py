def singleton(class_):
    instances = {}
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


@singleton
class DispatcherRegistry:
    def __init__(self):
        self.dispatchers = {}

    def add(self, dispatcher):
        self.dispatchers[dispatcher.name] = dispatcher.actor_ref

    def get(self, name: str):
        return self.dispatchers[name]
