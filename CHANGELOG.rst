=========
Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

Unreleased
----------

[0.1.0] - 2026-02-24
--------------------

Added
~~~~~

- Initial release of the ``telegram-sender`` library.
- Core sender implementation with support for various message types and responses.
- Flexible runner system for executing Telegram client operations.
- Comprehensive set of sending strategies:
    - ``RetryStrategy``: Automatic retry logic for failed requests.
    - ``RateLimitStrategy``: Throttling to respect Telegram API limits.
    - ``TimeoutStrategy``: Execution time constraints.
    - ``JitterStrategy``: Randomized delays to avoid detection and collisions.
    - ``DelayStrategy``: Fixed interval between messages.
    - ``RequeueStrategy``: Re-queueing logic for specific failure modes.
    - ``CompositeStrategy``: Combining multiple strategies for complex workflows.
- Media support for various Telegram types (Photos, Videos, Documents, etc.).
- Type-safe base models using Pydantic.
- OS-specific enums and metadata handling.
- Development environment configuration with ``ruff``, ``mypy``, and ``pre-commit``.
