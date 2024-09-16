import logging
import threading

class ScheduledCall:
    def __init__(self, func, time):
        self.func = func
        self.time = time
        self.__set_interval()

    def __str__(self):
        return f'{self.time}: {self.call}'

    def __set_interval(self):
      def wrapper():
        self.__set_interval()
        logging.info(f'Calling {self.func.__name__} now after waiting {self.time} seconds.')
        self.func()
      logging.info(f'Scheduling next call to {self.func.__name__} in {self.time} seconds.')
      t = threading.Timer(self.time, wrapper)
      t.start()
