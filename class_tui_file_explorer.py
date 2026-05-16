from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Tree, DataTable, Label
from textual.containers import Horizontal
from textual.message import Message
from textual import events
import os
from rich.console import Group
from rich.text import Text

from class_autocomplete_input import AutocompletePathFile
from class_file_manipulate import FileManipulate
from class_tree_viewer import TreeNode,TreeViewer
FM = FileManipulate()
AC = AutocompletePathFile('return string [cyan]ENTER[/cyan], Autofill path/file [cyan]TAB[/cyan], Cancel [cyan]ESC[/cyan]\nOr type complete path to file: ',
                                            FM.get_app_path(),absolute_path=False,verbose=True)

class PathEntered(Message):
    def __init__(self, path: str, options: list[str]):
        super().__init__()
        self.path = path
        self.options = options

class AutocompleteUpdated(Message):
    def __init__(self, options_text: str, options: list[str]):
        super().__init__()
        self.options_text = options_text
        self.options = options

class AutocompletePathInput(Input):
    """A Textual widget that uses AutocompletePathFile class."""
    BINDINGS = [
    ("tab", "autocomplete", "Autocomplete"),
    ]
    def __init__(self, autocomplete_engine: AutocompletePathFile, ini_path=None, **kwargs):
        super().__init__(**kwargs)
        self.engine = autocomplete_engine   # instance of AutocompletePathFile
        if ini_path:
            self.selected_path=ini_path
        else:
            self.selected_path=self.engine.base_path
        self.options_list = []    
        self.options_text = ""

    def get_initial_letter_text(self, list_auto):
        # Remove common prefix
        fill_add2, _ = self.engine.get_commontxt_optionlist(list_auto)
        stripped = [p.replace(fill_add2, "") for p in list_auto]
        # Remove common prefix again
        _, stripped = self.engine.get_commontxt_optionlist(stripped)
        # Get initial letters
        ini_letters = self.engine.get_initial_letters(stripped)
        return f"[{len(list_auto)}] Options with: {', '.join(ini_letters)}"        

    def action_autocomplete(self):
        current = self.value
        path_list = self.engine._get_possible_path_list(current)
        new_text = self.engine.autocomplete_path(current)
        new_text = new_text.replace(os.sep + os.sep, os.sep)
        # Update input
        self.value = new_text
        self.cursor_position = len(new_text)
        # Format options text
        if len(path_list) > 10:
            options_text = self.get_initial_letter_text(path_list)
        else:
            options_text = self.engine.options
        self.options_text = options_text
        self.options_list = path_list
        # Refresh UI
        self.refresh(recompose=True)
        # Notify app
        self.post_message(AutocompleteUpdated(options_text, path_list))

    async def on_key(self, event: events.Key):
        if event.key == "enter":
            self.post_message(PathEntered(self.value, self.options_list))
            return
        if event.key == "tab":
            self.action_autocomplete()
        return
        # Update list every time a key is pressed
        current = self.value
        path_list = self.engine._get_possible_path_list(current)
        self.options_list = path_list
        # Ask Textual to refresh the widget
        self.refresh(recompose=True)
        self.post_message(AutocompleteUpdated(self.options_list))
    
    def render(self):
        """Render input + optional options text."""
        base = super().render()
        # if self.options_text:
        #     return base + f"\n[dim]{self.options_text}[/dim]"
        if self.options_text:
            return Group(
                base,
                Text(self.options_text, style="dim")
            )
        return base
    
class PathSelected(Message):
    def __init__(self, path: str):
        self.path = path
        super().__init__()

class DirectorySelected(Message):
    def __init__(self, path: str):
        self.path = path
        super().__init__()

class ExplorerTree(Tree):

    # Override the Tree's own key bindings
    BINDINGS = [
        ("right", "expand_node", "Expand"),
        ("left", "collapse_node", "Collapse"),
        #("enter", "noop", "Return Selection"),
        #("space", "action_toggle_select", "Toggle"),
        #("tab", "action_toggle_select", "Toggle"),
    ]

    # Disable space toggling completely
    def action_toggle_node(self):
        pass

    # Right arrow expands
    def action_expand_node(self):
        node = self.cursor_node
        if node and not node.is_expanded:
            node.expand()

    # Left arrow collapses
    def action_collapse_node(self):
        node = self.cursor_node
        if node and node.is_expanded:
            node.collapse()
    
        

