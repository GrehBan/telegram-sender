Installation
============

Requirements
------------

* **Python 3.14** or newer.
* A Telegram API application (``api_id`` and ``api_hash``) obtained from
  `my.telegram.org <https://my.telegram.org>`_.

Install from source
-------------------

The project uses `uv <https://docs.astral.sh/uv/>`_ as its package manager.

.. code-block:: bash

   git clone https://github.com/GrehBan/telegram-sender.git
   cd telegram-sender
   uv sync

This installs all runtime dependencies:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Package
     - Purpose
   * - ``pyrofork >= 2.3.69``
     - Pyrogram fork --- Telegram MTProto client.
   * - ``tgcrypto >= 1.2.5``
     - Fast cryptography backend for Pyrogram.
   * - ``tg-devices``
     - Random device profile generation.
   * - ``pydantic >= 2.12.5``
     - Data validation and immutable models.
   * - ``qrcode >= 8.2``
     - QR-code login support.
   * - ``typing-extensions >= 4.15.0``
     - Backported typing helpers.
   * - ``uvloop >= 0.21.0``
     - High-performance event loop (Linux / macOS only, non-PyPy).

Development dependencies
------------------------

.. code-block:: bash

   uv sync --group dev

Installs: ``ruff``, ``mypy``, ``pre-commit``, ``isort``.
