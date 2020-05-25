Analyzer
========

For a high abstraction and to be agnostic about technology, Hadar uses objects as glue for optimizer. Objects are cool, but are too complicated to manipulated for data analysis. Analyzer contains tools to help analyzing study result.

Today, there is only :code:`ResultAnalyzer`, with two features level:

* **high level ** user asks directly to compute global cost and global remain capacity, etc.

* **low level ** user asks *raw* data represented inside pandas Dataframe.

Before speaking about this features, let's see how data are transformed.

Flatten Data
---------

As said above, object is nice to encapsulate data and represent it into agnostic form. Objects can be serialized into JSON or something else to be used by another software maybe in another language. But keep object to analyze data is awful.

Python has a very efficient tool for data analysis : pandas. Therefore challenge is to transform object into pandas Dataframe. Solution used is to flatten data to fill into table.

Consumption
***********

For example with consumption. Data into :code:`Study` is cost and asked quantity. And in :code:`Result` it's cost (same) and given quantity. This tuple *(cost, asked, given)* is present for each node, each consumption attached on this node, each scenario and each timestep. If we want to flatten data, we need to fill this table

+------+------+------+------+------+------+------+
| cost | asked| given| node | name | scn  |  t   |
+------+------+------+------+------+------+------+
| 10   | 5    | 5    | fr   | load | 0    |  0   |
+------+------+------+------+------+------+------+
| 10   | 7    | 7    | fr   | load | 0    |  1   |
+------+------+------+------+------+------+------+
| 10   | 7    | 5    | fr   | load | 1    |  0   |
+------+------+------+------+------+------+------+
| 10   | 6    | 6    | fr   | load | 1    |  1   |
+------+------+------+------+------+------+------+
| ...  | ...  | ...  | ...  | ...  | ..   | ...  |
+------+------+------+------+------+------+------+

It is the purpose of :code:`_build_consumption(study: Study, result: Result) -> pd.Dataframe` to build this array

Production
**********

Production follow the same pattern. However, they don't have *asked* and *given* but *available* and *used* quantity. Therefore table looks like

+------+------+------+------+------+------+------+
| cost | avail| used | node | name | scn  |  t   |
+------+------+------+------+------+------+------+
| 10   | 100  | 21   | fr   | coal | 0    |  0   |
+------+------+------+------+------+------+------+
| 10   | 100  | 36   | fr   | coal | 0    |  1   |
+------+------+------+------+------+------+------+
| 10   | 100  | 12   | fr   | coal | 1    |  0   |
+------+------+------+------+------+------+------+
| 10   | 100  | 81   | fr   | coal | 1    |  1   |
+------+------+------+------+------+------+------+
| ...  | ...  | ...  | ...  | ...  | ..   | ...  |
+------+------+------+------+------+------+------+

It's done by :code:`_build_production(study: Study, result: Result) -> pd.Dataframe` method.


Link
****

Link follow the same pattern. Hierarchical structure naming change. There are not *node* and *name* but *source* and *destination*. Therefore table looks like.

+------+------+------+------+------+------+------+
| cost | avail| used | src  | dest | scn  |  t   |
+------+------+------+------+------+------+------+
| 10   | 100  | 21   | fr   | uk   | 0    |  0   |
+------+------+------+------+------+------+------+
| 10   | 100  | 36   | fr   | uk   | 0    |  1   |
+------+------+------+------+------+------+------+
| 10   | 100  | 12   | fr   | uk   | 1    |  0   |
+------+------+------+------+------+------+------+
| 10   | 100  | 81   | fr   | uk   | 1    |  1   |
+------+------+------+------+------+------+------+
| ...  | ...  | ...  | ...  | ...  | ..   | ...  |
+------+------+------+------+------+------+------+

It's done by :code:`_build_link(study: Study, result: Result) -> pd.Dataframe` method.


Low level analysis
------------------

When you observe flat data, there are two kind of data. *Content* like cost, given, asked and *index* describes by node, name, scn, t.

Low level API analysis provided by :code:`ResultAnalyzer` lets user to

#. Organize index level, for example set time, then scenario, then name, then node.
#. Filter index, for example just time from 10 to 150, just 'fr' node, etc

User can said, *I want 'fr' node productions for first scenario to 50 until 60 timestep.* In this cas :code:`ResultAnalyzer` will return

+------+------+------+------+------+
|      |      | used | cost | avail|
+------+------+------+------+------+
| t    | name | 21   | fr   | uk   |
+------+------+------+------+------+
| 50   | oil  | 36   | fr   | uk   |
+      +------+------+------+------+
|      | coal | 12   | fr   | uk   |
+------+------+------+------+------+
| 60   | oil  | 81   | fr   | uk   |
+      +------+------+------+------+
| ...  | ...  | ...  | ...  | ...  |
+------+------+------+------+------+

If first index like node and scenario has only one element, there are removed.

This result can be done by this line of code. ::

    agg = hd.ResultAnalyzer(study, result)
    df = agg.agg_prod(agg.inode['fr'], agg.scn[0], agg.itime[50:60], agg.iname)

As you can see, user select index hierarchy by sorting :code:`agg.ixxx` . Then user specify filter by :code:`agg.ixxx[yy]`.

Behind this mechanism, there are :code:`Index` objects. As you can see directly in the code ::

    @property
    def inode(self) -> NodeIndex:
        """
        Get a node index to specify node slice to aggregate consumption or production.

        :return: new instance of NodeIndex()
        """
        return NodeIndex()


Each kind of index has to inherent from this class. :code:`Index` object encapsulate column metadata to use and range of filtered elements to keep (accessible by overriding :code:`__getitem__` method). Then, Hadar has child classes with good parameters : :code:`NameIndex` , :code:`NodeIndex` , :code:`ScnIndex` , :code:`TimeIndex` , :code:`SrcIndex` , :code:`DestIndex` . For example you can find below :code:`NodeIndex` implementation ::

    class NodeIndex(Index[str]):
        """Index implementation to filter nodes"""
        def __init__(self):
            Index.__init__(self, column='node')


TODO index ULM

Index instantiation are completely hidden for user. It created implicitly when user types :code:`agg.ixxx[yy]`. Then, hadar will

#. check that mandatory indexes are given with :code:`_assert_index` method.

#. pivot table to recreate indexing according to filter and sort asked with :code:`_pivot` method.

#. remove one-size top-level index with :code:`_remove_useless_index_level` method.

As you can see, low level analyze provides efficient method to extract data from adequacy study result. However data returned remains a kind of *roots* and is not ready for business purposes.

High Level Analysis
-------------------

Unlike low level, high level focus on provides ready to use data. Unlike low level, features should be designed one by one for business purpose. Today we have 2 features:

* :code:`get_cost(self, node: str) -> np.ndarray:` method which according to node given returns a matrix (scenario, horizon) shape with summarize cost.

* :code:`get_balance(self, node: str) -> np.ndarray` method which according to node given returns a matrix (scenario, horizon) shape with exchange balance (i.e. sum of exportation minus sum of importation)



































j
