#!/usr/bin/env python  # shebang for Unix-based systems
#!pythonw        # shebang for Windows systems
########################
# F.garcia
# creation: 15.02.2025
########################

class TreeNode:
    def __init__(self, name):
        self.name = name
        self.children = []
        self.i_am=''
        self.expand=True
        self.level=None
        self.parent = None 
        self.id=None
        self.info=None
        self.size=None
        self.default=None
        self.selected=None
        self.selectable=None
        self.selected_children=None

    def to_dict(self)->dict:
        """Convert node to dictionary. Only attributes not starting with '__'

        Returns:
            dict: Node as dictionary
        """
        me_dict={}
        for key in dir(self):
            if not key.startswith('__') and not key in ["to_dict"]:
                att=getattr(self,key)
                if  key not in ['parent','children']:
                    me_dict.update({key:att}) 
                else:
                    if key == 'parent':
                        if isinstance(att,TreeNode):
                            me_dict.update({key:getattr(att,'id')})
                        else:
                            me_dict.update({key:None})
                    elif key == 'children':
                        att_list=[]
                        for child in att:
                            if isinstance(child,TreeNode):
                                att_list.append(getattr(child,'id')) 
                            else:
                                att_list.append(None)
                        me_dict.update({key:att_list})
        return me_dict
    
    def get_bloodline(self,bloodline:list=None):
        """Gets a list with parents ids

        Args:
            bloodline (list, optional): previous blodline list. Defaults to None.

        Returns:
            list: blodline list with [id, parent.id, parent.parent.id, ...,main node id]
        """
        if not isinstance(bloodline,list):
            bloodline=[]
        bloodline.append(self.id)
        if isinstance(self.parent,TreeNode):
            
            bloodline=self.parent.get_bloodline(bloodline)
        return bloodline

