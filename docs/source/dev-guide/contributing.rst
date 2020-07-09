How to Contribute
=================


First off, thank you to considering contributing to Hadar. We believe technology can change the world. But only great community and open source can improve the world.

Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

We try to describe most of Hadar behavior and organization to avoid any *shadow part*. Additionally, you can read *Dev Guide* section or *Architecture* to learn hadar purposes and processes.

What kind of contribution ?
---------------------------

You can participate on Hadar from many ways:

* just use it and spread it !

* write plugin and extension for hadar

* Improve docs, code, examples

* Add new features

**Issue tracker are only for features, bug or improvment; not for support. If you have some question please go to TODO . Any support issue will be closed.**

Feature / Improvement
---------------------

Little changes can be directly send into a pull request. Like :

* Spelling / grammar fixes

* Typo correction, white space and formatting changes

* Comment clean up

* Adding logging messages or debugging output

For all other, you need first to create an issue. If issue receives good feedback. Then you can fork project, work on your side and send a Pull Request

Bug
---

**If you find a security bug, please DON'T create an issue. Contact use at admin@hadar-simulator.org**

First be sure it's a bug and not a misuse ! Issues are not for technical support. To speed up bug fixing (and avoid misuse), you need to clearly explain bug, with most simple step by step guide to reproduce bug. Specify us all details like OS, Hadar version and so on.

Please provide us response to these questions ::

    - What version of Hadar and python are you using ?
    - What operating system and processor architecture are you using?
    - What did you do?
    - What did you expect to see?
    - What did you see instead?


Best Practices
--------------

We try to code the most clear and maintainable software. Your Pull Request has to follow some good practices:


- respect `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ style guide
- name meaningful variables, method, class
- respect `SOLID <https://en.wikipedia.org/wiki/SOLID>`_ , `KISS <https://en.wikipedia.org/wiki/KISS_principle>`_ , `DRY <https://en.wikipedia.org/wiki/Don%27t_repeat_yourself>`_ , `YAGNI <https://en.wikipedia.org/wiki/You_aren%27t_gonna_need_it>`_ principe
- make code easy testable (use dependencies injection)
- test code (at least 80% UT code coverage)
- Add docstring for each class and method.

TL;TR: code as Uncle Bob !
