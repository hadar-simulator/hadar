Overview
========

Welcome to the Hadar Architecture Documentation.

Hadar purpose is to be *an adequacy library for everyone*.
Term *everyone* is important, Hadar must be such easy that everyone can use it.
And Hadar must be such flexible that everyone business can use it or customize it.

**Why these goals ?**

We design Hadar in the same spirit of python libraries like numy or scipy, and moreover like scikit-learn.
Before scikit-learn, people who want to develop machine learning have to had strong skill in mathematics background to develop their own code.
Some *ready to go* codes existed but were not easy to use and flexible.

Scikit-learn release the power of machine learning by abstract complex algorithms into very straight forward API.
It was designed like a toolbox to handle full machine learning framework, where user can juste assemble scikit-learn component or build their own.

Hadar want to be the next scikit-learn for adequacy.
Hadar has to be easy to use and flexible, which if we translate into architecture terms become **high abstraction level** and **independent modules**.


Independent modules
-------------------

User has the choice : Use only Hadar components, assemble them and create a full solution to generate, solve and analyze adequacy study. Or build their parts.


To reach this constraint, we split Hadar into 4 main modules which can be use together or apart :

- **workflow:** module used to generate data study. Hadar handle deterministic computation like stochastic. For stochastic computation user needs to generate many scenarios. Workflow will help user by providing a highly customizable pipeline framework to transform and generate data.


- **optimizer:** more complex and mathematical module. User will use it to describe study adequacy to resolve. No need to understand mathematics, Hadar will handle data input given and translate it to a linear optimization problem before to call a solver.

- **analyzer:** input data given to optimizer and output date with study result can be heavy to analyze. To avoid that every user build their own toolbox, we develop the most used features once for everyone.

- **viewer** analyzer output will be numpy matrix or pandas Dataframe, it great but not enough to analyze result. Viewer uses the analyzer feature and API to generate graphics from study data.

As said, these modules can be used together to handle complet adequacy study lifecycle or used seperately.

TODO graph architecture module


High Abstraction API
--------------------

Each above modules are like a tiny independent libraries. Therefore each module has a high level API.
High abstraction, is a bit confuse to handle and benchmark. For us a high abstraction is when user doesn't need to know mathematics or technicals stuffs when he uses library.

Scikit-learn is the best example of high abstraction level API. For example, if we just want to start a complet SVM research
::

    from sklean.svm import SVR
    svm = SVR()
    svm.fit(X_train, y_train)
    y_pred = svm.predict(X_test)


How many people using this features know that scikit-learn tries to project data into higher space to find a linear regression inside. And to accelerate computation, it uses mathematics feature called *a kernel trick* because problem respect strict requirements ? Perhaps just few people and it's all the beauty of an high level API, it hidden background gear.


Hadar tries to keep this high abstraction features. Look at the *Get Started* example
::

    import hadar as hd
    
    study = hd.Study(['a', 'b'], horizon=3) \
      .add_on_node('a', data=hd.Consumption(cost=10 ** 6, quantity=[20, 20, 20], name='load')) \
      .add_on_node('a', data=hd.Production(cost=10, quantity=[30, 20, 10], name='prod')) \
      .add_on_node('b', data=hd.Consumption(cost=10 ** 6, quantity=[20, 20, 20], name='load')) \
      .add_on_node('b', data=hd.Production(cost=20, quantity=[10, 20, 30], name='prod')) \
      .add_link(src='a', dest='b', quantity=[10, 10, 10], cost=2) \
      .add_link(src='b', dest='a', quantity=[10, 10, 10], cost=2) \
    
    
    optim = hd.LPOptimizer()
    res = optim.solve(study)


Create a study like you will draw it on a paper. Put your nodes, attach some production, consumption, link and run optimizer.


Go Next
-------

Now goals are fixed, we can go deeper into specific module documentation.
All architecture focuses on : High Abstraction and Independent module. You can also read the best practices guide to understand more development choice made in Hadar.


Let't start code explanation.

