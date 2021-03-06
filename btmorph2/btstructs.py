"""
File contains:

    - :class:`PopulationMorphology`
    - :class:`NeuronMorphology`
    - :class:`Tree`
    - :class:`Node`
    - :class:`P3D`
B. Torben-Nielsen (from legacy code).

Daniele Linaro contributed the iterators in  :class:`Tree`.

Sam Sutton refactored and renamed classes, implemented
PopulationMorphology and NeuronMorphology
"""
import sys
import h5py
import numpy as np

from btmorph2.btviz import plot_2D
from btmorph2.btviz import plot_3D
from btmorph2.btviz import animate
from btmorph2.btviz import plot_dendrogram
from numpy import mean, cov, dot, linalg, transpose
from __builtin__ import str


class PopulationMorphology(object):

    '''
    Simple population for use with a simple neuron (:class:`neuron`).

    List of neurons for statistical comparison, no visualisation methods
    '''
    
    neurons = []
    
    def __init__(self, obj):
        """
        Default constructor.

        Parameters
        -----------
        obj : : str, NeuronMorphology, list[NeuronMorphology]
            If obj is str it can either be a SWC file or directory containing
            SWC files. If obj is NeuronMorphology then Population will be
            create with NeuronMorphology, if List of NeuronMorphology then 
            population will be created with that list
        """

        try:
            if isinstance(obj, NeuronMorphology):
                self.add_neuron(obj)

            elif isinstance(obj, str):
                from os import listdir
                from os.path import isfile, isdir, join

                if isdir(obj):
                    files = [f for f in listdir(obj) if (isfile(join(obj, f)) 
                                                         and
                                                         f.endswith('.swc'))]
                    for f in files:
                        n = NeuronMorphology(input_file=join(obj, f))
                        self.add_neuron(n)
                if isfile(obj):
                    n = NeuronMorphology(input_file=join(obj))
                    self.add_neuron(n)

            elif isinstance(obj, list):
                if isinstance(obj[0], NeuronMorphology):
                    for n in obj:
                        self.add_neuron(n)

        except:
            print "Object is not valid type"

    def add_neuron(self, neuron):
        self.neurons.append(neuron)

    def remove_neuron(self, neuron):
        self.neurons.remove(neuron)

    def no_of_neurons(self):
        return len(self.neurons)

    def no_of_bifurcations(self):
        if self.neurons is not None:
            result = []
            for n in self.neurons:
                result.append(n.no_bifurcations())
        return result

    def no_terminals(self):
        if self.neurons is not None:
            result = []
            for n in self.neurons:
                result.append(n.no_terminals())
        return result

    def no_stems(self):
        if self.neurons is not None:
            result = []
            for n in self.neurons:
                result.append(n.no_stems())
        return result

    def total_length(self):
        if self.neurons is not None:
            result = []
            for n in self.neurons:
                result.append(n.total_length())
        return result

    def total_surface(self):
        if self.neurons is not None:
            result = []
            for n in self.neurons:
                result.append(n.total_surface())
        return result

    def total_volume(self):
        if self.neurons is not None:
            result = []
            for n in self.neurons:
                result.append(n.total_volume())
        return result

    def total_dimensions_verbose(self):
        if self.neurons is not None:
            result = []
            for n in self.neurons:
                result.append(n.total_dimensions_verbose())
        return result

    def global_horton_strahler(self):
        if self.neurons is not None:
            result = []
            for n in self.neurons:
                result.append(n.global_horton_strahler())
        return result

    def get_diameters(self):
        if self.neurons is not None:
            result = []
            for n in self.neurons:
                result.append(n.get_diameters())
        return result


