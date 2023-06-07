import panel as pn
import param


class ZipFolder(param.Parameterized):
    selected_device = param.String(default="")

    @param.output(("selected_device", param.String))
    def output(self):
        return (self.selected_device,)

    def panel(self):
        text = "# File or Folder? \n If you want to upload a complete folder, please zip it first. You can then upload the zip file in the following step."
        return pn.Column(pn.pane.Markdown(text))
