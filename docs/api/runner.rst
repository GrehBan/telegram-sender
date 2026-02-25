Runner API
==========

.. module:: telegram_sender.client.runner

SenderRunner
------------

.. class:: telegram_sender.client.runner.runner.SenderRunner(sender, *strategies, loop=None)

   Async queue-based runner that processes message requests.

   Wraps an ``IMessageSender`` and applies an optional chain of strategies
   organized into three phases (Pre-Send, On-Send, Post-Send) to every request.
   Runs a background ``asyncio`` task that sequentially pulls requests from a
   queue, executes them, and pushes responses to a separate results queue.

   Use as an async context manager::

       async with SenderRunner(sender, TimeoutStrategy(5), DelayStrategy(2)) as runner:
           await runner.request(req)
           async for resp in runner.results():
               ...

   :param sender: The sender used to dispatch messages.
   :type sender: IMessageSender
   :param \*strategies: Strategies applied to each request. Categorized by
       their base type (Pre, On, or Post).
   :type \*strategies: BasePreSendStrategy | BaseSendStrategy | BasePostSendStrategy
   :param loop: Optional event loop for creating futures. If not provided,
       the running loop is captured lazily.
   :type loop: asyncio.AbstractEventLoop | None

   .. property:: loop
      :type: asyncio.AbstractEventLoop

      The event loop bound to the runner.

   .. property:: task
      :type: asyncio.Task[None]

      The background processing task.

      :raises RuntimeError: If the runner has not been started via the async
          context manager.

   .. method:: request(request) -> asyncio.Future[MessageResponse]
      :async:

      Enqueue a message request for processing.

      :param request: The message request to enqueue.
      :type request: MessageRequest
      :returns: A ``Future`` that resolves to a ``MessageResponse`` once the
          request is handled, or has its exception set if the request fails.

   .. method:: result() -> MessageResponse
      :async:

      Wait for and return the next available response.

      :raises TimeoutError: If no response is available within 1 second.

   .. method:: results() -> AsyncGenerator[MessageResponse, None]
      :async:

      Yield responses as they become available.

      Terminates once the runner is stopped, the background task is done,
      and the response queue is empty.

   .. method:: close() -> None
      :async:

      Signal the runner to stop. Sets the stop event, waits for the
      background task to finish (draining any remaining requests), then
      returns.

   .. method:: run(drain=True) -> None
      :async:

      The request processing loop. Called automatically by
      ``__aenter__``; you do not need to call this directly.

      :param drain: If ``True``, process remaining requests before exiting.
      :type drain: bool

ISenderRunner
-------------

.. class:: telegram_sender.client.runner.protocols.ISenderRunner

   ``typing.Protocol`` defining the runner interface.

   .. method:: run() -> None
      :async:
      :abstractmethod:

   .. method:: request(request) -> asyncio.Future[MessageResponse]
      :async:
      :abstractmethod:

   .. method:: results() -> AsyncGenerator[MessageResponse, None]
      :abstractmethod:

   .. method:: result() -> MessageResponse
      :async:
      :abstractmethod:

Request lifecycle
-----------------

.. code-block:: text

   request(req)
       |
       v
   _requests queue  --[background task]--> _handle_request()
                                               |
                                               v
                                     +-------------------+
                                     |  1. Pre-Send      |
                                     +-------------------+
                                               |
                                               v
                                     +-------------------+
                                     |  2. On-Send       |
                                     |  (incl. PlainSend)|
                                     +-------------------+
                                               |
                                               v
                                     +-------------------+
                                     |  3. Post-Send     |
                                     +-------------------+
                                               |
                                               v
                                       _responses queue
                                               |
                                               v
   Future resolved                 results() yields response

   On exception: Future.set_exception(err)
                 response NOT placed in _responses queue
