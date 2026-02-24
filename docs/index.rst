telegram-sender
===============

A strategy-driven Telegram message sending library built on
`pyrofork <https://github.com/Mayuri-Chan/pyrofork>`_ with automatic device
profile randomization via
`tg-devices <https://github.com/GrehBan/tg-devices>`_.

Key features:

* **Async-first** --- fully built on ``asyncio``, usable as async context
  managers.
* **Strategy pipeline** --- compose retry, delay, rate-limit, timeout, jitter,
  and requeue behaviours in any order.
* **Device fingerprinting** --- every session gets a randomized device profile
  (model, OS version, app version) to blend in with real clients.
* **Pydantic v2 models** --- immutable, validated request / response objects
  with strict type safety.
* **Protocol-based design** --- all core interfaces are ``typing.Protocol``
  classes, making the library easy to extend and test.

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   architecture
   strategies

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/sender
   api/runner
   api/strategies
   api/types

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