class TreeViewer:
    def __init__(self, file_struct,indexes_dict:dict=None,str_style=0):
        self.file_struct = file_struct
        self.all_nodes=[]
        self.filtered_nodes=[]
        self.count=0
        self.filename_index=0
        self.size_index=None
        if indexes_dict:
            if 'name' in indexes_dict.keys():
                self.filename_index=indexes_dict['name']
            if 'size' in indexes_dict.keys():
                self.size_index=indexes_dict['size']    
        self.main_node=None
        self.str_style=str_style
        self._define_struct()
    
    @staticmethod
    def _is_dir(fs)->bool:
        """Check if is a File structure directory

        Args:
            fs (any): Checks for directory of filestructure

        Returns:
            bool: True if a directory.
        """
        if isinstance(fs,dict):
            for a_key,value in fs.items():
                if not isinstance(value,list):
                    return False
            return True
        return False
    
    @staticmethod
    def _is_file(fs)->bool:
        """Check if is a File structure file

        Args:
            fs (any): Checks for directory of filestructure

        Returns:
            bool: True if a directory.
        """
        if isinstance(fs,tuple):
            for value in fs:
                if isinstance(value,(dict,list)) :
                    return False
            return True
        if not isinstance(fs,(dict,list)) :
            return True
        return False
    
    def get_file_name_in_tuple(self,file_tup:tuple)->str:
        """Returns string when Filestructure has tuple with information
            uses filename_index to get position of filename in tuple
        Args:
            file_tup (tuple): tuple with file information

        Returns:
            str: file name in tuple
        """
        if len(file_tup)==0:
            self.count=self.count+1
            return 'file_'+str(self.count)
        return str(file_tup[self.filename_index])
    
    def get_file_size_in_tuple(self,file_tup:tuple)->str:
        """Returns string when Filestructure has tuple with information
            uses size_index to get position of filename in tuple
        Args:
            file_tup (tuple): tuple with file information

        Returns:
            int: file size in tuple
        """

        if len(file_tup)==0 or not self.size_index:
            return None
        return file_tup[self.size_index]

    def exist_subdirectories(self,node:TreeNode)->bool:
        """Searches for subdirectories in a node

        Args:
            node (TreeNode): Treenode

        Returns:
            bool: True if dir and has subdirectories.
        """
        if node.i_am=='dir':
            for child in node.children:
                if child.i_am=='dir':
                    return True
        return False
    
    def trace_path(self,node:TreeNode,level_except:list=None,reverse:bool=True)->list[str]:
        """generate trace path list from blodline

        Args:
            node (TreeNode): node to trace back
            level_except (list, optional): exception levels. Defaults to None.
            reverse (bool, optional): False node_name ,node_parent_name ... main_node_name. 
                                     True reversed order. Defaults to True.

        Returns:
            list[str]: list of names of nodes in bloodline
        """
        bl=node.get_bloodline()
        trace=[]
        if not level_except:
            level_except=[]
        for node_id in bl:
            bl_node_list= self.get_nodes_by_attribute('id',node_id)
            if len(bl_node_list)>0:
                bl_node=bl_node_list[0]
                if bl_node.level not in level_except:
                    trace.append(bl_node.name)
        if reverse:
            r_tr=[]
            for tr in trace:
                r_tr=[tr]+r_tr
            trace=r_tr
        return trace

    def _get_nodes(self,fs)->TreeNode:
        """Recursive Node formation from file structure

        Args:=
            fs (dict): File structure

        Returns:
            TreeNode: Main node 
        """
        if self._is_dir(fs):
            for a_key,file_list in fs.items():
                node = TreeNode(a_key)
                node.i_am='dir'
                self.all_nodes.append(node)
                node.children=self._get_nodes(file_list)
                return node
        
        elif isinstance(fs,list):
            node_list=[]
            for a_file in fs:
                if self._is_dir(a_file):
                    node = self._get_nodes(a_file)
                    node_list.append(node)
                elif self._is_file(a_file):
                    if isinstance(a_file,tuple):
                        a_f=self.get_file_name_in_tuple(a_file)
                        a_size=self.get_file_size_in_tuple(a_file)
                    else:
                        a_f=str(a_file)
                        a_size = None
                    node = TreeNode(a_f)
                    node.i_am='file'
                    node.info=a_file # add all info to the node
                    if isinstance(a_size,(int,float)):
                        node.size=a_size
                    if isinstance(a_size,(tuple,list)):
                        if len(a_size)>self.size_index:
                            node.size=a_size[self.size_index]
                    node_list.append(node)
                    self.all_nodes.append(node)
            return node_list
        raise ValueError(f'{type(fs)} is not a valid type for file structure!')
        return None

    def _define_struct(self):
        """Set information for file struct
        """
        self.main_node=self._get_nodes(self.file_struct)
        # print('[green]Node structure built')
        self._set_treenode_levels(self.main_node)
        # print('[green]Node structure Levels')
        self._set_treenode_sizes(self.main_node)
        # print('[green]Node structure Sizing')
        if len(self.all_nodes)>100:
            self.expand_all_treenodes(False)
            #print(f'[yellow]Encountered {len(self.all_nodes)} nodes')
    
    def get_nodes_by_attribute(self,attribute:str,value)->list[TreeNode]:
        """Returns a list of nodes which have node.attribute=value

        Args:
            attribute (str): node attibute
            value (any): value to find

        Returns:
            list: list of TreeNode
        """
        the_node=[]
        for node in self.all_nodes:
            if hasattr(node,attribute):
                if getattr(node,attribute)==value:
                    the_node.append(node)
        return the_node
    
    def call_style(self,node:TreeNode,level):
        """Function to be overwritten"""
        return self._call_style(node,level)

    def _call_style(self, node:TreeNode,level):
        """Inner style"""
        if self.str_style==0:
            if level==0:
                prefix = '  ' * (level - 1) 
            else:    
                prefix = '  ' * (level - 1) + '└── '
        elif self.str_style==1:
            if level==0:
                prefix = '  ' * (level - 1) 
            else:    
                prefix = '  ' * (level - 1) + '└── '
            prefix = str(node.level) +' > '+ prefix
        elif self.str_style==2:
            if level==0:
                prefix = '  ' * (level - 1) 
            else:    
                prefix = '  ' * (level - 1) + f'{node.i_am}({node.level}): '
        else:
            prefix=''
        return prefix

    def expand_all_treenodes(self,expand=True):
        """Expands or contract all nodes.

        Args:
            expand (bool, optional): Expand if True otherwise contract. Defaults to True.
        """
        for node in self.all_nodes:
            if node.i_am=='dir':
                node.expand=expand
    
    def clear_default(self):
        """Expands or contract all nodes.

        Args:
            expand (bool, optional): Expand if True otherwise contract. Defaults to True.
        """
        for node in self.all_nodes:
            node.default=False
    
    def clear_select(self):
        """Expands or contract all nodes.

        Args:
            expand (bool, optional): Expand if True otherwise contract. Defaults to True.
        """
        for node in self.all_nodes:
            node.select=False
    
    def clear_selected_children(self,node:TreeNode):
        """Expands or contract all nodes.

        Args:
            expand (bool, optional): Expand if True otherwise contract. Defaults to True.
        """
        for child in node.children:   
            node.selected_children=False
            self.clear_selected_children(child)
    
    def set_selected_children(self,node:TreeNode)->bool:
        """Searches the tree recursively and returns True if finds a selected child

        Args:
            node (TreeNode): node

        Returns:
            bool: True if at least one child is selected
        """
        if len(node.children)==0:
            return False
        else:
            for child in node.children:
                if child.selected:
                    node.selected_children=True
                    # return True
                child.selected_children=False
                child.selected_children=self.set_selected_children(child)
                if child.selected_children:
                    node.selected_children=True
            if node.selected_children:
                return True
        node.selected_children=False
        return False

    def treenode_to_string(self, node:TreeNode, str_out='', level=0, a_filter=None)->str:
        """Generates a string with a Tree structure.

        Args:
            node (TreeNode): TreeNode object to print
            str_out (str, optional): String prefix. Defaults to ''.
            level (int, optional): level depth. Defaults to 0.
            a_filter (_type_, optional): Filter only folders with 'dir','expand' checks for expand flag in node. Defaults to None.

        Returns:
            str: File tree string 
        """
        tree_list=self.treenode_to_string_list(node, str_out, level, a_filter)
        str_out='\n'.join(tree_list)
        return str_out
    
    def treenode_to_string_list(self, node:TreeNode, str_out='', level=0, a_filter=None)->list:
        """Generates a list of strings with a Tree structure.

        Args:
            node (TreeNode): TreeNode object to print
            str_out (str, optional): String prefix. Defaults to ''.
            level (int, optional): level depth. Defaults to 0.
            a_filter (_type_, optional): Filter only folders with 'dir','expand' checks for expand flag in node. Defaults to None.

        Returns:
            list: File tree list of string 
        """
        tree_list=[]
        if not str_out:
            str_out=''
        if node is None:
            return tree_list
        if not node.name:
            return tree_list
        if level==0 and not node.parent: 
            self.filtered_nodes=[]
        # set the style
        prefix = self.call_style(node,level)  
        if prefix is None:
            prefix = ""
        if a_filter not in ['dir','expand','expand_dir']:
            str_out=str_out+prefix + str(node.name)
            tree_list.append(str_out)
            self.filtered_nodes.append(node)
            for child in node.children:
                str_out=''
                tree_list=tree_list+self.treenode_to_string_list(child, str_out, level + 1,a_filter)
                
        elif a_filter == 'dir':
            if node.i_am=='dir':    
                str_out=str_out+prefix + str(node.name)
                tree_list.append(str_out)
                self.filtered_nodes.append(node)
                for child in node.children:
                    str_out=''
                    tree_list=tree_list+self.treenode_to_string_list(child, str_out, level + 1,a_filter)
        
        elif a_filter == 'expand_dir':
            if node.i_am=='dir' and node.expand:   
                str_out=str_out+prefix + str(node.name)
                tree_list.append(str_out)
                self.filtered_nodes.append(node)
                for child in node.children:
                    str_out=''
                    if child.i_am=='dir':
                        tree_list=tree_list+self.treenode_to_string_list(child, str_out, level + 1,a_filter)
            elif node.i_am=='dir' and not node.expand:    
                str_out=str_out+prefix + str(node.name)
                tree_list.append(str_out)
                self.filtered_nodes.append(node)

        elif a_filter == 'expand':
            if node.i_am=='dir' and node.expand:    
                str_out=str_out+prefix + str(node.name)
                tree_list.append(str_out)
                self.filtered_nodes.append(node)
                for child in node.children:
                    str_out=''
                    tree_list=tree_list+self.treenode_to_string_list(child, str_out, level + 1,a_filter)
            elif node.i_am=='dir' and not node.expand:    
                str_out=str_out+prefix + str(node.name)
                tree_list.append(str_out)
                self.filtered_nodes.append(node)
            elif node.i_am=='file':
                str_out=str_out+prefix + str(node.name)
                tree_list.append(str_out)
                self.filtered_nodes.append(node)
                for child in node.children:
                    str_out=''
                    tree_list=tree_list+self.treenode_to_string_list(child, str_out, level + 1,a_filter)
                    
        return tree_list
    
    def _set_treenode_levels(self, node:TreeNode, level=0):
        """Sets the level and parent in each node

        Args:
            node (TreeNode): main node
            level (int, optional): initial level value. Defaults to 0.
        """
        if node:
            node.level=level
            if not node.id:
                node.id=self.count
                self.count=self.count+1
            for child in node.children:
                child.parent=node
                self._set_treenode_levels(child, level + 1)
    
    def _set_treenode_sizes(self, node:TreeNode, level=0):
        """Sets the level and parent in each node

        Args:
            node (TreeNode): main node
            level (int, optional): initial level value. Defaults to 0.
        """
        if node and self.size_index:
            if node.i_am=='dir':
                size=0    
                for child in node.children:
                    size=size+self._set_treenode_sizes(child, level + 1)
                node.size=size #sets size of directory as sum of directories and files inside
                return size
            if node.i_am=='file':
                if node.size:
                    if isinstance(node.size,(int,float)):
                        return node.size 
                    if isinstance(node.size,(tuple,list)):
                        if len(node.size)>self.size_index:
                            return node.size[self.size_index]
        return 0
    
    def set_selected_by_name(self,name_list,parent_list,level_except=None):
        """Sets selected items with the same name in name list 
        Args:
            name_list (list[str]): name of selected file
            parent_list (list[str]): name of parent of selected file
        """
        expand_id_list=[]
        for name,parent_name in zip(name_list,parent_list):
            node_list=self.get_nodes_by_attribute("name",name)
            if len(node_list) ==1:
                node=node_list[0]
                node.selected = True
                expand_id_list += node.get_bloodline()
                
            elif len(node_list) >1:
                for node in node_list:
                    path_list=self.trace_path(node,level_except,True)
                    all_in_path=True
                    for path in path_list[:-1]: # exclude filename
                        if path not in parent_name:
                            all_in_path=False
                            break
                    if all_in_path:
                        node.selected = True
                        expand_id_list += node.get_bloodline()
        self.set_selected_children(self.main_node)
        # expand preselected
        if len(self.all_nodes)<1000:
            for an_id in set(expand_id_list):
                node_list=self.get_nodes_by_attribute("id",an_id)
                if len(node_list) ==1:
                    node=node_list[0]
                    node.expand=True
            
