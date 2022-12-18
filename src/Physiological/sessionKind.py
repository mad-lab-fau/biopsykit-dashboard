import param
import panel as pn
import pytz


class SessionKind(param.Parameterized):
    synced_radiobox = pn.widgets.RadioBoxGroup(name='Synced', options=['Synced', 'Not Synced'])
    session_type_select = pn.widgets.Select(name='Session Type', options=['Multi Session', 'Single Session'])
    timezone_select = pn.widgets.Select(name='Timezone', options=['None Selected'] + list(pytz.all_timezones),
                                        value='Europe/Berlin')
    text = ''
    ready = param.Boolean(default=False)

    @param.depends('timezone_select.value', watch=True)
    def timezone_selected(self):
        if self.timezone_select.value != 'None Selected':
            setattr(self, 'ready', True)
        else:
            setattr(self, 'ready', False)

    @param.output(('session_type', param.String), ('synced', param.Boolean), ('timezone', param.String))
    def output(self):
        if self.synced_radiobox.value == 'Synced':
            return self.session_type_select.value, True, self.timezone_select.value
        else:
            return self.session_type_select.value, False, self.timezone_select.value

    @param.depends('session_type_select.value', watch=True)
    def session_type_changed(self):
        if self.session_type_select.value == 'Multi Session':
            self.synced_radiobox.disabled = False
        else:
            self.synced_radiobox.disabled = True

    def panel(self):
        if self.text == "":
            f = open('../assets/Markdown/FirstPagePhysiologicalData.md', 'r')
            fileString = f.read()
            self.text = fileString
        self.ready = True
        return pn.Column(
            pn.pane.Markdown(self.text),
            self.timezone_select,
            self.session_type_select,
            self.synced_radiobox
        )