class NeuronMorphology(object):

    '''
    Neuron for use with a Tree (:class:`Tree`).

    Essentially a wrapper for Tree Class, represents a neuron object for which
    statistical analysis can be applied to
    '''

    def __init__(self, input_file=None, pca_translate=False,
                 translate_origin=None, width="x", height="z",
                 depth="y"):

        """
        Default constructor.

        Parameters
        -----------
        input_file : :class:`str`
            File name of neuron to be created
        pca_translate : boolean
            Default False. If True, the morphology is translated along the
                first 3 axes of the PCA performed on its compartments. The
                translated morphology is stored and all future references
                (morphometric and visualization) will use the translated
                morphology
        translate_origin : array of floats
            Default None. If set, this is a 3D array to define the location
                of the soma. Format is ['x', 'z', 'y'] The translated
                morphology will be stored. If used in conjunction with the
                pca_translate, the morphology will first be translated
                according to PCA and then moved to the specified soma location
        width : string
            Either "x", "y" or "z" to determine which axis in the SWC format
                corresponds to the internally stored axis.
        height : string
            Either "x", "y" or "z" to determine which axis in the SWC format
                corresponds to the internally stored axis.
        depth : string
            Either "x", "y" or "z" to determine which axis in the SWC format
                corresponds to the internally stored axis.
        """

        axis_config = [0, 0, 0]
        if width is "x":
            axis_config[0] = 0
        elif width is "z":
            axis_config[0] = 1
        elif width is "y":
            axis_config[0] = 2
        if height is "x":
            axis_config[1] = 0
        elif height is "z":
            axis_config[1] = 1
        elif height is "y":
            axis_config[1] = 2
        if depth is "x":
            axis_config[2] = 0
        elif depth is "z":
            axis_config[2] = 1
        elif depth is "y":
            axis_config[2] = 2
        if sum(axis_config) is not 3:
            raise Exception("Axes incorrectly set, \
                             ensure each axis is set correctly")

        self._tree = Tree(input_file, axis_config)
        self._all_nodes = self.tree.get_nodes()

        # compute some of the most used stats +
        self._soma_points, self._bif_points, self._end_points = \
            self.get_points_of_interest()            

        if pca_translate:
            self.get_tree().pca_project_tree()

        if translate_origin is not None:
            rootPos = self.get_tree().get_root().content['p3d'].xyz
            if rootPos[0] != translate_origin[0] and \
                rootPos[1] != translate_origin[1] and \
                    rootPos[2] != translate_origin[2]:

                translate = translate_origin - rootPos
                for n in self.get_tree().get_nodes():
                    n.content['p3d'].xyz = n.content['p3d'].xyz + translate

    def set_tree(self,tree):
        """
        Set the Tree object associated with this NeuronMorphology.
        Not implemented at this moment!!!
        """
        print("set_tree not implemented")
                    
    def get_tree(self):
        """
        Obtain the Tree object contained in this NeuronMorphology.

        Returns
        -------
        root : :class:`Node`
        """
        return self._tree
    tree = property(get_tree, set_tree)

    def plot_3DGL(self, displaysize=(800, 600), zoom=10, poly=True,
                  fast=False, multisample=True, graph=True):

        """
        Gate way to btvizGL3D plot

        Parameters
        -----------
        displaysize : tuple (int, int)
            set size of window, default is 800,600
        zoom : int
            distance from centre to start from
        poly : boolean
            Draw Polygon or Wire frame representation
        fast : boolean
            Increase fps by removing overlapping branches (only if poly = true)
        multisample : boolean
            Improves quality of image through multisample (false improves fps)
        graph : boolean
            Start with Graph enabled (can toggle while running with 'g' key)
        """
        from btmorph2.btvizGL import btvizGL

        window = btvizGL()
        window.Plot(self, displaysize, zoom, poly, fast, multisample, graph)
        window = None

    def animateGL(self, filename, displaysize=(800, 600), zoom=5,
                    poly=True, axis='z', graph=False):

        """
        Gate way to btvizGL

        Parameters
        -----------
        filename : string
            Filename for gif produces (available in captures/animations folder)
        displaysize : tuple (int, int)
            set size of window, default is 800,600
        zoom : int
            distance from centre to start from
        poly : boolean
            Draw Polygon or Wire frame representation
        graph : boolean
            Start with Graph enabled (can toggle while running with 'g' key)

        """
        from btmorph2.btvizGL import btvizGL

        window = btvizGL()
        window.Animate(self, filename, displaysize, zoom, poly, axis, graph)
        window = None

    def plot_3D(self, color_scheme="default", color_mapping=None,
                synapses=None, save_image=None,show_radius=True):

        """
        Gate way to btviz plot_3D_SWC to create object orientated relationship

        3D matplotlib plot of a neuronal morphology. The SWC has to be
        formatted with a "three point soma".
        Colors can be provided and synapse location marked

        Parameters
        ----------
        color_scheme: string
            "default" or "neuromorpho". "neuronmorpho" is high contrast
        color_mapping: list[float] or list[list[float,float,float]]
            Default is None. If present, this is a list[N] of colors
            where N is the number of compartments, which roughly corresponds to
            the number of lines in the SWC file. If in format of list[float],
            this list is normalized and mapped to the jet color map, if in
            format of list[list[float,float,float,float]], the 4 floats represt
            R,G,B,A respectively and must be between 0-255. When not None, this
            argument overrides the color_scheme argument(Note the difference
            with segments).
        synapses : vector of bools
            Default is None. If present, draw a circle or dot in a distinct
            color at the location of the corresponding compartment. This is
            a 1xN vector.
        save_image: string
            Default is None. If present, should be in format
            "file_name.extension", and figure produced will be saved as
            this filename.
        show_radius : boolean
            True (default) to plot the actual radius. If set to False,
            the radius will be taken from `btmorph2\config.py`
        """
        plot_3D(self, color_scheme, color_mapping, synapses, \
                    save_image,show_radius=show_radius)

    def animate(self, color_scheme="default", color_mapping=None,
                synapses=None, save_image="animation", axis="z"):

        """
        Gate way to btviz plot_3D_SWC to create object orientated relationship

        3D matplotlib plot of a neuronal morphology. The SWC has to be
        formatted with a "three point soma".
        Colors can be provided and synapse location marked

        Parameters
        ----------
        color_scheme: string
            "default" or "neuromorpho". "neuronmorpho" is high contrast
        color_mapping: list[float] or list[list[float,float,float]]
            Default is None. If present, this is a list[N] of colors
            where N is the number of compartments, which roughly corresponds to
            the number of lines in the SWC file. If in format of list[float],
            this list is normalized and mapped to the jet color map, if in
            format of list[list[float,float,float,float]], the 4 floats represt
            R,G,B,A respectively and must be between 0-255. When not None, this
            argument overrides the color_scheme argument(Note the difference
            with segments).
        synapses : vector of bools
            Default is None. If present, draw a circle or dot in a distinct
            color at the location of the corresponding compartment. This is
            a 1xN vector.
        save_image: string
            Default is "animation". If present, should be in format
            "file_name", and animation produced will be saved as
            this filename.gif.
        axis: string
            Default is "z". Rotation axis to animate, can be "x","y" or "z"
        """
        animate(self, color_scheme, color_mapping, synapses, save_image, axis)

    def plot_dendrogram(self):
        plot_dendrogram(self)
        
    def plot_2D(self, color_scheme="default", color_mapping=None,
                synapses=None, save_image=None, depth='y',show_radius=True):

        """
        Gate way to btviz plot_2D_SWC to create object orientated relationship

        2D matplotlib plot of a neuronal moprhology. Projection can be in XY
         and XZ.
        The SWC has to be formatted with a "three point soma".
        Colors can be provided

        Parameters
        -----------
        color_scheme: string
            "default" or "neuromorpho". "neuronmorpho" is high contrast
        color_mapping: list[float] or list[list[float,float,float]]
            Default is None. If present, this is a list[N] of colors
            where N is the number of compartments, which roughly corresponds to
            the number of lines in the SWC file. If in format of list[float],
            this list is normalized and mapped to the jet color map, if in
            format of list[list[float,float,float,float]], the 4 floats represt
            R,G,B,A respectively and must be between 0-255. When not None, this
            argument overrides the color_scheme argument(Note the difference
            with segments).
        synapses : vector of bools
            Default is None. If present, draw a circle or dot in a distinct
            color at the location of the corresponding compartment. This is a
            1xN vector.
        save_image: string
            Default is None. If present, should be in format
            "file_name.extension", and figure produced will be saved as
            this filename.
        depth : string
            Default 'y' means that X represents the superficial to deep axis. \
            Otherwise, use 'z' to conform the mathematical standard of having
            the Z axis.

        Notes
        -----
        If the soma is not located at [0,0,0], the scale bar (`bar_L`) and the
         ticks (`bar`) might not work as expected

        """
        plot_2D(self, color_scheme, color_mapping, synapses, \
                    save_image, depth,show_radius=show_radius)

    def get_points_of_interest(self):
        """
        Get lists containting the "points of interest", i.e., soma points,
        bifurcation points and end/terminal points.

        Returns
        -------
        soma_points : list
        bif_points : list
        end_points : list

        """
        soma_points = []
        bif_points = []
        end_points = []

        # updated 2014-01-21 for compatibility with new btstructs2
        for node in self._all_nodes:
            if len(node.children) > 1:
                if node.parent is not None:
                    bif_points.append(node)  # the root is not a bifurcation
            if len(node.children) == 0:
                if node.parent.index != 1:  # "3 point soma",
                                            # avoid the two side branches
                    end_points.append(node)
            if node.parent is None:
                soma_points = node

        return soma_points, bif_points, end_points

    def approx_soma(self):
        """
        *Scalar, global morphometric*

        By NeuroMorpho.org convention: soma surface ~ 4*pi*r^2, \
        where r is the abs(y_value) of point 2 and 3 in the SWC file


        Returns
        -------
        surface : float
             soma surface in micron squared
        """

        r = self._tree.get_node_with_index(1).content['p3d'].radius
        return 4.0*np.pi*r*r

    def no_bifurcations(self):
        """
        *Scalar, global morphometric*

        Count the number of bifurcations points in a complete moprhology

        Returns
        -------
        no_bifurcations : int
             number of bifurcation
        """
        return len(self._bif_points)

    def no_terminals(self):
        """
        *Scalar, global morphometric*

        Count the number of temrinal points in a complete moprhology

        Returns
        -------
        no_terminals : int
            number of terminals
        """
        return len(self._end_points)

    def no_stems(self):
        """
        *Scalar, global morphometric*

        Count the number of stems in a complete moprhology (except the three \
        point soma from the Neuromoprho.org standard)

        Returns
        -------
        no_stems : int
            number of stems
        """
        return len(self._tree.root.children)-2

    def no_nodes(self):
        """
        *Scalar, global morphometric*

        Count the number of nodes in a complete moprhology

        Returns
        -------
        no_nodes: int
            number of stems
        """
        return self._tree.get_nodes().__len__()

    def total_length(self):
        """
        *Scalar, global morphometric*

        Calculate the total length of a complete morphology


        Returns
        -------
        total_length : float
            total length in micron
        """
        L = 0
        # updated 2014-01-21 for compatibility with new btstructs2
        for Node in self._all_nodes:
            n = Node.content['p3d']
            if Node.index not in (1, 2, 3):
                p = Node.parent.content['p3d']
                d = np.sqrt(np.sum((n.xyz-p.xyz)**2))
                L += d
        return L

    def total_surface(self):
        """
        *Scalar, global morphometric*

        Total neurite surface (at least, surface of all neurites excluding
        the soma. In accordance to the NeuroMorpho / L-Measure standard)

        Returns
        -------
        total_surface : float
            total surface in micron squared

        """
        total_surf = 0
        all_surfs = []
        # updated 2014-01-21 for compatibility with new btstructs2
        for Node in self._all_nodes:
            n = Node.content['p3d']
            if Node.index not in (1, 2, 3):
                p = Node.parent.content['p3d']
                H = np.sqrt(np.sum((n.xyz-p.xyz)**2))
                surf = 2*np.pi*n.radius*H
                all_surfs.append(surf)
                total_surf = total_surf + surf
        return total_surf, all_surfs

    def total_volume(self):
        """
        *Scalar, global morphometric*

        Total neurite volume (at least, surface of all neurites excluding
        the soma. In accordance to the NeuroMorpho / L-Measure standard)

        Returns
        -------
        total_volume : float
            total volume in micron cubed
        """
        total_vol = 0
        all_vols = []
        # updated 2014-01-21 for compatibility with new btstructs2
        for Node in self._all_nodes:
            n = Node.content['p3d']
            if Node.index not in (1, 2, 3):
                p = Node.parent.content['p3d']
                H = np.sqrt(np.sum((n.xyz-p.xyz)**2))
                vol = np.pi*n.radius*n.radius*H
                all_vols.append(vol)
                total_vol = total_vol + vol
        return total_vol, all_vols

    def total_dimension(self):
        """
        *Scalar, global morphometric* Overall dimension of the morphology

        Returns
        -------
        dx : float
            x-dimension
        dy : float
            y-dimension
        dz : float
            z-dimension
        """
        dx, dy, dz = self.total_dimensions_verbose()
        return dx, dy, dz

    def total_dimensions_verbose(self):
        """
        *Scalar, global morphometric*

        Overall dimension of the whole moprhology. (No translation of the \
        moprhology according to arbitrary axes.)


        Returns
        -------
        dx : float
            x-dimension
        dy : float
            y-dimension
        dz : float
            z-dimension
        data : list
            minX,maxX,minY,maxY,minZ,maxZ

        """
        minX = sys.maxint
        maxX = -1 * sys.maxint
        minY = sys.maxint
        maxY = -1 * sys.maxint
        minZ = sys.maxint
        maxZ = -1 * sys.maxint
        for Node in self._all_nodes:
            n = Node.content['p3d']
            nx = n.xyz[0]
            ny = n.xyz[1]
            nz = n.xyz[2]
            minX = nx if nx < minX else minX
            maxX = nx if nx > maxX else maxX

            minY = ny if ny < minY else minY
            maxY = ny if ny > maxY else maxY

            minZ = nz if nz < minZ else minZ
            maxZ = nz if nz > maxZ else maxZ
        dx = np.sqrt((maxX-minX)*(maxX-minX))
        dy = np.sqrt((maxY-minY)*(maxY-minY))
        dz = np.sqrt((maxZ-minZ)*(maxZ-minZ))
        return dx, dy, dz, [minX, maxX, minY, maxY, minZ, maxZ]

    def global_horton_strahler(self):
        """
        Calculate Horton-Strahler number at the root
        See :func:`local_horton_strahler`

        Parameters
        ---------

        Returns
        ---------
        Horton-Strahler number at the root
        """
        return self.local_horton_strahler(self._tree.root)

    """
    Local measures
    """
    def get_diameters(self):
        """
        *Vector, local morphometric*

        Get the diameters of all points in the morphology
        """
        diams = []
        for node in self._all_nodes:
            if node.index not in (1, 2, 3):
                diams.append(node.content['p3d'].radius*2.0)
        return diams

    def get_segment_pathlength(self, to_node):
        """
        *Vector, local morphometric*.

        Length of the incoming segment. Between this Node and the soma or
        another branching point. A path is defined as a stretch between
        the soma and a bifurcation point, between bifurcation points,
        or in between of a bifurcation point and a terminal point

        Parameters
        ----------
        to_node : :class:`btmorph.btstructs2.SNode2`
           Node *to* which the measurement is taken

        Returns
        -------
        length : float
            length of the incoming path in micron

        """
        # updated 2014-01-21 for compatibility with new btstructs2
        L = 0
        if self._tree.is_leaf(to_node):
            path = self._tree.path_to_root(to_node)
            L = 0
        else:
            path = self._tree.path_to_root(to_node)[1:]
            p = to_node.parent.content['p3d']
            n = to_node.content['p3d']
            d = np.sqrt(np.sum((n.xyz-p.xyz)**2))
            L = L + d

        for node in path:
            # print 'going along the path'
            n = node.content['p3d']
            if len(node.children) >= 2:  # I arrive at either the soma or a
                                        # branch point close to the soma
                return L
            else:
                p = node.parent.content['p3d']
                d = np.sqrt(np.sum((n.xyz-p.xyz)**2))
                L = L + d

    def get_pathlength_to_root(self, from_node):
        """
        Length of the path between from_node to the root.
        another branching point

        Parameters
        ----------
        from_node : :class:`btmorph.btstructs2.SNode2`

        Returns
        -------
        length : float
            length of the path between the soma and the provided Node

        """

        L = 0
        if self._tree.is_leaf(from_node):
            path = self._tree.path_to_root(from_node)
            L = 0
        else:
            path = self._tree.path_to_root(from_node)[1:]
            p = from_node.parent.content['p3d']
            n = from_node.content['p3d']
            d = np.sqrt(np.sum((n.xyz-p.xyz)**2))
            L = L + d

        for node in path[:-1]:
            # print 'going along the path'
            n = node.content['p3d']
            p = node.parent.content['p3d']
            d = np.sqrt(np.sum((n.xyz-p.xyz)**2))
            L = L + d
        return L

    def get_segment_Euclidean_length(self, to_node):
        """
        Euclidean length to the incoming segment. Between this Node and the
         soma or another branching point

        Parameters
        ----------
        from_node : :class:`btmorph.btstructs2.SNode2`

        Returns
        -------
        length : float
            Euclidean distance *to* provided Node (from soma or first branch
             point with lower order)

        """
        L = 0
        if self._tree.is_leaf(to_node):
            path = self._tree.path_to_root(to_node)
        else:
            path = self._tree.path_to_root(to_node)[1:]

        n = to_node.content['p3d']
        for Node in path:
            if len(Node.children) >= 2:
                return L
            else:
                p = Node.parent.content['p3d']
                d = np.sqrt(np.sum((n.xyz-p.xyz)**2))
                L = d

    def get_Euclidean_length_to_root(self, from_node):
        """
        Euclidean length between the from_node and the root

        Parameters
        ----------
        from_node : :class:`btmorph.btstructs2.SNode2`

        Returns
        -------
        length : float
            length of the path between the soma and the provided Node

        """
        n = from_node.content['p3d']
        p = self._tree.root.content['p3d']
        d = np.sqrt(np.sum((n.xyz-p.xyz)**2))
        return d

    def max_degree(self):
        """
        Maximal degree of any node in a neuronal structure.

        Returns
        -------
        max_degree : float
            Highest degree in a neuronal structure
        """
        # -1: subtract the 2 fake nodes from the 3-point soma position
        return self.degree_of_node(self.tree.root)-2
    
    def degree_of_node(self, node):
        """
        Degree of a Node. (The number of leaf Node in the subneuron mounted at
         the provided Node)

        Parameters
        ----------
        node : :class:`btmorph.btstructs2.SNode2`

        Returns
        -------
        degree : float

        """
        return self.tree.degree_of_node(node)

    def order_of_node(self, node):
        """
        Order of a Node. (Going centrifugally away from the soma, the order
         increases with 1 each time a bifurcation point is passed)

        Parameters
        ----------
        node : :class:`btmorph.btstructs2.SNode2`

        Returns
        -------
        order : float
            order of the subneuron rooted at Node

        """
        return self._tree.order_of_node(node)

    def partition_asymmetry(self, node):
        """
        *Vector, local morphometric*

        Compute the partition asymmetry for a given Node.

        Parameters
        ----------
        node : :class:`btmorph.btstructs2.SNode2`

        Returns
        -------
        partition_asymmetry : float
            partition asymmetry of the subneuron rooted at Node
            (according to vanpelt and schierwagen 199x)

        """
        if node.children is None or len(node.children) == 1:
            return None
        d1 = self._tree.degree_of_node(node.children[0])
        d2 = self._tree.degree_of_node(node.children[1])
        if(d1 == 1 and d2 == 1):
            return 0  # by definition
        else:
            return np.abs(d1-d2)/(d1+d2-2.0)

    def amp(self, a):
        return np.sqrt(np.sum((a)**2))

    def bifurcation_angle_vec(self, node, where='local'):
        """
        *Vector, local morphometric*

        Only to be computed at branch points (_bif_points). Computes the angle
        between the two daughter branches in the plane defined by the
        parent and the two daughters.

        cos alpha = :math:`(a \dot b) / (|a||b|)`

        Parameters
        -----------
        Node : :class:`btmorph.btstructs.Node`
        where : string
            either "local" or "remote". "Local" uses the immediate daughter
            points while "remote" uses the point just before the next
            bifurcation or terminal point.

        Returns
        -------
        angle : float
            Angle in degrees
        """
        child_node1, child_node2 = self._get_child_nodes(node, where=where)
        scaled_1 = child_node1.content['p3d'].xyz - node.content['p3d'].xyz
        scaled_2 = child_node2.content['p3d'].xyz - node.content['p3d'].xyz
        return (np.arccos(np.dot(scaled_1, scaled_2) /
                (self.amp(scaled_1) * self.amp(scaled_2))) /
                (2*np.pi/360))

    def bifurcation_sibling_ratio(self, node, where='local'):
        """
        *Vector, local morphometric*

        Ratio between the diameters of two siblings.

        Parameters
        ----------
        Node : :class:`btmorph.btstructs2.SNode2`
        where : string
            Toggle 'local' or 'remote'

        Returns
        -------
        result : float
            Ratio between the diameter of two siblings
        """
        child1, child2 = self._get_child_nodes(node, where=where)
        radius1 = child1.content['p3d'].radius
        radius2 = child2.content['p3d'].radius
        if radius1 > radius2:
            return radius1 / radius2
        else:
            return radius2 / radius1

    def _get_child_nodes(self, node, where):
        if where == 'local':
            return node.children[0], node.children[1]
        else:
            grandchildren = []
            for child in node.children:
                t_child = self._find_remote_child(child)
                grandchildren.append(t_child)
        return grandchildren[0], grandchildren[1]

    def _find_remote_child(self, node):
        t_node = node
        while len(t_node.children) < 2:
            if len(t_node.children) == 0:
                # print t_node, '-> found a leaf'
                return t_node
            t_node = t_node.children[0]
        # print t_node,' -> found a bif'
        return t_node

    def bifurcation_ralls_power_fmin(self, node, where='local'):
        """
        *Vector, local morphometric*

        Approximation of Rall's ratio using scipy.optimize.fmin.
        The error function is :math:`F={D_{d1}}^n+{D_{d2}}^n-{D_p}^n`

        Parameters
        ----------
        node : :class:`btmorph.btstructs2.SNode2`
        where : string
            either "local" or "remote". "Local" uses the immediate daughter
            points while "remote" uses the point just before the next
            bifurcation or terminal point.

        Returns
        -------
        rr : float
            Approximation of Rall's ratio
        """
        p_diam = node.content['p3d'].radius*2
        child1, child2 = self._get_child_nodes(node, where=where)
        d1_diam = child1.content['p3d'].radius*2
        d2_diam = child2.content['p3d'].radius*2
        # print 'pd=%f,d1=%f,d2=%f' % (p_diam,d1_diam,d2_diam)

        if d1_diam >= p_diam or d2_diam >= p_diam:
            return np.nan

        import scipy.optimize
        mismatch = lambda n: np.abs(np.power(d1_diam, n) +
                                     np.power(d2_diam, n) -
                                     np.power(p_diam, n))
        p_lower = 0.0
        p_upper = 5.0  # THE associated mismatch MUST BE NEGATIVE

        best_n = scipy.optimize.fmin(mismatch,
                                     (p_upper-p_lower)/2.0,
                                     disp=False)
        if 0.0 < best_n < 5.0:
            return best_n
        else:
            return np.nan

    def bifurcation_rall_ratio_classic(self, node, where='local'):
        """
        *Vector, local morphometric*

        The ratio :math:`\\frac{ {d_1}^p + {d_2}^p  }{D^p}` computed with
        :math:`p=1.5`

        Parameters
        -----------
        node : :class:`btmorph.btstructs2.SNode2`
        where : string
            either 'local or 'remote'. 'Local' uses the immediate daughter
            points while "remote" uses the point just before the next
            bifurcation or terminal point.

        Returns
        -------
        rr : float
            Approximation of Rall's ratio

        """
        p_diam = node.content['p3d'].radius*2
        child1, child2 = self._get_child_nodes(node, where=where)
        d1_diam = child1.content['p3d'].radius*2
        d2_diam = child2.content['p3d'].radius*2

        return ((np.power(d1_diam, 1.5) + np.power(d2_diam, 1.5)) /
                np.power(p_diam, 1.5))

    def bifurcation_ralls_power_brute(self, node, where='local', min_v=0,
                                      max_v=5, steps=1000):
        """
        *Vector, local morphometric*

        Approximation of Rall's ratio.
         :math:`D^p = {d_1}^p + {d_2}^p`, p is approximated by brute-force
         checking the interval [0,5] in 1000 steps (by default, but the exact
         search dimensions can be specified by keyworded arguments.

        Parameters
        -----------
        node : :class:`btmorph.btstructs2.SNode2`
        where : string
            either 'local or 'remote'. 'Local' uses the immediate daughter
            points while "remote" uses the point just before the next
            bifurcation or terminal point.

        Returns
        -------
        rr : float
            Approximation of Rall's power, p

        """
        p_diam = node.content['p3d'].radius*2
        child1, child2 = self._get_child_nodes(node, where=where)
        d1_diam = child1.content['p3d'].radius*2
        d2_diam = child2.content['p3d'].radius*2
        # print 'pd=%f,d1=%f,d2=%f' % (p_diam,d1_diam,d2_diam)

        if d1_diam >= p_diam or d2_diam >= p_diam:
            return None

        test_v = np.linspace(min_v, max_v, steps)
        min_mismatch = 100000000000.0
        best_n = -1
        for n in test_v:
            mismatch = ((np.power(d1_diam, n) + np.power(d2_diam, n)) -
                        np.power(p_diam, n))
            # print "n=%f -> mismatch: %f" % (n,mismatch)
            if np.abs(mismatch) < min_mismatch:
                best_n = n
                min_mismatch = np.abs(mismatch)
        return best_n

    def pos_angles(self, x):
        return x if x > 0 else 180 + (180+x)

    def _get_ampl_angle(self, node):
        """
        Compute the angle of this Node on the XY plane and against the origin
        """
        a = np.rad2deg(np.arctan2(node.content['p3d'].y,
                                  node.content['p3d'].x))
        return self.pos_angle(a)

    def local_horton_strahler(self, node):
        """
        We assign Horton-Strahler number to all nodes of a neuron,
         in bottom-up order, as follows:

        If the Node is a leaf (has no children), its Strahler number is one.
        If the Node has one child with Strahler number i, and all other
         children have Strahler numbers less than i, then the Strahler number
         of the Node is i again.
        If the Node has two or more children with Strahler number i, and no
         children with greater number, then the Strahler number of the Node
         is i + 1.
        *If the Node has only one child, the Strahler number of the Node equals
         to the Strahler number of the child
        The Strahler number of a neuron is the number of its root Node.

        See wikipedia for more information: http://en.wikipedia.org/
        wiki/Strahler_number

        Parameters
        ---------
        node : :class:`btmorph.btstructs2.SNode2`
            Node of interest
        Returns
        ---------
        hs : int
            The Horton-Strahler number (Strahler number) of the Node
        """
        # Empy neuron
        if node is None:
            return -1
        # Leaf => HS=1
        if len(node.children) == 0:
            return 1
        # Not leaf
        childrenHS = map(self.local_horton_strahler, node.children)
        if len(node.children) == 1:
            return max(childrenHS + [(min(childrenHS))])
        elif len(node.children) == 2:
            return max(childrenHS + [(min(childrenHS)+1)])
        else:
            return max(childrenHS)        
        

    def get_boundingbox(self):
        '''
        Get minimum and maximum positions in each axis

        Returns
        --------
        minv : 1D array of 3 int
            minimum values of axis in order x,y,z
        maxv : 1D array of 3 int
            maximum values of axis in order x,y,z
        '''
        minv = [0, 0, 0]
        maxv = [0, 0, 0]
        for node in self._all_nodes:
            xyz = node.content['p3d'].xyz
            for i in (0, 1, 2):
                if(xyz[i] < minv[i]):
                    minv[i] = xyz[i]
                if(xyz[i] > maxv[i]):
                    maxv[i] = xyz[i]
        return minv, maxv


