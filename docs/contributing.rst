Contributing
============

Development setup
-----------------

.. code-block:: bash

   git clone https://github.com/GrehBan/telegram-sender.git
   cd telegram-sender
   uv sync --group dev

This installs the runtime dependencies plus development tools.

Code style
----------

* **Line length**: 79 characters.
* **Formatter**: ``ruff format`` (double quotes, space indentation).
* **Linter**: ``ruff check`` with the following rule sets enabled:

  - ``E`` --- pycodestyle errors
  - ``F`` --- pyflakes
  - ``C4`` --- flake8-comprehensions
  - ``Q`` --- flake8-quotes
  - ``RET`` --- flake8-return
  - ``I`` --- isort (built into ruff)
  - ``UP`` --- pyupgrade
  - ``T10`` --- flake8-debugger

* **Import order**: ``ruff`` isort profile with ``src`` as first-party.
* **Type checker**: ``mypy`` in strict mode with the Pydantic plugin.

Running checks
--------------

.. code-block:: bash

   # Lint
   uv run ruff check telegram_sender/

   # Format (check only)
   uv run ruff format --check telegram_sender/

   # Format (apply)
   uv run ruff format telegram_sender/

   # Type check
   uv run mypy telegram_sender/

All three must pass cleanly before merging.

Project layout
--------------

.. code-block:: text

   telegram_sender/
   +-- __init__.py
   +-- __meta__.py              # version string
   +-- enums/
   |   +-- os.py                # OS enum
   +-- types/
   |   +-- base.py              # BaseType (Pydantic base)
   |   +-- media.py             # Media types
   +-- client/
       +-- sender/
       |   +-- protocols.py     # IMessageSender protocol
       |   +-- sender.py        # MessageSender implementation
       |   +-- request.py       # MessageRequest model
       |   +-- response.py      # MessageResponse model
       +-- runner/
       |   +-- protocols.py     # ISenderRunner protocol
       |   +-- runner.py        # SenderRunner implementation
       +-- strategies/
           +-- protocols.py     # ISendStrategy protocol
           +-- composite.py     # CompositeStrategy
           +-- delay.py         # DelayStrategy
           +-- requeue.py       # RequeueStrategy
           +-- retry.py         # BaseRetryStrategy, RetryStrategy
           +-- jitter.py        # JitterStrategy
           +-- rate_limit.py    # RateLimiterStrategy
           +-- timeout.py       # TimeoutStrategy

Conventions
-----------

* All core interfaces are ``typing.Protocol`` classes in ``protocols.py``
  files.
* All Pydantic models use ``frozen=True`` (immutable).
* All logging uses ``logging.getLogger(__name__)`` with ``%``-style
  formatting (no f-strings in logger calls).
* Google-style docstrings in English on all public classes and methods.
