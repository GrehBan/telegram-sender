=========
Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[0.2.0] - 2026-02-25
---------------------

Changed
~~~~~~~

- **Architectural Refactor**: Redesigned the strategy system into a three-phase pipeline (Pre-Send, On-Send, Post-Send).
- Updated ``SenderRunner`` to automatically categorize and execute strategies based on these phases.
- Migrated ``RetryStrategy`` and ``JitterStrategy`` from Post-Send to On-Send phase for more robust retry logic.
- Moved class-level ``Args`` documentation to ``__init__`` methods across all core classes.
- Refactored ``MessageSender`` to delegate media dispatch logic to a new centralized ``resolve_media`` utility.
- Renamed ``VoiceNote`` to ``VideoNote`` for consistency with Pyrogram and Telegram naming conventions.
- Moved ``RateLimiterStrategy`` from Post-Send to Pre-Send phase to correctly enforce limits before transmission.

Added
~~~~~

- Added ``PlainSendStrategy`` as the mandatory final fallback in the On-Send pipeline.
- Added a new ``proxy`` module for typed MTProto, SOCKS5, and HTTPS proxy configurations.
- Enhanced ``RequeueStrategy`` with a ``per_request`` flag, allowing for both global and individual message cycle tracking.
- Added ``resolve_timeout`` utility to safely extract flood-wait delays from errors.
- Improved documentation and API reference for the new strategy architecture.
- Added ``.add()`` method to each pipeline phase (``pre_send``, ``on_send``, ``post_send``), enabling runtime strategy registration after construction.
- Comprehensive docstrings added to previously undocumented internal methods and modules.

Fixed
~~~~~

- Fixed ``TimeoutStrategy`` to respect existing responses in the composite chain, preventing duplicate sends.
- Improved ``resolve_timeout`` (and dependent strategies) to use the provided default as a **minimum** delay (using ``max()``), respecting user configuration.
- Corrected type hints in ``SenderRunner`` and strategy protocols to ensure strict type safety.
- Fixed ``MediaGroup`` captioning to correctly attach ``MessageRequest.text`` to the first item in an album.
- Resolved various minor naming inconsistencies across the codebase and documentation.

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