class FileExplorer(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #main {
        height: 1fr;
    }
    """
    
    def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.actual_path=FM.extract_path("")
            self.selection=[]
            self.file_structure = {"TreeStruct": []}
            # Build TreeViewer from your lazy file_structure
            self.viewer = TreeViewer(self.file_structure,{'name': 0, 'size': 1},str_style=0)

    def compose(self):
        # Create your autocomplete engine
        self.auto_engine = AutocompletePathFile(
            prompt="Enter path:",
            base_path=FM.get_app_path(),
            absolute_path=False,
            verbose=True,
            inquire=False
        )
        yield Header()
        yield AutocompletePathInput(self.auto_engine, id="path_input")
        # NEW: two labels under the input
        yield Label("", id="options_label")   # shows autocomplete options text
        yield Label("", id="path_label")      # shows actual explorer path
        with Horizontal():
            yield ExplorerTree("No path loaded", id="tree")
            table = DataTable(id="list")
            table.cursor_type = "row"
            table.zebra_stripes = True
            yield table
        yield Footer()

    def on_mount(self):
        self.load_tree()
        path=self.actual_path
        # Update path label
        path_label = self.query_one("#path_label", Label)
        path_label.update(path)
        # Update list panel
        self.load_directory_into_list(path)
        # Update Autocomplete text
        input_widget = self.query_one("#path_input", AutocompletePathInput)
        input_widget.value = path
        input_widget.cursor_position = len(path)
    
    async def on_autocomplete_updated(self, event: AutocompleteUpdated):
        options_label = self.query_one("#options_label", Label)
        path_label = self.query_one("#path_label", Label)
        # 1. Show autocomplete suggestions
        options_label.update(event.options_text)
        # 2. Determine the actual path prefix
        fill_add2, fill_add, comp_list = self.remove_common_paths_in_lists(event.options)
        file_exist, is_file = FM.validate_path_file(fill_add2)
        if file_exist and is_file:
            self.actual_path = FM.extract_path(fill_add2)
        elif not file_exist:
            self.actual_path = FM.extract_path(fill_add2)
        else:
            self.actual_path = fill_add2
        # 3. Update path label
        path_label.update(self.actual_path)
        # 4. Load directory contents (lazy)
        self.load_directory_into_list(self.actual_path)
        # 5. Load Tree
        self.load_tree()
    
    def load_tree(self):
        tree = self.query_one("#tree", Tree)
        # Update lazy file structure
        self.update_file_structure(self.actual_path)
        # Reset root
        tree.root.label = self.actual_path
        tree.root.data = self.actual_path
        tree.root.remove_children()
        # Load first level
        self.build_tree_level(tree.root, self.actual_path)
        tree.root.expand()
    
    async def on_tree_node_expanded(self, event: Tree.NodeExpanded):
        node = event.node
        path = node.data
        # Update lazy file structure
        self.update_file_structure(path)
        # Clear placeholder children
        node.remove_children()
        # Load real children
        self.build_tree_level(node, path)

    def remove_common_paths_in_lists(self,autocompleted_list):
        comp_list = []
        fill_add2, _ = self.auto_engine.get_commontxt_optionlist(autocompleted_list)
        for path in autocompleted_list:
            comp_list.append(path.replace(fill_add2, ""))
        fill_add, comp_list = self.auto_engine.get_commontxt_optionlist(comp_list)
        return fill_add2, fill_add, comp_list
    
    async def on_input_submitted(self, event: Input.Submitted):
        path = event.value.strip()
        if os.path.exists(path):
            self.post_message(PathSelected(path))

    async def on_path_selected(self, event: PathSelected):
        tree = self.query_one("#tree", Tree)
        tree.root.label = event.path
        tree.root.remove_children()
        # Build tree using your FileManipulate class
        self.build_tree_level(tree.root, self.actual_path)# event.path)
        tree.root.expand()
        # Also update right panel
        self.post_message(DirectorySelected(event.path))
        # Update Autocomplete text
        input_widget = self.query_one("#path_input", AutocompletePathInput)
        input_widget.value = event.path
        input_widget.cursor_position = len(event.path)

    def update_file_structure(self, path: str):
        try:
            entries = os.listdir(path)
        except (PermissionError,FileNotFoundError):
            return
        contents = []
        # 1) Ensure path exists in TreeViewer graph
        path_list = FM.path_to_list(path)
        path_id = self.add_path_nodes(path_list, self.viewer.main_node.id)
        parent_node = self.viewer.get_nodes_by_attribute("id", path_id)[0]
        for entry in entries:
            full = os.path.join(path, entry)
            entry_id = self.find_nodes(path_list+[entry], self.viewer.main_node.id)
            if entry_id:
                continue
            if os.path.isdir(full):
                contents.append({entry: []})
                # Create TreeNode for folder
                node = TreeNode(entry)
                node.i_am = "dir"
                node.parent = parent_node
                node.children = []
                # Assign ID + level
                self.viewer._set_treenode_levels(node, parent_node.level + 1)
                self.viewer.all_nodes.append(node)
                parent_node.children.append(node)
            else:
                size = FM.get_file_size(full)
                contents.append((entry, size))
                node = TreeNode(entry)
                node.i_am = "file"
                node.size = size
                node.info = (entry, size)
                node.parent = parent_node
                node.children = []
                # Assign ID + level
                self.viewer._set_treenode_levels(node, parent_node.level + 1)
                self.viewer.all_nodes.append(node)
                parent_node.children.append(node)

        # 2) Update raw file_structure
        new_struct = FM.path_to_file_structure_dict(path, contents, set_list=True)
        current_list = self.file_structure["TreeStruct"]
        merged_list = FM.merge_file_structure_lists(current_list, [new_struct])
        self.file_structure["TreeStruct"] = merged_list

        # 3) Keep viewer.file_struct in sync
        self.viewer.file_struct = self.file_structure
    
    def add_path_nodes(self, path_list, parent_id):
        parent_node = self.viewer.get_nodes_by_attribute("id", parent_id)[0]
        if not isinstance(parent_node, TreeNode):
            return None

        if len(path_list) == 0:
            return parent_id
        # Check if child already exists
        for child_node in parent_node.children:
            if child_node.name == path_list[0]:
                return self.add_path_nodes(path_list[1:], child_node.id)
        # No child with that name → create new dir node
        node = TreeNode(path_list[0])
        node.i_am = "dir"
        node.parent = parent_node
        node.children = []
        # Assign ID + level
        self.viewer._set_treenode_levels(node, parent_node.level + 1)
        # Add to viewer
        self.viewer.all_nodes.append(node)
        parent_node.children.append(node)
        return self.add_path_nodes(path_list[1:], node.id)
    
    def find_nodes(self, path_list, parent_id):
        parent_node = self.viewer.get_nodes_by_attribute("id", parent_id)[0]
        if not isinstance(parent_node, TreeNode):
            return None
        if len(path_list) == 0:
            return parent_id
        # Check if child already exists
        for child_node in parent_node.children:
            if child_node.name == path_list[0]:
                return self.add_path_nodes(path_list[1:], child_node.id)
        return None

    def build_tree_level(self, node, path):
        try:
            for entry in os.listdir(path):
                full = os.path.join(path, entry)
                if os.path.isdir(full):    
                    path_id=self.add_path_nodes(FM.path_to_list(full),self.viewer.main_node.id)
                    try:
                        v_node=self.viewer.get_nodes_by_attribute("id",path_id)[0]
                    except IndexError:
                        v_node=None
                    sel_txt=""
                    if node and (v_node.selected_children or v_node.selected):
                        sel_txt="✔" 
                    # Add folder node with icon
                    child = node.add(f"{sel_txt}📁 {entry}", data=full)
                    # Check if this folder has subfolders
                    if self.folder_has_subfolders(full):
                        child.allow_expand = True
                    else:
                        child.allow_expand = False
        except (PermissionError,FileNotFoundError):
            pass
    
    def folder_has_subfolders(self, path):
        try:
            for entry in os.listdir(path):
                full = os.path.join(path, entry)
                if os.path.isdir(full):
                    return True
            return False
        except (PermissionError,FileNotFoundError):
            return False        
    
    @staticmethod
    def get_selected_unselected_text(is_selected:bool):
        if is_selected:
            return "[✔]"
        return "[ ]"

    def load_directory_into_list(self, path: str):
        table = self.query_one("#list", DataTable)
        table.clear(columns=True)
        path_id = self.add_path_nodes(FM.path_to_list(path), self.viewer.main_node.id)
        table.add_columns("✔", "Name", "Type", "Size", "Modified")
        try:
            for entry in os.listdir(path):
                full = os.path.join(path, entry)
                entry_id = self.find_nodes([entry], path_id)
                try:
                    entry_node=self.viewer.get_nodes_by_attribute("id",entry_id)[0]
                except IndexError:
                    entry_node=None
                im_selected=False
                if entry_node and entry_node.selected:
                    im_selected=True
                if os.path.isdir(full):
                    icon = "📁"
                    table.add_row(
                        self.get_selected_unselected_text(im_selected),
                        f"{icon} {entry}",
                        "Dir",
                        "",
                        FM.get_modified_date(full).strftime("%Y-%m-%d %H:%M")
                    )
                else:
                    size = FM.get_file_size(full)
                    size_txt = FM.get_size_str_formatted(size, 11, True)
                    table.add_row(
                        self.get_selected_unselected_text(im_selected),
                        entry,
                        "File",
                        size_txt,
                        FM.get_modified_date(full).strftime("%Y-%m-%d %H:%M")
                    )
                table.action_scroll_home()
        except (PermissionError,FileNotFoundError):
            pass
    
    async def on_tree_node_selected(self, event: Tree.NodeSelected):
        path = event.node.data
        self.actual_path = path
        # Update path label
        path_label = self.query_one("#path_label", Label)
        path_label.update(path)
        # Update list panel
        self.load_directory_into_list(path)
        # Update Autocomplete text
        input_widget = self.query_one("#path_input", AutocompletePathInput)
        input_widget.value = path
        input_widget.cursor_position = len(path)
    
    async def on_key(self, event: events.Key):
        if event.key == "space":
            focused = self.focused
            if isinstance(focused, DataTable):
                await self.handle_list_space()

        if event.key == "enter":
            focused = self.focused
            if isinstance(focused, DataTable):
                await self.handle_list_enter()
    
    async def handle_list_space(self):
        table = self.query_one("#list", DataTable)
        im_selected=False
        row_coord = table.cursor_row
        row_keys=list(table.rows.keys())
        row_key = row_keys[row_coord]
        if row_key is not None:
            col_keys=list(table.columns.keys())
            current = table.get_cell(row_key, col_keys[0])
            entry = str(table.get_cell(row_key, col_keys[1]))
            entry=entry.replace("📁 ","")
            path_list=FM.path_to_list(self.actual_path)+[entry]
            my_id=self.find_nodes(path_list,self.viewer.main_node.id)
            if my_id:
                node=self.viewer.get_nodes_by_attribute("id",my_id)[0]
                node.selected=not node.selected
                im_selected=node.selected
                self.viewer.clear_selected_children(self.viewer.main_node)
                self.viewer.set_selected_children(self.viewer.main_node)
            table.update_cell(row_key, col_keys[0], self.get_selected_unselected_text(im_selected))
        
        full = os.path.join(self.actual_path, entry)
        if im_selected:
            if full not in self.selection:
                self.selection.append(full)
        else:
            if full in self.selection:
                self.selection.remove(full)
        # Refresh tree
        tree = self.query_one("#tree", Tree)
        tree.root.remove_children()
        # Build tree using your FileManipulate class
        self.build_tree_level(tree.root, self.actual_path)
        
    async def handle_list_enter(self):
        table = self.query_one("#list", DataTable)
        result_dict={"Struct":self.file_structure,"TreeView":self.viewer,"Selection":self.selection}
        self.exit(result=result_dict)

if __name__ == "__main__":
    result=FileExplorer().run()
    if isinstance(result,dict):
        print("*"*33)
        print(result.get("Struct"))
        print("*"*33)
        print(result.get("Selection"))
        print("*"*33)
        viewer=result.get("TreeView")
        if isinstance(viewer,TreeViewer):
            viewer.call_style=viewer._call_style
            print(viewer.treenode_to_string(viewer.main_node,a_filter='dir'))