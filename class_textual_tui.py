# -*- coding: utf-8 -*-
########################
# F.garcia
# creation: 15.02.2025
##########################

from textual.app import App, ComposeResult
from textual.widgets import Static, ListView, ListItem, Label, Input 
from rich.text import Text
from textual.widgets import Button
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer
from textual.widgets import Tree
from textual.reactive import reactive
from textual import events
from textual.message import Message

from class_tree_viewer import TreeViewer,TreeNode

import os
from class_autocomplete_input import AutocompletePathFile
from class_file_manipulate import FileManipulate
FM = FileManipulate()


from textual.widgets import TextArea
from textual.screen import Screen
import json



class CopyTextWidget(Vertical):

    class Closed(Message):
        def __init__(self, sender):
            super().__init__()
            self.sender = sender

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def compose(self):
        yield TextArea(
            value=self.text,
            read_only=True,
            id="copy_text",
        )

        yield Horizontal(
            Button("Close", id="close"),
            id="buttons"
        )

    def on_mount(self):
        self.query_one("#copy_text", TextArea).focus()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "close":
            self.post_message(self.Closed(self))

    def on_key(self, event: events.Key):
        if event.key == "escape":
            self.post_message(self.Closed(self))


class CopyTextApp(App):

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def compose(self) -> ComposeResult:
        yield CopyTextWidget(self.text)

    def on_copy_text_widget_closed(self, message: CopyTextWidget.Closed):
        self.exit()


class CopyTextScreen(Screen):

    def __init__(self, text: str, node=None):
        super().__init__()
        self.raw_text = text
        self.node = node
        self.json_text = None   # will be generated lazily
        self.mode = "raw"

    def compose(self):
        yield Vertical(
            TextArea(
                placeholder="",
                id="copy_text",
            ),
            Horizontal(
                Button("Copy Text", id="copy_text_btn"),
                Button("Copy JSON", id="copy_json"),
                Button("Close", id="close"),
                id="buttons"
            )
        )

    def on_mount(self):
        area = self.query_one("#copy_text", TextArea)
        area.insert(self.raw_text)
        area.focus()

    def on_button_pressed(self, event: Button.Pressed):
        area = self.query_one("#copy_text", TextArea)

        if event.button.id == "close":
            self.app.pop_screen()

        elif event.button.id == "copy_text_btn":
            # Switch back to raw text
            self.mode = "raw"
            area.clear()
            area.insert(self.raw_text)
            area.focus()

        elif event.button.id == "copy_json":
            # Generate JSON only once
            if self.json_text is None:
                self.json_text = json.dumps(self.node_to_dict(self.node), indent=2)

            self.mode = "json"
            area.clear()
            area.insert(self.json_text)
            area.focus()

    def on_key(self, event: events.Key):
        if event.key == "escape":
            self.app.pop_screen()

    def node_to_dict(self, node):
        """Convert a TreeNode subtree into a JSON‑friendly dict."""
        def convert(n):
            entry = {}

            # Convert raw metadata to string
            if hasattr(n, "data") and isinstance(n.data, dict):
                raw = n.data.get("raw")
                if raw is not None:
                    entry["raw"] = str(raw)

            # Convert label to string (Rich Text -> plain text)
            if hasattr(n, "label"):
                entry["label"] = str(n.label)

            # Convert children
            if n.children:
                entry["children"] = [convert(child) for child in n.children]

            return entry

        return convert(node)


