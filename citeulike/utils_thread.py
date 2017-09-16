
import threading

def execute_in_parallel(lambda_list, timeout_seconds = None):
    """
        Execute a list of functions in parallel. There is no support for the max number of tasks executed in parallel.
        The functions must take no input.
    """
    threads = []

    for function in lambda_list:
        thread = threading.Thread(target = function)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join(timeout_seconds)