class Tree(object):
    """
    Tree for use with a Node (:class:`Node`).

    While the class is designed to contain binary trees (for neuronal
    morphologies)the number of children is not limited. As such,
    this is a generic implementation of a tree structure as a linked list.
    """

    def __init__(self, input_file=None, axis_config=[0, 1, 2]):
        """
        Default constructor.

        Parameters
        -----------
        input_file : :class:`str`
            File name of neuron to be created,
        """
        if input_file is not None:
            # check if SWC file or *NMF* file
            extension = input_file.split(".")[-1] # string after last dot in file_name
            if extension.lower()=="swc":
                self.read_SWC_tree_from_file(input_file)
            elif extension.lower()=="nmf":
                self.read_NMF_tree_from_file(input_file)
        if (axis_config[0] is not 0 or axis_config[1]
                is not 1 or axis_config[2] is not 2):  # switch axis
            if axis_config[0] == 0:
                self.switch_axis(1, 2)
            if axis_config[1] == 0:
                self.switch_axis(1, 2)
            elif axis_config[1] == 1:
                self.switch_axis(0, 2)
            elif axis_config[1] == 2:
                self.switch_axis(0, 1)
                self.switch_axis(1, 2)
            if axis_config[2] == 2:
                self.switch_axis(0, 1)

    def switch_axis(self, a, b):
        for n in self.get_nodes():
            tA = n.content['p3d'].xyz[a]
            tB = n.content['p3d'].xyz[b]
            n.content['p3d'].xyz[a] = tB
            n.content['p3d'].xyz[b] = tA

    def set_root(self, node):

        """
        Set the root Node of the tree

        Parameters
        -----------
        Node : :class:`Node`
            to-be-root Node
        """
        node.parent = None
        self._root = node

    def get_root(self):
        """
        Obtain the root Node

        Returns
        -------
        root : :class:`Node`
        """
        return self._root
    root = property(get_root, set_root)

    def is_root(self, node):

        """
        Check whether a Node is the root Node

        Parameters
        -----------
        node : :class:`Node`
            Node to be check if root

        Returns
        --------
        is_root : boolean
            True is the queried Node is the root, False otherwise
        """
        if node.parent is None:
            return True
        else:
            return False

    def is_leaf(self, node):

        """
        Check whether a Node is a leaf Node, i.e., a Node without children

        Parameters
        -----------
        node : :class:`Node`
            Node to be check if leaf Node

        Returns
        --------
        is_leaf : boolean
            True is the queried Node is a leaf, False otherwise
        """
        if len(node.children) == 0:
            return True
        else:
            return False

    def is_branch(self, node):

        """
        Check whether a Node is a branch Node, i.e., a Node with two children

        Parameters
        -----------
        node : :class:`Node`
            Node to be check if branch Node

        Returns
        --------
        is_leaf : boolean
            True is the queried Node is a branch, False otherwise
        """
        if hasattr(node, 'children'):
            if len(node.children) == 2:
                return True
            else:
                return False
        else:
            return None

    def add_node_with_parent(self, node, parent):

        """
        Add a Node to the tree under a specific parent Node

        Parameters
        -----------
        node : :class:`Node`
            Node to be added
        parent : :class:`Node`
            parent Node of the newly added Node
        """
        node.parent = parent
        if parent is not None:
            parent.add_child(node)

    def remove_node(self, node):

        """
        Remove a Node from the tree

        Parameters
        -----------
        Node : :class:`Node`
            Node to be removed
        """
        node.parent.remove_child(node)
        self._deep_remove(node)

    def _deep_remove(self, node):
        children = node.children
        node.make_empty()
        for child in children:
            self._deep_remove(child)

    def get_nodes(self):

        """
        Obtain a list of all nodes in the tree

        Returns
        -------
        all_nodes : list of :class:`Node`
        """
        n = []
        self._gather_nodes(self.root, n)
        return n

    def get_segments_fast(self):

        """
        Obtain a list of all segments in the tree
        fast version (doesn't contain overlapping segments

        Returns
        -------
        all_segments : list of list of :class:`Node` for each segment
        """
        leaves = []
        branches = []
        for n in self.get_nodes():
            if self.is_leaf(n):
                leaves.append(n)
            elif self.is_branch(n):
                branches.append(n)

        all_segments = []

        for l in leaves:
            segment = []
            n = l
            segment.append(n)
            while True:
                n = n.get_parent()
                if self.is_branch(n):
                    segment.append(n)
                    all_segments.append(segment)
                    break
                elif self.is_root(n):
                    segment.append(n)
                    all_segments.append(segment)
                    break
                else:
                    segment.append(n)
        for b in branches:
            segment = []
            n = b
            segment.append(n)
            while True:
                n = n.get_parent()
                if self.is_branch(n):
                    segment.append(n)
                    all_segments.append(segment)
                    break
                elif self.is_root(n):
                    segment.append(n)
                    all_segments.append(segment)
                    break
                else:
                    segment.append(n)
        return all_segments

    def get_segments(self):

        """
        Obtain a list of all segments in the tree
        Contains overlapping segments so joints are modelled correctly

        Returns
        -------
        all_segments : list of list of :class:`Node` for each segment
        """
        leaves = []

        for n in self.get_nodes():
            if self.is_leaf(n):
                leaves.append(n)

        all_segments = []

        for l in leaves:
            segment = []
            n = l
            segment.append(n)
            while True:
                n = n.get_parent()
                if self.is_root(n):
                    segment.append(n)
                    all_segments.append(segment)
                    break
                else:
                    segment.append(n)
        return all_segments

    def get_sub_tree(self, fake_root):

        """
        Obtain the subtree starting from the given Node

        Parameters
        -----------
        fake_root : :class:`Node`
            Node which becomes the new root of the subtree

        Returns
        -------
        sub_tree :  NeuronMorphology
            New tree with the Node from the first argument as root Node
        """
        ret = Tree()
        cp = fake_root.__copy__()
        cp.parent = None
        ret.root = cp
        return ret

    def _gather_nodes(self, node, node_list):

        if node is not None:
            node_list.append(node)
            for child in node.children:
                self._gather_nodes(child, node_list)

    def get_node_with_index(self, index):

        """
        Get a Node with a specific name. The name is always an integer

        Parameters
        ----------
        index : int
            Name of the Node to be found

        Returns
        -------
        Node : :class:`Node`
            Node with the specific index
        """
        return self._find_node(self.root, index)

    def get_node_in_subtree(self, index, fake_root):

        """
        Get a Node with a specific name in a the subtree rooted at fake_root.
        The name is always an integer

        Parameters
        ----------
        index : int
            Name of the Node to be found
        fake_root: :class:`Node`
            Root Node of the subtree in which the Node with a given index
            is searched for

        Returns
        -------
        Node : :class:`Node`
            Node with the specific index
        """
        return self._find_node(fake_root, index)

    def _find_node(self, node, index):

        """
        Sweet breadth-first/stack iteration to replace the recursive call.
        Traverses the tree until it finds the Node you are looking for.

        Parameters
        -----------
        node : :class:`Node`
            Node to be found
         index : int
            Name of the Node to be found

        Returns
        -------
        node : :class:`Node`
            when found and None when not found
        """
        stack = []
        stack.append(node)
        while(len(stack) != 0):
            for child in stack:
                if child.index == index:
                    return child
                else:
                    stack.remove(child)
                    for cchild in child.children:
                        stack.append(cchild)
        return None  # Not found!

    def degree_of_node(self, node):

        """
        Get the degree of a given Node. The degree is defined as the number of
        leaf nodes in the subtree rooted at this Node.

        Parameters
        ----------
        node : :class:`Node`
            Node of which the degree is to be computed.

        Returns
        -------
        degree : int
        """
        sub_tree = self.get_sub_tree(node)
        st_nodes = sub_tree.get_nodes()
        leafs = 0
        for n in st_nodes:
            if sub_tree.is_leaf(n):
                leafs = leafs + 1
        return leafs

    def order_of_node(self, node):

        """
        Get the order of a given Node. The order or centrifugal order is
        defined as 0 for the root and increased with any bifurcation.
        Hence, a Node with 2 branch points on the shortest path between
        that Node and the root has order 2.

        Parameters
        ----------
        node : :class:`Node`
            Node of which the order is to be computed.

        Returns
        -------
        order : int
        """
        ptr = self.path_to_root(node)
        order = 0
        for n in ptr:
            if len(n.children) > 1:
                order = order+1
        # order is on [0,max_order] thus subtract 1 from this calculation
        return order - 1

    def path_to_root(self, node):

        """
        Find and return the path between a Node and the root.

        Parameters
        ----------
        Node : :class:`Node`
            Node at which the path starts

        Returns
        -------
        path : list of :class:`Node`
            list of :class:`Node` with the provided Node and the root as first
            and last entry, respectively.
        """
        n = []
        self._go_up_from(node, n)
        return n

    def _go_up_from(self, node, n):

        n.append(node)
        if node.parent is not None:
            self._go_up_from(node.parent, n)

    def path_between_nodes(self, from_node, to_node):

        """
        Find the path between two nodes. The from_node needs to be of higher \
        order than the to_node. In case there is no path between the nodes, \
        the path from the from_node to the soma is given.

        Parameters
        -----------
        from_node : :class:`Node`
        to_node : :class:`Node`
        """
        n = []
        self._go_up_from_until(from_node, to_node, n)
        return n

    def _go_up_from_until(self, from_node, to_node, n):

        n.append(from_node)
        if from_node == to_node:
            return
        if from_node.parent is not None:
            self._go_up_from_until(from_node.parent, to_node, n)

    def read_NMF_tree_from_file(self,input_file):
        """
        Non-specific for a "tree data structure"
        Read and load a morphology from an NTF file and parse it into
        an NeuronMorphology object.        
        """
        hf = h5py.File(input_file,"r")
        ids = list(hf.get("swc/index"))
        s_types = list(hf.get("swc/type"))
        xs = list(hf.get("swc/x"))
        ys = list(hf.get("swc/y"))
        zs = list(hf.get("swc/z"))
        rs = list(hf.get("swc/r"))
        parents = list(hf.get("swc/parent_index"))
        swc_set = hf['swc']        
        soma_attr = swc_set.attrs['soma_type']
        print("soma_attr:{}, len(xs)={}".format(soma_attr,len(xs)))

        all_nodes = dict()
        for i in range(len(xs)):
            x = xs[i]
            y = ys[i]
            z = zs[i]
            radius = rs[i]
            swc_type = s_types[i]
            index = ids[i]
            parent_index = parents[i]
            # create a node
            tP3D = P3D(np.array([x, y, z]), radius, swc_type)
            t_node = Node(index)
            t_node.content = {'p3d': tP3D}
            all_nodes[index] = (swc_type, t_node, parent_index)

        # create an internal tree
        if soma_attr=="1_point_soma":
            for index, (swc_type, node, parent_index) in all_nodes.items():
                if index == 1:
                    # print "Set soma -- 1-point soma"
                    self.root = node
                    """add 2 extra point because the internal representation
                    relies on the 3-point soma position.
                    Shift all subsequent indices by 2."""
                    sp = node.content['p3d']
                    """
                     1 1 xs ys zs rs -1
                     2 1 xs (ys-rs) zs rs 1
                     3 1 xs (ys+rs) zs rs 1
                    """
                    pos1 = P3D([sp.xyz[0], sp.xyz[1]-sp.radius,
                                sp.xyz[2]], sp.radius, 1)
                    pos2 = P3D([sp.xyz[0], sp.xyz[1]+sp.radius,
                                sp.xyz[2]], sp.radius, 1)
                    sub1 = Node(2)
                    sub1.content = {'p3d': pos1}
                    sub2 = Node(3)
                    sub2.content = {'p3d': pos2}
                    self.add_node_with_parent(sub1, self.root)
                    self.add_node_with_parent(sub2, self.root)
                else:
                    parent_node = all_nodes[parent_index][1]
                    if parent_node is None:
                        print("parent appears to be NONE")
                    if parent_node.index > 1:
                        parent_node.index = parent_node.index  # +2
                    if node.index > 1:
                        node.index = node.index  # +2
                    self.add_node_with_parent(node, parent_node)        
        # IF 3-point soma representation
        elif soma_attr=="3_point_soma":
            for index, (swc_type, node, parent_index) in all_nodes.items():
                if index == 1:
                    # print "Set soma -- 3 point soma"
                    self.root = node
                elif index in (2, 3):
                    # the 3-point soma representation
                    # (http://neuromorpho.org/neuroMorpho/SomaFormat.html)
                    self.add_node_with_parent(node, self.root)
                else:
                    parent_node = all_nodes[parent_index][1]
                    self.add_node_with_parent(node, parent_node)
        # IF multiple cylinder soma representation
        elif soma_attr=="multiple_cylinder_soma":
            self.root = all_nodes[1][1]

            # get all some info
            soma_cylinders = []
            connected_to_root = []
            for index, (swc_type, node, parent_index) in all_nodes.items():
                if swc_type == 1 and not index == 1:
                    soma_cylinders.append((node, parent_index))
                    if index > 1:
                        connected_to_root.append(index)

            # make soma
            s_node_1, s_node_2 = self._make_soma_from_cylinders(soma_cylinders,
                                                                all_nodes)

            # add soma
            self.root = all_nodes[1][1]
            self.root.content["p3d"].radius = s_node_1.content["p3d"].radius
            self.add_node_with_parent(s_node_1, self.root)
            self.add_node_with_parent(s_node_2, self.root)

            # add the other points
            for index, (swc_type, node, parent_index) in all_nodes.items():
                if swc_type == 1:
                    pass
                else:
                    parent_node = all_nodes[parent_index][1]
                    if parent_node.index in connected_to_root:
                        self.add_node_with_parent(node, self.root)
                    else:
                        self.add_node_with_parent(node, parent_node)

        return self                    
                            
    def read_SWC_tree_from_file(self, input_file, types=range(1, 10)):
        """
        Non-specific for a "tree data structure"
        Read and load a morphology from an SWC file and parse it into
        an NeuronMorphology object.

        On the NeuroMorpho.org website, 5 types of somadescriptions are
        considered (http://neuromorpho.org/neuroMorpho/SomaFormat.html).
        The "3-point soma" is the standard and most files are converted
        to this format during a curation step. btmorph follows this default
        specificationand the *internal structure of btmorph implements
        the 3-point soma*.

        However, two other options to describe the soma
        are still allowed and available, namely:
        - one-point soma
        - multiple cylinder soma

        """
        # check soma-representation: 3-point soma or a non-standard
        # representation
        self.soma_type = self._determine_soma_type(input_file)
        print "NeuronMorphology::read_SWC_tree_from_file found soma_type=%i" \
            % self.soma_type

        f = open(input_file, 'r')
        all_nodes = dict()
        for line in f:
            if not line.startswith('#'):
                split = line.split()
                index = int(split[0].rstrip())
                swc_type = int(split[1].rstrip())
                x = float(split[2].rstrip())
                y = float(split[3].rstrip())
                z = float(split[4].rstrip())
                radius = float(split[5].rstrip())
                parent_index = int(split[6].rstrip())

                if swc_type in types:
                    tP3D = P3D(np.array([x, y, z]), radius, swc_type)
                    t_node = Node(index)
                    t_node.content = {'p3d': tP3D}
                    all_nodes[index] = (swc_type, t_node, parent_index)
                else:
                    print type,index

        # IF 1-point soma representation
        if self.soma_type == 0:
            for index, (swc_type, node, parent_index) in all_nodes.items():
                if index == 1:
                    # print "Set soma -- 1-point soma"
                    self.root = node
                    """add 2 extra point because the internal representation
                    relies on the 3-point soma position.
                    Shift all subsequent indices by 2."""
                    sp = node.content['p3d']
                    """
                     1 1 xs ys zs rs -1
                     2 1 xs (ys-rs) zs rs 1
                     3 1 xs (ys+rs) zs rs 1
                    """
                    pos1 = P3D([sp.xyz[0], sp.xyz[1]-sp.radius,
                                sp.xyz[2]], sp.radius, 1)
                    pos2 = P3D([sp.xyz[0], sp.xyz[1]+sp.radius,
                                sp.xyz[2]], sp.radius, 1)
                    sub1 = Node(2)
                    sub1.content = {'p3d': pos1}
                    sub2 = Node(3)
                    sub2.content = {'p3d': pos2}
                    self.add_node_with_parent(sub1, self.root)
                    self.add_node_with_parent(sub2, self.root)
                else:
                    parent_node = all_nodes[parent_index][1]
                    if parent_node is None:
                        print("parent appears to be NONE")
                    if parent_node.index > 1:
                        parent_node.index = parent_node.index  # +2
                    if node.index > 1:
                        node.index = node.index  # +2
                    self.add_node_with_parent(node, parent_node)

        # IF 3-point soma representation
        elif self.soma_type == 1:
            for index, (swc_type, node, parent_index) in all_nodes.items():
                if index == 1:
                    # print "Set soma -- 3 point soma"
                    self.root = node
                elif index in (2, 3):
                    # the 3-point soma representation
                    # (http://neuromorpho.org/neuroMorpho/SomaFormat.html)
                    self.add_node_with_parent(node, self.root)
                else:
                    parent_node = all_nodes[parent_index][1]
                    self.add_node_with_parent(node, parent_node)
        # IF multiple cylinder soma representation
        elif self.soma_type == 2:
            self.root = all_nodes[1][1]

            # get all some info
            soma_cylinders = []
            connected_to_root = []
            for index, (swc_type, node, parent_index) in all_nodes.items():
                if swc_type == 1 and not index == 1:
                    soma_cylinders.append((node, parent_index))
                    if index > 1:
                        connected_to_root.append(index)

            # make soma
            s_node_1, s_node_2 = self._make_soma_from_cylinders(soma_cylinders,
                                                                all_nodes)

            # add soma
            self.root = all_nodes[1][1]
            self.root.content["p3d"].radius = s_node_1.content["p3d"].radius
            self.add_node_with_parent(s_node_1, self.root)
            self.add_node_with_parent(s_node_2, self.root)

            # add the other points
            for index, (swc_type, node, parent_index) in all_nodes.items():
                if swc_type == 1:
                    pass
                else:
                    parent_node = all_nodes[parent_index][1]
                    if parent_node.index in connected_to_root:
                        self.add_node_with_parent(node, self.root)
                    else:
                        self.add_node_with_parent(node, parent_node)

        return self

    def write_SWC_tree_to_file(self, input_file):
        """
        Non-specific for a tree.

        Used to write an SWC file from a morphology stored in this
        :class:`NeuronMorphology`. Output uses the 3-point soma standard.

         Parameters
        -----------
        input_file : :class:`str`
            File name to write SWC to

        """
        writer = open(input_file, 'w')
        nodes = self.get_nodes()
        nodes.sort()

        # 3 point soma representation (See Neuromoprho.org FAQ)
        s1p = nodes[0].content["p3d"]
        s1_xyz = s1p.xyz
        s2p = nodes[1].content["p3d"]
        s2_xyz = s2p.xyz
        s3p = nodes[2].content["p3d"]
        s3_xyz = s3p.xyz
        soma_str = "1 1 " + str(s1_xyz[0]) + " " + str(s1_xyz[1]) + \
                   " " + str(s1_xyz[2]) + " " + str(s1p.radius) + " -1\n" + \
                   "2 1 " + str(s2_xyz[0]) + " " + str(s2_xyz[1]) + \
                   " " + str(s2_xyz[2]) + " " + str(s2p.radius) + " 1\n" + \
                   "3 1 " + str(s3_xyz[0]) + " " + str(s3_xyz[1]) + \
                   " " + str(s3_xyz[2]) + " " + str(s3p.radius) + " 1\n"
        writer.write(soma_str)
        writer.flush()

        # add the soma compartment, then enter the loop
        for node in nodes[3:]:
            p3d = node.content['p3d']  # update 2013-03-08
            xyz = p3d.xyz
            radius = p3d.radius
            tt = p3d.segtype
            p3d_string = (str(node.index)+' '+str(tt) + ' ' + str(xyz[0]) +
                          ' ' + str(xyz[1]) + ' ' + str(xyz[2]) +
                          ' ' + str(radius) + ' ' + str(node.parent.index))
            # print 'p3d_string: ', p3d_string
            writer.write(p3d_string + '\n')
            writer.flush()
        writer.close()
        # print 'STree::writeSWCTreeToFile -> finished. Tree in >',fileN,'<'

    def _make_soma_from_cylinders(self, soma_cylinders, all_nodes):

        """Now construct 3-point soma
        step 1: calculate surface of all cylinders
        step 2: make 3-point representation with the same surface"""

        total_surf = 0
        for (node, parent_index) in soma_cylinders:
            n = node.content["p3d"]
            p = all_nodes[parent_index][1].content["p3d"]
            H = np.sqrt(np.sum((n.xyz-p.xyz)**2))
            surf = 2*np.pi*p.radius*H
            # print "(node %i) surf as cylinder:  %f (R=%f, H=%f), P=%s" %
            # (node.index,surf,n.radius,H,p)
            total_surf = total_surf+surf
        print "found 'multiple cylinder soma' w/ total soma surface=", \
            total_surf

        # define appropriate radius
        radius = np.sqrt(total_surf / (4 * np.pi))
        # print "found radius: ", radius

        s_node_1 = Node(2)
        r = self.root.content["p3d"]
        rp = r.xyz
        s_p_1 = P3D(np.array([rp[0], rp[1]-radius, rp[2]]), radius, 1)
        s_node_1.content = {'p3d': s_p_1}
        s_node_2 = Node(3)
        s_p_2 = P3D(np.array([rp[0], rp[1]+radius, rp[2]]), radius, 1)
        s_node_2.content = {'p3d': s_p_2}

        return s_node_1, s_node_2


    def _determine_soma_type(self,file_n):
        """
        Costly method to determine the soma type used in the SWC file.
        This method searches the whole file for soma entries.  

        Parameters
        ----------
        file_n : string
            Name of the file containing the SWC description

        Returns
        -------
        soma_type : int
            Integer indicating one of the su[pported SWC soma formats.
            0: 1-point soma
            1: Default three-point soma
            2: multiple cylinder description,
            3: otherwise [not suported in btmorph]
        """
        file = open(file_n,"r")
        somas = 0
        for line in file:
            if not line.startswith('#') :
                split = line.split()
                index = int(split[0].rstrip())
                s_type = int(split[1].rstrip())
                if s_type == 1 :
                    somas = somas +1
        file.close()
        if somas == 3:
            return 1
        elif somas == 1:
            return 0
        elif somas > 3:
            return 2
        else:
            return 3    

    def _pca(self, A):
        """ performs principal components analysis
         (PCA) on the n-by-p data matrix A
         Rows of A correspond to observations, columns to variables.

         Returns :
          coeff :
        is a p-by-p matrix, each column containing coefficients
        for one principal component.
          score :
        the principal component scores; that is, the representation
        of A in the principal component space. Rows of SCORE
        correspond to observations, columns to components.
          latent :
        a vector containing the eigenvalues
        of the covariance matrix of A.
        source: http://glowingpython.blogspot.jp/2011/07/
        principal-component-analysis-with-numpy.html
        """
        # computing eigenvalues and eigenvectors of covariance matrix
        M = (A-mean(A.T, axis=1)).T  # subtract the mean (along columns)
        [latent, coeff] = linalg.eig(cov(M))  # attention:not always sorted
        score = dot(coeff.T, M)  # projection of the data in the new space
        return coeff, score, latent

    def pca_project_tree(self, threeD=True):
        """
        Returns a tree which is a projection of the original tree on the plane
         of most variance

        Parameters
        ----------
        tree : :class:`btmorph.btstructs2.STree2`
        A tree

        Returns
        --------
        tree : :class:`btmorph.btstructs2.STree2`
            New flattened tree
        """
        nodes = self.get_nodes()
        N = len(nodes)
        coords = map(lambda n: n.content['p3d'].xyz, nodes)
        points = transpose(coords)
        _, score, _ = self._pca(points.T)
        if threeD is False:
            score[2, :] = [0]*N
        newp = transpose(score)
        # Move soma to origin
        translate = score[:, 0]
        for i in range(0, N):
            nodes[i].content['p3d'].xyz = newp[i] - translate

        import time
        fmt = '%Y_%b_%d_%H_%M_%S'
        now = time.strftime(fmt)
        self.write_SWC_tree_to_file('tmpTree_3d_' + now + '.swc')
        self = self.read_SWC_tree_from_file('tmpTree_3d_' + now + '.swc')
        import os
        os.remove('tmpTree_3d_' + now + '.swc')
        return self

    def __iter__(self):

        nodes = []
        self._gather_nodes(self.root, nodes)
        for n in nodes:
            yield n

    def __getitem__(self, index):

        return self._find_node(self.root, index)

    def __str__(self):

        return "Tree ("+str(len(self.get_nodes()))+" nodes)"