# Example usage
if __name__ == "__main__":
    import os
    from class_file_manipulate import FileManipulate
    F_M=FileManipulate()
    def get_file_info(src_item):
        return (F_M.extract_filename(src_item),F_M.get_file_size(src_item))
        return ('f',F_M.get_file_size(src_item))
    # fs=F_M.get_file_structure_from_active_path('D:\\temp','test',{},full_path=False,fcn_call=get_file_info)
    fs=F_M.load_dict_to_json(F_M.get_app_path()+os.sep+'db_files'+os.sep+'__temp__fs.json')
    T_V=TreeViewer(fs,indexes_dict={'name':0,'size':1})
    print(T_V.count)
    print(T_V._is_dir(fs))
    print(T_V.main_node.to_dict())
    print("Amount of nodes: ",len(T_V.all_nodes))
    T_V.call_style=T_V._call_style #need to set an style before calling
    tree=T_V.treenode_to_string(T_V.main_node,a_filter='dir')
    print(tree)
    # print(T_V.main_node.children[0].children[0].get_bloodline())
    # print('*'*50)
    # T_V.str_style=2
    # def my_style(node:TreeNode,level):
    #     if level==0:
    #         prefix = '8>' * (level - 1) 
    #     else:    
    #         prefix = '8'+'==' * (level - 1) + '==> '
    #     prefix=str(node.id)+":"+prefix
    #     return prefix
    
    # T_V.call_style=my_style
    # tree=T_V.treenode_to_string(T_V.main_node,a_filter=None)
    # print(tree)

    # T_V.str_style=1
    # T_V.call_style=T_V._call_style #need to set an style before calling
    # tree=T_V.treenode_to_string(T_V.main_node,a_filter='dir')
    # print(tree)