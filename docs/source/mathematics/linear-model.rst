.. _linear-model:

Linear Model
============

The main optimizer is :code:`LPOptimizer`. It creates linear programming problem representing network adequacy. We will see mathematics problem, step by step

#. Basic adequacy equations
#. Add lack of adequacy terms (lost of load and spillage)

    As you will see, :math:`\Gamma_x` represents a quantity in network, :math:`\overline{\Gamma_x}` is the maximum, :math:`\underline{\Gamma_x}` is the minimum, :math:`\overline{\underline{\Gamma_x}}` is the maximum and minimum a.k.a it's a forced quantity. Upper case grec letter is for quantity, and lower case grec letter is for cost :math:`\gamma_x` associated to this quantity.

Basic adequacy
--------------

Let's begin by the first adequacy behavior. We have a graph :math:`G(N, L)` with :math:`N` nodes on the graph and :math:`L`  unidirectional edges on this graph.

Variables
*********

* :math:`n \in N` a node belongs to graph

* :math:`T \in \mathbb{Z}_+` time horizon

Edge variables

* :math:`l \in L` an unidirectional edge belongs to graphs

* :math:`\overline{\Gamma_l} \in \mathbb{R}^T_+` maximum power transfert capacity for :math:`l`

* :math:`\Gamma_l \in \mathbb{R}^T_+` power transfered inside :math:`l`

* :math:`\gamma_l \in \mathbb{R}^T_+` proportional cost when :math:`\Gamma_l` is used

* :math:`L^n_\uparrow \subset L` set of edges with direction to node :math:`n` (i.e. importation for :math:`n`)

* :math:`L^n_\downarrow \subset L` set of edges with direction from node :math:`n` (i.e. exportation for :math:`n`)


Productions variables

* :math:`P^n` set of productions attached to node :math:`n`

* :math:`p \in P^n` a production inside set of productions attached to node :math:`n`

* :math:`\overline{\Gamma_p} \in \mathbb{R}^T_+` maximum power capacity available for :math:`p` production.

* :math:`\Gamma_p \in \mathbb{R}^T_+` power capacity of :math:`p` used during adequacy

* :math:`\gamma_p \in \mathbb{R}^T_+` proportional cost when :math:`\Gamma_p` is used

Consumptions variables

* :math:`C^n` set of consumptions attached to node :math:`n`

* :math:`c \in C^n` a consumption inside set of consumptions attached to node :math:`n`

* :math:`\underline{\overline{\Gamma_c}} \in \mathbb{R}^T_+` forced consumptions of :math:`c` to sustain.

Objective
*********

.. math::
    \begin{array}{rcl}
    objective & = & \min{\Omega_{transmission} + \Omega_{production}} \\
    \Omega_{transmission} &=& \sum^{L}_{l}{\Gamma_l*{\gamma_l}} \\
    \Omega_{production} & = & \sum^N_n \sum^{P^n}_{p}{\Gamma_p * {\gamma_p}}
    \end{array}

Constraint
**********

First constraint is from Kirschhoff law and describes balance between productions and consumptions

.. math::
    \begin{array}{rcl}
    \Pi_{kirschhoff} &:& \forall n &,& \sum^{C^n}_{c}{\underline{\overline{\Gamma_c}}} + \sum^{L^n_{\downarrow}}_{l}{ \Gamma_l } = \sum^{P^n}_{p}{ \Gamma_p } + \sum^{L^n_{\uparrow}}_{l}{ \Gamma_l }
    \end{array}

Then productions and edges need to be bounded

.. math::
    \begin{array}{rcl}
    \Pi_{Edge\ bound} &:& \forall l \in L &,&  0 \le \Gamma_{l} \le \overline{\Gamma_l} \\
    \Pi_{Prod\ bound} &:&
    \left\{ \begin{array}{cl}
    \forall n \in N \\
    \forall p \in P^n
    \end{array} \right. &,& 0 \le \Gamma_p \le \overline{\Gamma_p}
    \end{array}


Lack of adequacy
--------------

Variables
*********

Sometime, there are a lack of adequacy because there are not enough production, called *lost of load*.

    Like :math:`\Gamma_x` means quantity present in network, :math:`\Lambda_x` represents a lack in network (consumption or production) to reach adequacy. Like for :math:`\Gamma_x`, lower case grec letter :math:`\lambda_x` is for cost associated to this lack.

* :math:`\Lambda_c \in \mathbb{R}^T_+` lost of load for :math:`c` consumption

* :math:`\lambda_c \in \mathbb{R}^T_+` proportional cost when :math:`\Lambda_c` is used

Objective
*********

Objective has a new term

.. math::
    \begin{array}{rcl}
    objective & = & \min{\Omega_{transmission} + \Omega_{production}} + \underbrace{\Omega_{lol}}\\
    \Omega_{lol} & = & \sum^N_n \sum^{C^n}_{c}{\Lambda_c * {\lambda_c}}
    \end{array}

Constraints
**********

Kirschhoff law needs an update too. Lost of Load is represented like a *fantom* import of energy to reach adequacy.

.. math::
    \begin{array}{rcl}
        \Pi_{kirschhoff} &:& \forall n &,& \sum^{C^n}_{c}{\underline{\overline{\Gamma_c}}} + \sum^{L^n_{\downarrow}}_{l}{ \Gamma_l } = \sum^{P^n}_{p}{ \Gamma_p } + \sum^{L^n_{\uparrow}}_{l}{ \Gamma_l } + \underbrace{\sum^{C^n}_{c}{ \Lambda_c }}
    \end{array}

Lost of load must be bounded

.. math::
    \begin{array}{rcl}
    \Pi_{Lol\ bound} &:&
    \left\{ \begin{array}{cl}
    \forall n \in N \\
    \forall c \in C^n
    \end{array} \right. &,& 0 \le \Lambda_c \le \overline{\underline{\Gamma_c}}
    \end{array}