class Node(object):

    """
    Simple Node for use with a simple Neuron (NeuronMorphology)

    By design, the "content" should be a dictionary. (2013-03-08)
    """

    def __init__(self, index):
        """
        Constructor.

        Parameters
        -----------
        index : int
           Index, unique name of the :class:`Node`
        """
        self.parent = None
        self.index = index
        self.children = []
        self.content = {}

    def get_parent(self):

        """
        Return the parent Node of this one.

        Returns
        -------
        parent : :class:`Node`
           In case of the root, None is returned.Otherwise a :class:`Node` is
            returned
        """
        return self.__parent

    def set_parent(self, parent):

        """
        Set the parent Node of a given other Node

        Parameters
        ----------
        Node : :class:`Node`
        """
        self.__parent = parent

    parent = property(get_parent, set_parent)

    def get_index(self):

        """
        Return the index of this Node

        Returns
        -------
        index : int
        """
        return self.__index

    def set_index(self, index):

        """
        Set the unique name of a Node

        Parameters
        ----------

        index : int
        """
        self.__index = index

    index = property(get_index, set_index)

    def get_children(self):

        """
        Return the children nodes of this one (if any)

        Returns
        -------
        children : list :class:`Node`
           In case of a leaf an empty list is returned
        """
        return self.__children

    def set_children(self, children):

        """
        Set the children nodes of this one

        Parameters
        ----------

        children: list :class:`Node`
        """
        self.__children = children

    children = property(get_children, set_children)

    def get_content(self):

        """
        Return the content dict of a :class:`Node`

        Returns
        -------
        parent : :class:`Node`
           In case of the root, None is returned.Otherwise a :class:`Node` is
           returned
        """
        return self.__content

    def set_content(self, content):

        """
        Set the content of a Node. The content must be a dict

        Parameters
        ----------
        content : dict
            dict with content. For use in btmorph at least a 'p3d' entry should
             be present
        """
        if isinstance(content, dict):
            self.__content = content
        else:
            raise Exception("Node.set_content must receive a dict")

    content = property(get_content, set_content)

    def add_child(self, child_node):

        """
        add a child to the children list of a given Node

        Parameters
        -----------
        Node :  :class:`Node`
        """
        self.children.append(child_node)

    def make_empty(self):
        """
        Clear the Node. Unclear why I ever implemented this. Probably to cover
         up some failed garbage collection
        """
        self.parent = None
        self.content = {}
        self.children = []

    def remove_child(self, child):
        """
        Remove a child Node from the list of children of a specific Node

        Parameters
        -----------
        Node :  :class:`Node`
            If the child doesn't exist, you get into problems.
        """
        self.children.remove(child)

    def __str__(self):

        return 'Node (ID: '+str(self.index)+')'

    def __lt__(self, other):

        if self.index < other.index:
            return True

    def __le__(self, other):

        if self.index <= other.index:
            return True

    def __gt__(self, other):

        if self.index > other.index:
            return True

    def __ge__(self, other):

        if self.index >= other.index:
            return True

    def __copy__(self):  # customization of copy.copy

        ret = Node(self.index)
        for child in self.children:
            ret.add_child(child)
        ret.content = self.content
        ret.parent = self.parent
        return ret


class P3D(object):

    """
    Basic container to represent and store 3D information
    """

    def __init__(self, xyz, radius, segtype=7):
        """ Constructor.

        Parameters
        -----------

        xyz : numpy.array
            3D location
        radius : float
        segtype : int
            Type asscoiated with the segment according to SWC standards
        """
        self.xyz = xyz
        self.radius = radius
        self.segtype = segtype

    def __str__(self):

        return "P3D [%.2f %.2f %.2f], R=%.2f" % (self.xyz[0], self.xyz[1],
                                                 self.xyz[2], self.radius)
