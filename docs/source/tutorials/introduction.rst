Get Started
===========

Install
^^^^^^^

You can directly install hadar by pip::

  pip install hadar

Two Node Example
^^^^^^^^^^^^^^^^

For example, a electric grid can have some nodes wich produce too more power and some nodes wich produce not enough power.

.. image:: https://mermaid.ink/img/eyJjb2RlIjoiZ3JhcGggTFJcblx0QVtBPGJyLz5sb2FkPTIwPGJyLz5wcm9kPTMwXSAtLT5CW0I8YnIvPmxvYWQ9MjA8YnIvPnByb2Q9MTBdXG5cdFx0XHRcdFx0IiwibWVybWFpZCI6eyJ0aGVtZSI6ImRlZmF1bHQifSwidXBkYXRlRWRpdG9yIjpmYWxzZX0

In this case, A produce 10 more and B need 10 more. Perform adequecy is quiet easy : A will share 10 to B

.. image:: https://mermaid.ink/img/eyJjb2RlIjoiZ3JhcGggTFJcblx0QVtBPGJyLz5sb2FkPTIwPGJyLz5wcm9kPTMwXSAtLT4gfHNoYXJlIDEwfCBCW0I8YnIvPmxvYWQ9MjA8YnIvPnByb2Q9MTBdXG5cdFx0XHRcdFx0IiwibWVybWFpZCI6eyJ0aGVtZSI6ImRlZmF1bHQifX0


Hadar compute adequacy from simple to complex network. For example, to compute above network, just few line need::

   from hadar.solver.input import *
   from hadar.solver.study import solve

   study = Study(['a', 'b']) \
       .add_on_node('a', data=Consumption(cost=10 ** 6, quantity=[20], type='load')) \
       .add_on_node('a', data=Production(cost=10, quantity=[30], type='prod')) \
       .add_on_node('b', data=Consumption(cost=10 ** 6, quantity=[20], type='load')) \
       .add_on_node('b', data=Production(cost=20, quantity=[10], type='prod')) \
       .add_border(src='a', dest='b', quantity=[10], cost=2) \

   res = solve(study)