class TextualInputWidget(Vertical):

    class Submitted(Message):
        def __init__(self, sender, value: str):
            super().__init__()
            self.sender = sender
            self.value = value

    class Cancelled(Message):
        def __init__(self, sender):
            super().__init__()
            self.sender = sender

    def __init__(self, title: str, prompt: str, default: str = "", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.prompt = prompt
        self.default = default

    def compose(self) -> ComposeResult:
        yield Static(self.prompt, id="prompt")
        yield Input(value=self.default, id="input_box")

        yield Horizontal(
            Button("OK", id="ok"),
            Button("Cancel", id="cancel"),
            id="buttons"
        )

    def on_mount(self):
        self.query_one("#input_box", Input).focus()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "ok":
            value = self.query_one("#input_box", Input).value
            self.post_message(self.Submitted(self, value))
        elif event.button.id == "cancel":
            self.post_message(self.Cancelled(self))

    def on_key(self, event: events.Key):
        if event.key == "escape":
            self.post_message(self.Cancelled(self))
        elif event.key == "enter":
            value = self.query_one("#input_box", Input).value
            self.post_message(self.Submitted(self, value))


class TextualInputApp(App):

    def __init__(self, title: str, prompt: str, default: str = ""):
        super().__init__()
        self.title = title
        self.prompt = prompt
        self.default = default
        self.result = None

    def compose(self) -> ComposeResult:
        yield TextualInputWidget(self.title, self.prompt, self.default)

    def on_textual_input_widget_submitted(self, message: TextualInputWidget.Submitted):
        self.result = message.value
        self.exit(self.result)

    def on_textual_input_widget_cancelled(self, message: TextualInputWidget.Cancelled):
        self.exit(None)

class ConfirmInputWidget(Vertical):

    class Confirmed(Message):
        """Posted when the user confirms with correct input."""
        def __init__(self, sender):
            super().__init__()
            self.sender = sender

    class Cancelled(Message):
        """Posted when the user cancels."""
        def __init__(self, sender):
            super().__init__()
            self.sender = sender

    def __init__(self, title, question, required_text, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.question = question
        self.required_text = required_text

    def compose(self):
        yield Static(self.question, id="question")
        yield Static(f'Type **{self.required_text}** to confirm:', id="instruction")

        yield Input(placeholder="Type here...", id="confirm_input")

        yield Horizontal(
            Button("Confirm", id="confirm", disabled=True),
            Button("Cancel", id="cancel"),
            id="buttons"
        )

    def on_mount(self):
        self.query_one("#confirm_input", Input).focus()

    # Enable confirm button only when input matches
    def on_input_changed(self, event: Input.Changed):
        confirm_btn = self.query_one("#confirm", Button)
        confirm_btn.disabled = (event.value.strip() != self.required_text)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "confirm":
            self.post_message(self.Confirmed(self))
        elif event.button.id == "cancel":
            self.post_message(self.Cancelled(self))

    def on_key(self, event: events.Key):
        input_box = self.query_one("#confirm_input", Input)
        confirm_btn = self.query_one("#confirm", Button)

        if event.key == "escape":
            self.post_message(self.Cancelled(self))

        elif event.key == "enter":
            # Only confirm if the text matches
            if not confirm_btn.disabled:
                self.post_message(self.Confirmed(self))

class ConfirmInputApp(App):

    def __init__(self, title, question, required_text):
        super().__init__()
        self.title = title
        self.question = question
        self.required_text = required_text

    def compose(self):
        yield ConfirmInputWidget(self.title, self.question, self.required_text)

    def on_confirm_input_widget_confirmed(self, message: ConfirmInputWidget.Confirmed):
        self.exit(True)

    def on_confirm_input_widget_cancelled(self, message: ConfirmInputWidget.Cancelled):
        self.exit(False)

class MessageBoxWidget(Vertical):

    class Choice(Message):
        """Posted when the user makes a choice."""
        def __init__(self, sender, value: bool):
            super().__init__()
            self.sender = sender
            self.value = value

    def __init__(self, title, question, default=True, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.question = question
        self.default = default

    def compose(self):
        yield Static(self.question, id="question")

        yield Horizontal(
            Button("Yes", id="yes"),
            Button("No", id="no"),
            id="buttons"
        )

    def on_mount(self):
        # Highlight default button
        if self.default:
            self.query_one("#yes", Button).focus()
        else:
            self.query_one("#no", Button).focus()

    def on_button_pressed(self, event: Button.Pressed):
        choice = (event.button.id == "yes")
        self.post_message(self.Choice(self, choice))

    def on_key(self, event: events.Key):
        yes_btn = self.query_one("#yes", Button)
        no_btn = self.query_one("#no", Button)

        if event.key == "escape":
            self.post_message(self.Choice(self, False))

        elif event.key == "enter":
            if yes_btn.has_focus:
                self.post_message(self.Choice(self, True))
            else:
                self.post_message(self.Choice(self, False))

        elif event.key in ("tab", "right"):
            if yes_btn.has_focus:
                no_btn.focus()
            else:
                yes_btn.focus()

        elif event.key in ("left", "shift+tab"):
            if no_btn.has_focus:
                yes_btn.focus()
            else:
                no_btn.focus()

class MessageBoxApp(App):
    def __init__(self, title, question, default=True):
        super().__init__()
        self.title = title
        self.question = question
        self.default = default

    def compose(self):
        yield MessageBoxWidget(self.title, self.question, self.default)

    def on_message_box_widget_choice(self, message: MessageBoxWidget.Choice):
        self.exit(message.value)

class MenuItem(ListItem):
    def __init__(self, text: str, locked: bool = False, prefix: str = None):
        self.text = text
        self.locked = locked
        self.prefix = prefix or ""

        if locked:
            label = Label(f"{self.prefix}🔒[dim]{text}[/dim]")
        else:
            label = Label(f"{self.prefix}{text}")

        super().__init__(label)


class MenuWidget(Vertical):

    class Selected(Message):
        """Posted when a menu item is selected."""
        def __init__(self, sender, value):
            super().__init__()
            self.sender = sender
            self.value = value

    def __init__(self, menu_items, menu_options=None, **kwargs):
        super().__init__(**kwargs)

        # Normalize menu_items
        if isinstance(menu_items, dict):
            self.menu_dict = menu_items
            self.menu_items = list(menu_items.keys())
        else:
            self.menu_dict = None
            self.menu_items = menu_items

        self.menu_options = menu_options or {}
        self.default_selection = self.menu_options.get(
            "default_selection",
            self.menu_items[0]
        )
        self.locked_items = set(self.menu_options.get("locked", []))

        # Prefix / enumeration
        self.pre_texts = []
        do_enum = self.menu_options.get("enumerate", False)
        prefix = self.menu_options.get("prefix", "")

        for i, _ in enumerate(self.menu_items):
            if do_enum:
                self.pre_texts.append(f"{i+1}{prefix}")
            else:
                self.pre_texts.append(prefix)

        self.subtitle = self.menu_options.get("subtitle", "")

    def compose(self):
        yield Static(self.subtitle, id="subtitle")
        yield Static("", id="help")

        yield ListView(
            *[
                MenuItem(item, locked=item in self.locked_items, prefix=pre)
                for item, pre in zip(self.menu_items, self.pre_texts)
            ],
            id="menu"
        )

    def on_mount(self):
        list_view = self.query_one("#menu", ListView)
        index = self.menu_items.index(self.default_selection)
        list_view.index = index
        list_view.focus()

    def on_list_view_highlighted(self, event: ListView.Highlighted):
        item = event.item
        key = item.text

        if self.menu_dict:
            help_label = self.query_one("#help", Static)
            help_label.update(self.menu_dict[key])

    def on_list_view_selected(self, event: ListView.Selected):
        item = event.item
        key = item.text

        # Locked items cannot be selected
        if item.locked:
            return

        # Emit selection to parent
        self.post_message(self.Selected(self, key))

    def on_key(self, event: events.Key):
        list_view = self.query_one("#menu", ListView)
        items = list_view.children
        count = len(items)
        index = list_view.index

        if event.key == "escape":
            self.post_message(self.Selected(self, None))

        elif event.key == "enter":
            list_view.action_select_cursor()

        elif event.key == "home":
            self._jump_to_selectable(list_view, start=-1, forward=True)

        elif event.key == "end":
            self._jump_to_selectable(list_view, start=count, forward=False)

        elif event.key == "tab":
            self._jump_to_selectable(list_view, start=index, forward=True)

        elif event.key == "shift+tab":
            self._jump_to_selectable(list_view, start=index, forward=False)

    def _jump_to_selectable(self, list_view, start, forward=True):
        items = list_view.children
        count = len(items)
        step = 1 if forward else -1
        index = start

        for _ in range(count):
            index = (index + step) % count
            item = items[index]
            if not item.locked:
                list_view.index = index
                list_view.focus()
                return

class MenuApp(App):
    def __init__(self, menu_items, menu_options=None):
        super().__init__()
        self.menu_items = menu_items
        self.menu_options = menu_options

    def compose(self):
        yield MenuWidget(self.menu_items, self.menu_options)

    def on_menu_widget_selected(self, message: MenuWidget.Selected):
        self.exit(message.value)

class CheckTreeWidget(Tree):
    # Override the Tree's own key bindings
    BINDINGS = [
        ("right", "expand_node", "Expand"),
        ("left", "collapse_node", "Collapse"),
        ("enter", "noop", "Return Selection"),
        ("space", "action_toggle_select", "Toggle"),
        ("tab", "action_toggle_select", "Toggle"),
    ]

    def action_noop(self):
        """Enter key pressed — return selection."""
        selected = self.get_selected_items()

        # If one-selection mode and nothing is selected yet,
        # select the cursor node automatically
        if self.one_selection and not selected:
            node = self.cursor_node
            if node and node.data:
                viewer_node = self.viewer.get_nodes_by_attribute("id", node.data["node"])[0]
                # Do not Emit a locked item
                if viewer_node.id in self.locked_items:
                    return
                if viewer_node.selectable in [True, None]:
                    viewer_node.selected = True
                    node.data["selected"] = True
                    node.set_label(self.format_label(node))
                    selected = [viewer_node.id] if self.return_id else [viewer_node.name]

        # Emit the selection to the parent app
        self.post_message(self.SelectionChanged(self, selected))

    # Disable Tree's default toggle behavior
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
            
    class SelectionChanged(Message):
        """Posted when selection changes."""
        def __init__(self, sender, selected):
            super().__init__()
            self.sender = sender
            self.selected = selected

    def __init__(self, viewer:TreeViewer, tree_mode:dict=None, **kwargs):
        super().__init__("Root", **kwargs)
        self.viewer = viewer
        self.tree_mode = tree_mode or {}
        self.one_selection = self.tree_mode.get("one_selection", False)
        self.return_id = self.tree_mode.get("return_id", True)
        self.locked_items = self.tree_mode.get("locked_items", [])     
        self.dir_selectable = self.tree_mode.get("dir_selectable", True)  
        self.only_dir = self.tree_mode.get("only_dir", False)
        self.default_selected_items = self.tree_mode.get("default_selected_items", [])
        self.button_flag = None

    # ------------------------------------------------------------
    # BUILD TREE
    # ------------------------------------------------------------
    def on_mount(self):
        root = self.viewer.main_node
        self.build_textual_tree(self.root, root)
        self.refresh_labels(self.root)

    def build_textual_tree(self, tparent, viewer_node):
        if not isinstance(viewer_node,TreeNode):
            return
        if self.only_dir and viewer_node.i_am != "dir":
            return
        data = {
            "node": viewer_node.id,
            "selected": viewer_node.selected or False,
            "raw": viewer_node.name,
        }

        if viewer_node.parent is None:
            tnode = tparent
            tnode.set_label(viewer_node.name)
            tnode.data = data
        else:
            tnode = tparent.add(viewer_node.name, data=data)

        # Expand/collapse and selectable
        tnode.allow_expand = (viewer_node.i_am == "dir")
        if viewer_node.i_am == "dir":
            if viewer_node.expand:
                tnode.expand()
            else:
                tnode.collapse()
            viewer_node.selectable = self.dir_selectable
        
        # Default selected
        if viewer_node.id in self.default_selected_items:
            viewer_node.selected=True

        # Recurse
        for child in viewer_node.children or []:
            self.build_textual_tree(tnode, child)

        return tnode

    # ------------------------------------------------------------
    # LABEL FORMATTING
    # ------------------------------------------------------------
    def strip_checkbox(self, label):
        label = str(label)
        if label.startswith("[x] ") or label.startswith("[ ] "):
            return label[4:]
        return label

    def format_label(self, node):
        if node.data is None:
            return node.label

        viewer_node = self.viewer.get_nodes_by_attribute("id", node.data["node"])[0]
        if not isinstance(viewer_node,TreeNode):
            return
        node.data["selected"] = viewer_node.selected

        checked = viewer_node.selected
        raw = self.strip_checkbox(node.data.get("raw", node.label))

        # Locked items
        if viewer_node.id in self.locked_items:
            return Text("🔒 ") + Text(raw, style="dim italic")
            # return f"🔒 {Text(raw, style='dim italic')}"

        # Non-selectable
        if viewer_node.selectable == False or self.one_selection:
            # Selected children items
            if viewer_node.selected_children:
                return Text(raw, style="yellow")
            return raw

        # Selected children items
        box = "[X]" if checked else "[ ]"
        if viewer_node.selected_children or checked:
            return Text(f"{box} {raw}", style="yellow")
        return f"{box} {raw}"

    def refresh_labels(self, node):
        if node.data:
            node.set_label(self.format_label(node))
        for child in node.children:
            self.refresh_labels(child)

    # ------------------------------------------------------------
    # EVENTS
    # ------------------------------------------------------------
    def on_mouse_down(self, event: events.MouseDown):
        self.button_flag = event.button

    def on_tree_node_selected(self, event: Tree.NodeSelected):
        node = event.node

        # Right click toggles
        if self.button_flag == 3:
            self.button_flag = None
            self.toggle_node(node)

        # Left click just highlights
        if self.button_flag == 1:
            self.button_flag = None

    def on_key(self, event):
        if event.key in ("space", "tab"):
            self.toggle_node(self.cursor_node)
        elif event.key == "ctrl+a":
            self.select_all()
        elif event.key == "ctrl+u":
            self.unselect_all()
    
    def get_node_by_id(self,an_id)->TreeNode:
        try:
            viewer_node = self.viewer.get_nodes_by_attribute("id", an_id)[0]
        except IndexError:
            return None
        return viewer_node
    # ------------------------------------------------------------
    # SELECTION LOGIC
    # ------------------------------------------------------------
    def toggle_node(self, node):
        if node is None or node.data is None:
            return
        viewer_node=self.get_node_by_id(node.data["node"])
        if not viewer_node:
            return

        if viewer_node.selectable in [True, None]:
            viewer_node.selected = not viewer_node.selected
            self.viewer.clear_selected_children(self.viewer.main_node)
            self.viewer.set_selected_children(self.viewer.main_node)
            
        node.data["selected"] = viewer_node.selected
        node.set_label(self.format_label(node))

        if self.one_selection:
            self.post_message(self.SelectionChanged(self, self.get_selected_items()))
        
        self.refresh_labels(self.root)

    def select_recursive(self, viewer_node, selection=True):
        viewer_node.selected = selection
        for child in viewer_node.children:
            self.select_recursive(child, selection)

    def select_all(self):
        self.select_recursive(self.viewer.main_node, True)
        self.refresh_labels(self.root)

    def unselect_all(self):
        self.select_recursive(self.viewer.main_node, False)
        self.refresh_labels(self.root)

    # ------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------
    def get_selected_items(self):
        selected = []

        def walk(node):
            if node.data and node.data.get("selected"):
                if self.return_id:
                    selected.append(node.data["node"])
                else:
                    selected.append(node.data["raw"])
            for child in node.children:
                walk(child)

        walk(self.root)
        return selected 
    
    

class CheckTreeApp(App):
    BINDINGS = [
    ("c", "copy_node", "Copy Node Info"),
    ]

    def __init__(self, viewer, tree_mode=None, **kwargs):
        super().__init__(**kwargs)
        self.viewer = viewer
        self.tree_mode = tree_mode

    def compose(self):
        yield Header()
        yield CheckTreeWidget(self.viewer, self.tree_mode, id="tree")
        yield Footer()
    
    def on_check_tree_widget_selection_changed(self, message: CheckTreeWidget.SelectionChanged):
        self.exit(message.selected)

    def action_copy_node(self):
        tree = self.query_one("#tree")
        node = tree.cursor_node

        if not node:
            return

        lines = []

        def get_label(n):
            # Prefer your stored raw text if present
            if hasattr(n, "data") and isinstance(n.data, dict) and "raw" in n.data:
                return str(n.data["raw"])
            # Fallback to label if available
            if hasattr(n, "label"):
                return str(n.label)
            # Last resort: repr
            return repr(n)

        def walk(n, indent=0):
            prefix = " " * indent
            label = get_label(n)
            lines.append(f"{prefix}{label}")
            for child in n.children:
                walk(child, indent + 2)

        walk(node)
        text_dump = "\n".join(lines)
        self.push_screen(CopyTextScreen(text_dump, node=node))




if __name__ == "__main__":
    items = {
        "Tree Example":"Tree List Selection",
        "File Example":"File path explorer Example",
        "Locked Example":"To Lock",
        "Locked Example 2":"2nd Locked",
        "Exit":"Quitting?"
    }
    items_list=list(items.keys())
    menu_options={
        "title": "Main Menu",
        "subtitle": "[yellow]Please Select one option:[/yellow]",
        "default_selection":items_list[1],
        "locked":[items_list[2],items_list[3]],
        "enumerate":True,
        "prefix":". "
        }
    menu_selection = MenuApp(items,menu_options).run()
    if menu_selection == "Tree Example":

        # Example dynamic structure
        tree_data = {
            "Root_item": [
                {"expandable_item1": [("selectable_item1",1), ("selectable_item2",2)]},
                {"expandable_item2": [
                    {"expandable_item3": [("selectable_item4",3)]},
                    "selectable_item1"
                ]},
                ("selectable_item5",4),
                ("selectable_item6",5)
            ]
        }
        tree_mode={
                "one_selection":True,
                "root_selectable":True,
                "dir_selectable":False,
                "only_dir":False, 
                "locked_items":[3,5],
                "default_selected_items":[],
                "return_id":True
                }
        
        tree_viewer=TreeViewer(tree_data,{'name':0,"size":1})
        result = CheckTreeApp(tree_viewer,tree_mode).run()
        print("Selected items:", result)
        for anid in result:
            node=tree_viewer.get_nodes_by_attribute("id",anid)[0]
            print(f"{anid}->{node.name}")
    if menu_selection == "File Example":
        
        input_path = AutocompletePathFile('return string [cyan]ENTER[/cyan], Autofill path/file [cyan]TAB[/cyan], Cancel [cyan]ESC[/cyan]\nOr type complete path to file: ',
                                            FM.get_app_path(),absolute_path=False,verbose=True).get_input()
        (file_exist, is_file)=FM.validate_path_file(input_path)
        if file_exist:
            if is_file:
                input_path=FM.extract_path(input_path,False)
            else:
                input_path=FM.remove_separator_in_path_end(input_path)
            print(f"\nBuilding structure for: {input_path}")
            def add_size(file):
                try:
                    return (FM.extract_filename(file,True),FM.get_file_size(file))
                except:
                    return (file,-1)
            file_struct=FM.get_file_structure_from_active_path(input_path,input_path,{},fcn_call=add_size)
            
            tree_mode={
                "one_selection":False,
                "root_selectable":True,
                "dir_selectable":False,
                "only_dir":False, 
                "locked_items":[],
                "default_selected_items":[]
                }
            
            tree_viewer=TreeViewer(file_struct,{'name':0,"size":1})
            tree_viewer.expand_all_treenodes(False)
            result = CheckTreeApp(tree_viewer,tree_mode).run()
            path_results=[]
            for id in result:
                try:
                    node=tree_viewer.get_nodes_by_attribute("id",id)[0]
                    print(f"{node.info[0]}: {FM.get_size_str_formatted(node.info[1],11,True)}")
                    s_path_list=tree_viewer.trace_path(node)
                    s_path=str(os.sep).join(s_path_list)
                    path_results.append(s_path)
                except (TypeError,IndexError):
                    pass
            print("Selected items:", result)
            print("Selected paths:", path_results)
    elif menu_selection == "Exit":
        result = MessageBoxApp(
                                title="Confirm Exit",
                                question="Are you sure you want to Exit?",
                                default=True
                                ).run()
        print("I quitted before user chose:", result)

    print("Bye Bye")
