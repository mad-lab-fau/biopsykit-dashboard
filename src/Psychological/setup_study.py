import panel as pn
import param


def add_keys_nested_dict(d, keys):
    if d is None:
        d = {}
    if len(keys) == 1 and keys[0] not in d:
        d.setdefault(keys[0], None)
    else:
        key = keys[0]
        if key not in d:
            d[key] = {}
        if d[key] is None:
            d[key] = {}
        add_keys_nested_dict(d[key], keys[1:])


def change_value_nested_dict(d, keys, value):
    if len(keys) == 1:
        d[keys[0]] = value
    else:
        change_value_nested_dict(d[keys[0]], keys[1:], value)


# TODO: Rename Phase
class SetUpStudyDesign(param.Parameterized):
    add_study_btn = pn.widgets.Button(
        name="Add Study Part", button_type="primary", align="end"
    )
    study_name_input = pn.widgets.TextInput(
        name="Study Name",
        value="",
        placeholder="Type in here the name of the Study Part",
    )
    add_phase_btn = pn.widgets.Button(name="Add Phase", button_type="primary")
    add_subphase_btn = pn.widgets.Button(name="Add Subphase", button_type="primary")
    structure_accordion = pn.layout.Accordion(name="Study Structure")
    subject_time_dict = param.Dynamic()
    structure = {}

    def add_study_part(self, _):
        part_name = self.study_name_input.value
        if not self._assert_study_part_name(part_name):
            return
        self.structure[part_name] = None
        self.structure_accordion.append(self.get_phase_panel(part_name))

    def _assert_study_part_name(self, name):
        if name in self.structure.keys():
            pn.state.notifications.error("Study Part already exists")
            return False
        if name == "":
            pn.state.notifications.warning("Please enter a name for the study part")
            return False
        if name is None:
            pn.state.notifications.warning("Please enter a name for the study part")
            return False
        return True

    def state_add_phase(self, target, event):
        target.disabled = not self._assert_study_part_name(event.new)

    def state_add_value(self, target, event):
        target.disabled = event.new is None or event.new == ""

    # TODO
    def change_value(self, input_value, keys):
        change_value_nested_dict(self.structure, keys, input_value)

    # TODO: entsprechenden key aus Liste nehmen
    def remove_value(self, btn, keys):
        if not btn:
            return
        if len(keys) == 1:
            self.structure[keys[0]] = None
            index = self.get_accordion_index(keys[0])
            if index == -1:
                return
            self.structure_accordion.__setitem__(index, self.get_phase_panel(keys[0]))

    def add_value(self, input_value, btn, part_name, phase_row):
        if not btn:
            pn.state.notifications.warning("Click on Add Value in order to add a value")
            return
        change_value_nested_dict(self.structure, part_name, input_value)
        pn.state.notifications.success("Value added")
        phase_row.visible = False
        print(self.structure)
        # TODO: noch an richtige Stelle einfügen
        # self.structure_accordion.__setitem__(index, col)

    def get_accordion_index(self, name):
        index_list = [
            lst_index
            for (lst_index, element) in enumerate(self.structure_accordion.objects)
            if element.name == name
        ]
        if len(index_list) != 1:
            pn.state.notifications.error("Phase not found")
            return -1
        index = index_list[0]
        return index

    # TODO: Fix
    def remove_phase(self, btn, part_name, phase_name):
        if not btn:
            return
        pass
        # self.structure.pop(part_name)
        # index = self.get_accordion_index(part_name)
        # if index == -1:
        #     return
        # self.structure_accordion.pop(index)

    def add_subphase(
        self, btn, subphase_name_input, part_name, value_row, subphase_acc
    ):
        if not btn:
            return
        if not subphase_name_input:
            return
        value_row.visible = False
        key_list = part_name + [subphase_name_input]
        panel = self.get_phase_panel(key_list)
        subphase_acc.append(panel)
        add_keys_nested_dict(self.structure, key_list)

    def get_phase_panel(self, part_name) -> pn.Column:
        if not isinstance(part_name, list):
            part_name = [part_name]
        value_input = pn.widgets.IntInput(
            name="Value",
            placeholder="Type in here the value of the Phase",
        )
        value_add_btn = pn.widgets.Button(
            name="Add Value", button_type="primary", align="end", disabled=True
        )
        value_input.link(value_add_btn, callbacks={"value": self.state_add_value})
        subphase_name_input = pn.widgets.TextInput(
            name="Subphase Name",
            value="",
            placeholder="Type in here the name of the Subphase",
        )
        subphase_add_btn = pn.widgets.Button(
            name="Add Subphase", button_type="primary", align="end", disabled=False
        )
        if len(part_name) == 3:
            subphase_add_btn.visible = False
            subphase_name_input.visible = False
        value_row = pn.Row(value_input, value_add_btn)
        phase_row = pn.Row(subphase_name_input, subphase_add_btn)
        rename_input = pn.widgets.TextInput(
            name="Rename Phase", placeholder="Rename the Phase"
        )
        rename_btn = pn.widgets.Button(
            name="Rename", button_type="warning", align="end"
        )
        remove_phase_btn = pn.widgets.Button(
            name="Remove Phase", button_type="danger", align="end"
        )
        subphase_accordion = pn.layout.Accordion()
        pn.bind(
            self.remove_phase, remove_phase_btn, part_name, part_name[-1], watch=True
        )
        pn.bind(
            self.rename_phase,
            rename_btn,
            rename_input,
            part_name[-1],
            part_name,
            watch=True,
        )
        pn.bind(
            self.add_subphase,
            subphase_add_btn,
            subphase_name_input,
            part_name,
            value_row,
            subphase_accordion,
            watch=True,
        )
        col = pn.Column(
            value_row,
            phase_row,
            subphase_accordion,
            pn.layout.Divider(),
            remove_phase_btn,
            name=part_name[-1],
        )
        pn.bind(
            self.add_value, value_input, value_add_btn, part_name, phase_row, watch=True
        )
        return col

    def panel(self):
        self.add_study_btn.disabled = True
        self.study_name_input.link(
            self.add_study_btn, callbacks={"value_input": self.state_add_phase}
        )
        self.add_study_btn.on_click(self.add_study_part)
        text = "# Set up the study design \n Here you can set up the study design. You can add study parts, phases and subphases."
        return pn.Column(
            pn.pane.Markdown(text),
            self.structure_accordion,
            pn.Row(self.study_name_input, self.add_study_btn),
        )
