.. highlight:: shell

==========================
Frequently Asked Questions
==========================

**Question:** How can I simulate "dummy" log filling if I just want to try something out?

**Answer:** You can use our development utility fake_logger. More info on its usage can be found in
`disruption_generator/utils/fake_logger.py`. You can run it for example like this::

   python fake_logger.py --log-file dummy.log --append --max-interval 2 --randomize --target-msg  "FINISH" --seconds 0

------------

**Question:** How can I configure logging levels of `disruption_generator`?

**Answer:** Generally speaking by creating a file called `custom_logging.yaml` in `disruption_generator` directory and
overriding default values in it. More info on this process can be found in `disruption_generator/default_logging.yaml`.
