"""
The module contains implementation of the single thread executor.

The class uses standard concurrent.futures.Future to control
scheduled tasks

"""
import heapq
import threading
import time
from collections import namedtuple
from concurrent import futures
from enum import Enum

_Task = namedtuple(
    '_Task',
    ['abs_time', 'priority', 'action', 'args', 'kwargs', 'future'],
)


class TaskQueue(object):
    """
    Priority queue for Task objects providing (time, priority) sorting.

    Class provides facility to order the tasks according to their
    scheduled absolute execution time and priority and aquire tasks
    that are due to be executed
    """

    def __init__(self):
        """Initialize a queue without parameters."""
        self._queue = []

    def schedule_task(self, task):
        """
        Schedule task.

        Parameters
        ----------
        task : Task
            task to schedule
        """
        heapq.heappush(self._queue, (task.abs_time, task.priority, task))

    def empty(self):
        """
        Check if the queue is empty.

        Returns
        -------
        bool
            indication if the queue is empty
        """
        return not self._queue

    def pop_tasks_till_timestamp(self, timestamp):
        """
        Pop tasks with time <= timestamp.

        Parameters
        ----------
        timestamp : float
            absolute time

        Returns
        -------
        list[Task]
            list of poped tasks sorted by time and priority
        """
        tasks = []
        next_task = next(iter(self._queue), None)
        while next_task:
            task_time, _, task = next_task
            if task_time <= timestamp:
                tasks.append(task)
                heapq.heappop(self._queue)
                next_task = next(iter(self._queue), None)
            else:
                break

        return tasks

    def get_time_till_next_task(self, timestamp):
        """
        Return relative time left till the next task execution.

        Parameters
        ----------
        timestamp : float
            absolute timestamp to calculate difference with

        Returns
        -------
        float
            time left till next task scheduled execution
        """
        if not self._queue:
            return None

        return self._queue[0][0] - timestamp

    def get_tasks(self):
        """
        Return scheduled tasks.

        Returns
        -------
        array_like[(int, Task)]
            list of tuples (Task-id, Task) representing scheduled tasks
        """
        return [task[2] for task in self._queue]


class Stopped(Exception):
    """
    Scheduler stoped exception.

    Exception to indicate that the scheduler is stopped and no more
    tasks can be scheduled
    """


class ScopedUnlocker(object):
    """
    Context manager compaitable utility to unlock/lock mutex/condition.

    The utility unlocks on enter and relocks again on exit
    """

    def __init__(self, lock):
        """
        Init the ScopedUnlocker.

        Parameters
        ----------
        lock : lock_like
            synchronization primitive supporting acquire/release
        """
        self.lock = lock

    def __enter__(self):
        """
        Releases the lock.

        Returns
        -------
        ScopedUnlocker
            returnes itself
        """
        self.lock.release()
        return self

    def __exit__(self, e_type, e_value, e_trace):
        """
        Reaquires the lock.

        Parameters
        ----------
        e_type :
            exception type
        e_value :
            exception value
        e_trace :
            exception traceback
        """
        self.lock.acquire()


Future = futures.Future

IMMEDIATE = 0
TOP_PRIO = 0


class SingleThreadExecutor(object):
    """
    Single-thread executor.

    The class provides scheduling facilities to allow management
    and execution of delayed calls

    The tasks scheduled in the executor are referenced via
    concurent.futures.Future
    """

    _statuses = Enum('statuses', ['Running', 'Stopped', 'StoppedSync'])

    def __init__(self):
        """Initialize the class."""
        self._mutex = threading.Lock()
        self._condition = threading.Condition(self._mutex)
        self._tasks = TaskQueue()
        self._time = time.monotonic
        self._status = self._statuses.Stopped
        self._tasks_to_finish = 0

    def run(self):
        """
        Enter processing loop.

        It can block the thread in which it is called
        """
        with self._condition:
            self._tasks_to_finish = 0
            self._status = self._statuses.Running

        while True:
            with self._condition:
                if not self._wait_for_task_to_process(self._condition):
                    break

                self._process_expired_tasks()

    def stop(self, sync=False):
        """
        Stop the execution.

        The call signals that the processing loop should be ended.

        Parameters
        ----------
        sync : bool, optional
            indicates if already scheduled tasks should be finished,
            by default False
        """
        with self._condition:
            self._tasks_to_finish = sum(
                not task.future.cancelled() for task in self._tasks.get_tasks()
            )

            self._status = (
                self._statuses.StoppedSync if sync and self._tasks_to_finish
                else self._statuses.Stopped
            )
            self._condition.notify()

    def schedule_delayed(self, delay, priority, action, *args, **kwargs):
        """
        Schedules task to be executed with delay (current time + delay).

        Parameters
        ----------
        delay : float
            time to delay task execution in fractional seconds
        priority : int
            prioritity of the task (0 is the highest)
        action : executable
            task action
        args : list
            positional arguments to be forwarded to action
        kwargs : dictionary
            named arguments to be forwarded to action

        Raises
        ------
        Stopped
            is raised if the scheduler was stopped

        Returns
        -------
        int
            id of the scheduled task
        """
        stop_requested_statuses = {
            self._statuses.Stopped, self._statuses.StoppedSync,
        }
        with self._condition:
            if self._status in stop_requested_statuses:
                raise Stopped()

            task = _Task(
                self._time() + delay, priority, action, args, kwargs, Future(),
            )
            self._tasks.schedule_task(task)
            self._condition.notify()
        return task.future

    def _wait_for_task_to_process(self, condition):
        while True:
            if self._status == self._statuses.Stopped:
                return False

            should_stop = (
                (self._tasks.empty() or not self._tasks_to_finish)
                and self._status == self._statuses.StoppedSync
            )
            if should_stop:
                self._status = self._statuses.Stopped
                return False

            delay = self._tasks.get_time_till_next_task(self._time())
            if delay is not None and delay <= 0:
                return True

            condition.wait(delay)

    def _process_expired_tasks(self):
        expired_tasks = self._tasks.pop_tasks_till_timestamp(self._time())

        with ScopedUnlocker(self._condition):
            for task in expired_tasks:
                self._process_task(task)
                time.sleep(0)

    def _process_task(self, task):
        task.future.set_running_or_notify_cancel()
        if not task.future.cancelled():
            try:
                task_result = task.action(
                    *(task.args or ()), **(task.kwargs or {}),
                )
            except Exception as ex:
                task.future.set_exception(ex)
            else:
                task.future.set_result(task_result)
            finally:
                if self._status == self._statuses.StoppedSync:
                    self._tasks_to_finish -= 1
